import os
import re
import requests
import threading
import time
import json
from urllib.parse import quote
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import urllib.parse
import shutil

class MusicLyricsCoverDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("音乐歌词和封面下载器")
        self.root.geometry("1200x900")
        
        # 设置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
        # 初始化下载器
        self.downloader = MusicDownloader()
        
        # 状态变量
        self.is_processing = False
        self.current_task = None
        self.songs = []
        
    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置颜色
        self.root.configure(bg='#f0f0f0')
        
    def create_widgets(self):
        """创建界面控件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = tk.Label(
            main_frame, 
            text="🎵 音乐歌词和封面下载器", 
            font=("微软雅黑", 18, "bold"),
            fg="#333333",
            bg="#f0f0f0"
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))
        
        # 浏览器控制区域
        browser_frame = ttk.LabelFrame(main_frame, text="浏览器设置", padding="10")
        browser_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.headless_var = tk.BooleanVar(value=True)
        headless_check = ttk.Checkbutton(
            browser_frame, 
            text="无头模式 (后台运行)", 
            variable=self.headless_var
        )
        headless_check.grid(row=0, column=0, padx=(0, 20))
        
        self.init_browser_btn = ttk.Button(
            browser_frame,
            text="初始化浏览器",
            command=self.init_browser,
            width=15
        )
        self.init_browser_btn.grid(row=0, column=1)
        
        # 下载选项区域
        options_frame = ttk.LabelFrame(main_frame, text="下载选项", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.download_lyrics_var = tk.BooleanVar(value=True)
        lyrics_check = ttk.Checkbutton(
            options_frame, 
            text="下载歌词 (.lrc)", 
            variable=self.download_lyrics_var
        )
        lyrics_check.grid(row=0, column=0, padx=(0, 20))
        
        self.download_cover_var = tk.BooleanVar(value=True)
        cover_check = ttk.Checkbutton(
            options_frame, 
            text="下载封面 (.jpg)", 
            variable=self.download_cover_var
        )
        cover_check.grid(row=0, column=1, padx=(0, 20))
        
        self.auto_naming_var = tk.BooleanVar(value=True)
        naming_check = ttk.Checkbutton(
            options_frame,
            text="自动命名 (歌曲名 - 歌手)",
            variable=self.auto_naming_var
        )
        naming_check.grid(row=0, column=2)
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="歌曲列表文件", padding="10")
        file_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=50)
        file_entry.grid(row=0, column=0, padx=(0, 10), sticky=(tk.W, tk.E))
        
        browse_btn = ttk.Button(file_frame, text="浏览...", command=self.browse_file)
        browse_btn.grid(row=0, column=1, padx=(0, 10))
        
        # 单曲下载区域
        single_frame = ttk.LabelFrame(main_frame, text="单曲下载", padding="10")
        single_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        single_frame.columnconfigure(1, weight=1)
        
        ttk.Label(single_frame, text="歌曲名:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.song_var = tk.StringVar()
        song_entry = ttk.Entry(single_frame, textvariable=self.song_var, width=30)
        song_entry.grid(row=0, column=1, padx=(0, 10), sticky=(tk.W, tk.E))
        
        ttk.Label(single_frame, text="歌手:").grid(row=0, column=2, padx=(0, 5), sticky=tk.W)
        self.artist_var = tk.StringVar()
        artist_entry = ttk.Entry(single_frame, textvariable=self.artist_var, width=30)
        artist_entry.grid(row=0, column=3, padx=(0, 10), sticky=(tk.W, tk.E))
        
        # 控制按钮区域
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=5, column=0, columnspan=3, pady=(0, 10))
        
        self.process_btn = ttk.Button(
            control_frame, 
            text="开始批量下载", 
            command=self.start_batch_download,
            width=15
        )
        self.process_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.single_btn = ttk.Button(
            control_frame, 
            text="下载单曲", 
            command=self.download_single,
            width=15
        )
        self.single_btn.grid(row=0, column=1, padx=(0, 10))
        
        self.test_btn = ttk.Button(
            control_frame,
            text="测试连接",
            command=self.test_connection,
            width=15
        )
        self.test_btn.grid(row=0, column=2, padx=(0, 10))
        
        self.stop_btn = ttk.Button(
            control_frame,
            text="停止",
            command=self.stop_processing,
            width=15,
            state=tk.DISABLED
        )
        self.stop_btn.grid(row=0, column=3, padx=(0, 10))
        
        self.view_folder_btn = ttk.Button(
            control_frame,
            text="打开下载文件夹",
            command=self.open_download_folder,
            width=15
        )
        self.view_folder_btn.grid(row=0, column=4)
        
        # 进度区域
        progress_frame = ttk.LabelFrame(main_frame, text="进度信息", padding="10")
        progress_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var,
            length=500,
            mode='determinate'
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 进度标签
        self.progress_label = tk.Label(
            progress_frame,
            text="就绪",
            font=("微软雅黑", 10),
            bg="#f0f0f0"
        )
        self.progress_label.grid(row=1, column=0, sticky=tk.W)
        
        # 统计信息
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        self.lyrics_stats_var = tk.StringVar(value="歌词: 0")
        lyrics_stats_label = tk.Label(
            stats_frame,
            textvariable=self.lyrics_stats_var,
            font=("微软雅黑", 9),
            bg="#f0f0f0",
            fg="#0066cc"
        )
        lyrics_stats_label.grid(row=0, column=0, padx=(0, 20))
        
        self.cover_stats_var = tk.StringVar(value="封面: 0")
        cover_stats_label = tk.Label(
            stats_frame,
            textvariable=self.cover_stats_var,
            font=("微软雅黑", 9),
            bg="#f0f0f0",
            fg="#cc3300"
        )
        cover_stats_label.grid(row=0, column=1, padx=(0, 20))
        
        self.total_stats_var = tk.StringVar(value="总计: 0")
        total_stats_label = tk.Label(
            stats_frame,
            textvariable=self.total_stats_var,
            font=("微软雅黑", 9, "bold"),
            bg="#f0f0f0",
            fg="#333333"
        )
        total_stats_label.grid(row=0, column=2)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="下载日志", padding="10")
        log_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 创建带滚动条的文本区域
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            width=100,
            height=10,
            font=("Consolas", 9),
            wrap=tk.WORD,
            bg="#ffffff",
            fg="#333333"
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 资源链接显示区域
        link_frame = ttk.LabelFrame(main_frame, text="资源链接详情", padding="10")
        link_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        link_frame.columnconfigure(0, weight=1)
        
        # 创建Notebook标签页
        self.link_notebook = ttk.Notebook(link_frame)
        self.link_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 歌词链接标签页
        self.lyrics_text = tk.Text(
            self.link_notebook,
            width=100,
            height=3,
            font=("Consolas", 9),
            wrap=tk.WORD,
            bg="#f8f8f8",
            fg="#0066cc"
        )
        self.link_notebook.add(self.lyrics_text, text="歌词链接")
        
        # 封面链接标签页
        self.cover_text = tk.Text(
            self.link_notebook,
            width=100,
            height=3,
            font=("Consolas", 9),
            wrap=tk.WORD,
            bg="#f8f8f8",
            fg="#cc3300"
        )
        self.link_notebook.add(self.cover_text, text="封面链接")
        
        # 页面信息显示区域
        info_frame = ttk.LabelFrame(main_frame, text="页面信息", padding="10")
        info_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(0, weight=1)
        
        self.info_text = tk.Text(
            info_frame,
            width=100,
            height=4,
            font=("Consolas", 8),
            wrap=tk.WORD,
            bg="#f0f0f0",
            fg="#333333"
        )
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 底部状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#e0e0e0",
            fg="#333333",
            font=("微软雅黑", 9)
        )
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 配置权重
        main_frame.rowconfigure(7, weight=1)
        
    def browse_file(self):
        """浏览文件"""
        file_path = filedialog.askopenfilename(
            title="选择歌曲列表文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            
    def init_browser(self):
        """初始化浏览器"""
        try:
            self.log_message("正在初始化Chrome浏览器...", "info")
            self.downloader.init_browser(self.headless_var.get())
            self.log_message("✓ 浏览器初始化成功", "success")
        except Exception as e:
            self.log_message(f"✗ 浏览器初始化失败: {e}", "error")
            
    def log_message(self, message, level="info"):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 设置颜色
        if level == "error":
            color = "red"
            prefix = "[错误] "
        elif level == "warning":
            color = "orange"
            prefix = "[警告] "
        elif level == "success":
            color = "green"
            prefix = "[成功] "
        else:
            color = "black"
            prefix = "[信息] "
        
        full_message = f"[{timestamp}] {prefix}{message}\n"
        
        # 插入到文本区域
        self.log_text.insert(tk.END, full_message)
        self.log_text.see(tk.END)
        
        # 更新状态栏
        self.status_var.set(f"{prefix}{message}")
        
    def update_link_info(self, lyrics_url, cover_url):
        """更新歌词和封面链接信息"""
        # 更新歌词链接
        self.lyrics_text.delete(1.0, tk.END)
        if lyrics_url:
            self.lyrics_text.insert(1.0, f"歌词下载链接:\n{lyrics_url}")
            self.lyrics_text.tag_configure("link", foreground="blue", underline=True)
            text_content = self.lyrics_text.get(1.0, tk.END)
            
            # 高亮链接
            link_patterns = [r'https://s\.myhkw\.cn/api\.php\?get=lrc[^\s]+']
            for pattern in link_patterns:
                for match in re.finditer(pattern, text_content):
                    start_idx = f"1.0+{match.start()}c"
                    end_idx = f"1.0+{match.end()}c"
                    self.lyrics_text.tag_add("link", start_idx, end_idx)
        else:
            self.lyrics_text.insert(1.0, "未找到歌词链接")
        
        # 更新封面链接
        self.cover_text.delete(1.0, tk.END)
        if cover_url:
            self.cover_text.insert(1.0, f"封面下载链接:\n{cover_url}")
            self.cover_text.tag_configure("link", foreground="blue", underline=True)
            text_content = self.cover_text.get(1.0, tk.END)
            
            # 高亮链接
            link_patterns = [r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp)[^\s]*']
            for pattern in link_patterns:
                for match in re.finditer(pattern, text_content):
                    start_idx = f"1.0+{match.start()}c"
                    end_idx = f"1.0+{match.end()}c"
                    self.cover_text.tag_add("link", start_idx, end_idx)
        else:
            self.cover_text.insert(1.0, "未找到封面链接")
            
    def update_page_info(self, page_info):
        """更新页面信息"""
        self.info_text.delete(1.0, tk.END)
        if page_info:
            info_text = ""
            if page_info.get('title'):
                info_text += f"页面标题: {page_info['title']}\n"
            if page_info.get('current_url'):
                info_text += f"当前URL: {page_info['current_url']}\n"
            if page_info.get('song_info'):
                info_text += f"歌曲信息: {page_info['song_info']}\n"
            if page_info.get('lyrics_found'):
                info_text += f"歌词: {'已找到' if page_info['lyrics_found'] else '未找到'}\n"
            if page_info.get('cover_found'):
                info_text += f"封面: {'已找到' if page_info['cover_found'] else '未找到'}\n"
            
            self.info_text.insert(1.0, info_text)
        else:
            self.info_text.insert(1.0, "无页面信息")
            
    def update_progress(self, current, total, message=""):
        """更新进度"""
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
            self.progress_label.config(text=f"{message} ({current}/{total})")
        else:
            self.progress_label.config(text=message)
            
    def update_stats(self, lyrics_count, cover_count, total):
        """更新统计信息"""
        self.lyrics_stats_var.set(f"歌词: {lyrics_count}")
        self.cover_stats_var.set(f"封面: {cover_count}")
        self.total_stats_var.set(f"总计: {total}")
        
    def open_download_folder(self):
        """打开下载文件夹"""
        try:
            save_dir = "downloaded_music"
            if os.path.exists(save_dir):
                os.startfile(os.path.abspath(save_dir))
            else:
                messagebox.showinfo("提示", "下载文件夹不存在")
        except Exception as e:
            messagebox.showerror("错误", f"打开文件夹失败: {e}")
            
    def start_batch_download(self):
        """开始批量下载"""
        if self.is_processing:
            messagebox.showwarning("警告", "当前正在处理中，请等待完成")
            return
            
        file_path = self.file_path_var.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("错误", "请选择有效的歌曲列表文件")
            return
            
        # 解析歌曲列表
        try:
            self.songs = self.downloader.parse_song_list(file_path)
            if not self.songs:
                messagebox.showwarning("警告", "歌曲列表为空或格式不正确")
                return
        except Exception as e:
            messagebox.showerror("错误", f"解析歌曲列表失败: {e}")
            return
            
        # 检查下载选项
        if not self.download_lyrics_var.get() and not self.download_cover_var.get():
            messagebox.showwarning("警告", "请至少选择一个下载选项")
            return
            
        # 检查浏览器是否初始化
        if not self.downloader.is_initialized():
            messagebox.showwarning("警告", "请先初始化浏览器")
            return
            
        # 开始处理
        self.is_processing = True
        self.process_btn.config(state=tk.DISABLED)
        self.single_btn.config(state=tk.DISABLED)
        self.test_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # 在新线程中处理
        self.current_task = threading.Thread(
            target=self.process_batch_download,
            daemon=True
        )
        self.current_task.start()
        
    def process_batch_download(self):
        """批量下载处理"""
        try:
            total = len(self.songs)
            
            self.log_message(f"开始处理 {total} 首歌曲", "info")
            self.update_progress(0, total, "开始处理")
            
            lyrics_count = 0
            cover_count = 0
            
            for i, song_info in enumerate(self.songs, 1):
                if not self.is_processing:
                    self.log_message("用户停止处理", "warning")
                    break
                    
                song_name = song_info['song']
                artist = song_info['artist']
                
                self.log_message(f"处理: {song_name} - {artist}", "info")
                self.update_progress(i, total, f"正在处理: {song_name}")
                
                # 处理单首歌曲
                result = self.process_single_song(song_name, artist, i, total)
                
                if result.get('lyrics_success'):
                    lyrics_count += 1
                    self.log_message(f"✓ 歌词下载成功: {result.get('lyrics_filename', '')}", "success")
                
                if result.get('cover_success'):
                    cover_count += 1
                    self.log_message(f"✓ 封面下载成功: {result.get('cover_filename', '')}", "success")
                
                # 更新统计
                self.update_stats(lyrics_count, cover_count, i)
                
                # 延迟
                time.sleep(1)
            
            # 处理完成
            self.log_message(f"处理完成! 歌词: {lyrics_count}, 封面: {cover_count}, 总计: {total}", "info")
            self.update_progress(total, total, "处理完成")
            
        except Exception as e:
            self.log_message(f"处理过程中出现错误: {str(e)}", "error")
        finally:
            self.finish_processing()
            
    def download_single(self):
        """下载单曲"""
        if self.is_processing:
            messagebox.showwarning("警告", "当前正在处理中，请等待完成")
            return
            
        song_name = self.song_var.get().strip()
        artist = self.artist_var.get().strip()
        
        if not song_name or not artist:
            messagebox.showerror("错误", "请输入歌曲名和歌手")
            return
            
        # 检查下载选项
        if not self.download_lyrics_var.get() and not self.download_cover_var.get():
            messagebox.showwarning("警告", "请至少选择一个下载选项")
            return
            
        # 检查浏览器是否初始化
        if not self.downloader.is_initialized():
            messagebox.showwarning("警告", "请先初始化浏览器")
            return
            
        # 开始处理
        self.is_processing = True
        self.process_btn.config(state=tk.DISABLED)
        self.single_btn.config(state=tk.DISABLED)
        self.test_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # 在新线程中处理
        self.current_task = threading.Thread(
            target=lambda: self.process_single_download(song_name, artist),
            daemon=True
        )
        self.current_task.start()
        
    def process_single_download(self, song_name, artist):
        """单曲下载处理"""
        try:
            self.log_message(f"开始下载: {song_name} - {artist}", "info")
            self.update_progress(0, 1, "开始下载")
            
            result = self.process_single_song(song_name, artist, 1, 1)
            
            lyrics_success = result.get('lyrics_success', False)
            cover_success = result.get('cover_success', False)
            
            if lyrics_success:
                self.log_message(f"✓ 歌词下载成功: {result.get('lyrics_filename', '')}", "success")
            elif self.download_lyrics_var.get():
                self.log_message(f"✗ 歌词下载失败: {song_name} - {artist}", "error")
            
            if cover_success:
                self.log_message(f"✓ 封面下载成功: {result.get('cover_filename', '')}", "success")
            elif self.download_cover_var.get():
                self.log_message(f"✗ 封面下载失败: {song_name} - {artist}", "error")
            
            self.update_progress(1, 1, "下载完成")
            self.update_stats(1 if lyrics_success else 0, 1 if cover_success else 0, 1)
                
        except Exception as e:
            self.log_message(f"处理过程中出现错误: {str(e)}", "error")
        finally:
            self.finish_processing()
            
    def test_connection(self):
        """测试连接"""
        try:
            self.log_message("测试连接中...", "info")
            
            # 测试示例歌曲
            test_url = "https://s.myhkw.cn/?name=Always%20Online%20%E6%9E%97%E4%BF%8A%E6%9D%B0&type=qq"
            self.log_message(f"测试URL: {test_url}", "info")
            
            if not self.downloader.is_initialized():
                self.downloader.init_browser(self.headless_var.get())
            
            # 获取页面
            page_data = self.downloader.get_page_with_selenium(test_url)
            
            if page_data:
                lyrics_url = page_data.get('lyrics_url')
                cover_url = page_data.get('cover_url')
                
                if lyrics_url or cover_url:
                    self.log_message(f"✓ 连接成功", "success")
                    self.update_link_info(lyrics_url, cover_url)
                    self.update_page_info({
                        'title': page_data.get('title', ''),
                        'current_url': page_data.get('current_url', ''),
                        'song_info': page_data.get('song_info', ''),
                        'lyrics_found': bool(lyrics_url),
                        'cover_found': bool(cover_url)
                    })
                else:
                    self.log_message("✗ 连接失败，未找到资源链接", "error")
            else:
                self.log_message("✗ 连接失败，无法获取页面", "error")
                
        except Exception as e:
            self.log_message(f"✗ 测试连接失败: {e}", "error")
            
    def process_single_song(self, song_name, artist, current=None, total=None):
        """处理单首歌曲"""
        try:
            # 显示处理信息
            if current and total:
                info_msg = f"[{current}/{total}] 搜索: {song_name} - {artist}"
            else:
                info_msg = f"搜索: {song_name} - {artist}"
            
            self.log_message(info_msg, "info")
            
            # 使用Selenium获取页面
            page_data = self.downloader.get_music_resources(song_name, artist)
            
            result = {
                'lyrics_success': False,
                'cover_success': False
            }
            
            if page_data:
                lyrics_url = page_data.get('lyrics_url')
                cover_url = page_data.get('cover_url')
                
                # 显示链接
                self.update_link_info(lyrics_url, cover_url)
                
                # 显示页面信息
                page_info = {
                    'title': page_data.get('title', ''),
                    'current_url': page_data.get('current_url', ''),
                    'song_info': f"{page_data.get('actual_song', song_name)} - {page_data.get('actual_artist', artist)}",
                    'lyrics_found': bool(lyrics_url),
                    'cover_found': bool(cover_url)
                }
                self.update_page_info(page_info)
                
                # 自动命名设置
                auto_naming = self.auto_naming_var.get()
                
                # 下载歌词
                if self.download_lyrics_var.get() and lyrics_url:
                    self.log_message(f"  下载歌词链接: {lyrics_url}", "info")
                    lyrics_result = self.downloader.download_lyrics(
                        lyrics_url, 
                        page_data.get('actual_song', song_name), 
                        page_data.get('actual_artist', artist),
                        auto_naming
                    )
                    
                    if lyrics_result['success']:
                        result['lyrics_success'] = True
                        result['lyrics_filename'] = lyrics_result['filename']
                    else:
                        self.log_message(f"   歌词下载失败: {lyrics_result.get('error', '未知错误')}", "warning")
                
                # 下载封面
                if self.download_cover_var.get() and cover_url:
                    self.log_message(f"  下载封面链接: {cover_url}", "info")
                    cover_result = self.downloader.download_cover(
                        cover_url,
                        page_data.get('actual_song', song_name),
                        page_data.get('actual_artist', artist),
                        auto_naming
                    )
                    
                    if cover_result['success']:
                        result['cover_success'] = True
                        result['cover_filename'] = cover_result['filename']
                    else:
                        self.log_message(f"   封面下载失败: {cover_result.get('error', '未知错误')}", "warning")
            
            return result
                
        except Exception as e:
            error_msg = str(e)
            self.log_message(f"处理错误: {error_msg}", "error")
            self.update_link_info(None, None)
            self.update_page_info({
                'title': '错误',
                'current_url': '',
                'song_info': f"{song_name} - {artist}",
                'lyrics_found': False,
                'cover_found': False
            })
            return result
            
    def stop_processing(self):
        """停止处理"""
        self.is_processing = False
        self.log_message("正在停止处理...", "warning")
        
    def finish_processing(self):
        """处理完成后的清理工作"""
        self.is_processing = False
        
        # 恢复按钮状态
        self.root.after(0, lambda: self.process_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.single_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.test_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
        
        self.log_message("处理已停止", "info")
    def on_closing(self):
        """关闭窗口时的处理"""
        if self.is_processing:
            if messagebox.askokcancel("退出", "下载正在进行中，确定要退出吗？"):
                self.is_processing = False
                if self.current_task and self.current_task.is_alive():
                    self.current_task.join(timeout=2)
                self.downloader.close()
                self.root.destroy()
        else:
            self.downloader.close()
            self.root.destroy()

class MusicDownloader:
    """音乐下载器，整合歌词和封面下载"""
    def __init__(self):
        self.driver = None
        self.base_url = "https://s.myhkw.cn/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://y.qq.com/',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
    def is_initialized(self):
        """检查浏览器是否已初始化"""
        return self.driver is not None
        
    def init_browser(self, headless=True):
        """初始化Chrome浏览器"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def parse_song_list(self, file_path):
        """解析歌曲列表文件"""
        songs = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        match = re.match(r'^\d+\.\s*(.+?)\s*-\s*(.+)$', line)
                        if match:
                            song_name = match.group(1).strip()
                            artist = match.group(2).strip()
                            songs.append({'song': song_name, 'artist': artist})
                        elif ' - ' in line:
                            parts = line.split(' - ', 1)
                            song_part = re.sub(r'^\d+\.\s*', '', parts[0])
                            songs.append({'song': song_part.strip(), 'artist': parts[1].strip()})
        except Exception as e:
            raise Exception(f"读取文件错误: {e}")
        return songs
    
    def build_search_url(self, song_name, artist):
        """构建搜索URL"""
        search_query = f"{song_name} {artist}"
        encoded_query = quote(search_query)
        return f"{self.base_url}?name={encoded_query}&type=qq"
    
    def get_page_with_selenium(self, url):
        """使用Selenium获取页面"""
        try:
            if not self.driver:
                raise Exception("浏览器未初始化")
            
            self.driver.get(url)
            
            # 等待页面加载
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 等待歌词按钮出现
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "j-lrc-btn"))
                )
            except:
                pass
            
            time.sleep(2)  # 确保页面完全渲染
            
            # 获取页面源码
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 查找歌词链接
            lrc_btn = soup.find('a', {'id': 'j-lrc-btn'})
            lyrics_url = lrc_btn['href'] if lrc_btn and lrc_btn.get('href') else None
            
            # 查找封面图片
            cover_url = self._extract_cover_url(soup)
            
            # 获取歌曲信息
            song_info = None
            name_input = soup.find('input', {'id': 'j-name'})
            author_input = soup.find('input', {'id': 'j-author'})
            
            if name_input and name_input.get('value') and author_input and author_input.get('value'):
                song_info = f"{name_input['value']} - {author_input['value']}"
            
            return {
                'title': self.driver.title,
                'current_url': self.driver.current_url,
                'lyrics_url': lyrics_url,
                'cover_url': cover_url,
                'song_info': song_info,
                'page_source': page_source[:1000]
            }
            
        except Exception as e:
            raise Exception(f"Selenium获取页面失败: {e}")
    
    def _extract_cover_url(self, soup):
        """从页面中提取封面图片URL"""
        try:
            # 方法1: 查找APlayer的封面图片
            aplayer_pic = soup.find('div', {'class': 'aplayer-pic'})
            if aplayer_pic:
                style = aplayer_pic.get('style', '')
                if 'background-image:' in style:
                    match = re.search(r'background-image:\s*url\(["\']?([^"\'\)]+)["\']?\)', style)
                    if match:
                        return self._make_absolute_url(match.group(1))
            
            # 方法2: 查找img标签
            img_tags = soup.find_all('img')
            for img in img_tags:
                for attr in ['src', 'data-src', 'data-original']:
                    img_url = img.get(attr)
                    if img_url:
                        # 检查是否是专辑封面
                        if any(keyword in img_url.lower() for keyword in ['cover', 'album', 'artist', 'photo']):
                            return self._make_absolute_url(img_url)
            
            # 方法3: 查找特定的QQ音乐图片模式
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    patterns = [
                        r'https://y\.gtimg\.cn/music/photo_new/[^\s"\']+\.(?:jpg|jpeg|png)',
                        r'photo_new[^\s"\']+\.(?:jpg|jpeg|png)',
                        r'T002R[^\s"\']+\.(?:jpg|jpeg|png)'
                    ]
                    for pattern in patterns:
                        matches = re.findall(pattern, script.string)
                        for match in matches:
                            if not match.startswith(('http://', 'https://')):
                                match = 'https://y.gtimg.cn/' + match
                            return match
            
            # 方法4: 查找背景图片
            for tag in soup.find_all(style=True):
                style = tag.get('style', '')
                if 'background' in style or 'background-image' in style:
                    matches = re.findall(r'url\(["\']?([^"\'\)]+\.(?:jpg|jpeg|png|gif|webp))["\']?\)', style)
                    if matches:
                        return self._make_absolute_url(matches[0])
            
            return None
            
        except Exception as e:
            print(f"提取封面URL失败: {e}")
            return None
    
    def _make_absolute_url(self, url):
        """将相对URL转换为绝对URL"""
        if not url:
            return None
        
        url = url.strip()
        
        # 如果已经是完整URL
        if url.startswith(('http://', 'https://')):
            return url
        
        # 处理双斜杠开头的URL
        if url.startswith('//'):
            return 'https:' + url
        
        # 处理base_url
        parsed_base = urllib.parse.urlparse(self.base_url)
        base_domain = parsed_base.scheme + '://' + parsed_base.netloc
        
        # 处理以/开头的相对路径
        if url.startswith('/'):
            return base_domain + url
        
        return url
    
    def get_music_resources(self, song_name, artist):
        """获取歌曲的歌词和封面信息"""
        try:
            search_url = self.build_search_url(song_name, artist)
            page_data = self.get_page_with_selenium(search_url)
            
            if not page_data:
                return None
            
            # 提取实际的歌曲名和歌手
            soup = BeautifulSoup(page_data.get('page_source', ''), 'html.parser')
            name_input = soup.find('input', {'id': 'j-name'})
            author_input = soup.find('input', {'id': 'j-author'})
            
            actual_song = name_input['value'] if name_input and name_input.get('value') else song_name
            actual_artist = author_input['value'] if author_input and author_input.get('value') else artist
            
            return {
                'actual_song': actual_song,
                'actual_artist': actual_artist,
                'lyrics_url': page_data.get('lyrics_url'),
                'cover_url': page_data.get('cover_url'),
                'title': page_data.get('title'),
                'current_url': page_data.get('current_url')
            }
            
        except Exception as e:
            raise Exception(f"获取音乐资源失败: {e}")
    
    def download_lyrics(self, lyrics_url, song_name, artist, auto_naming=True):
        """下载歌词文件"""
        try:
            # 下载歌词
            response = requests.get(lyrics_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            content = response.text.strip()
            
            # 检查是否为有效的歌词文件
            if not content:
                return {'success': False, 'error': '歌词文件为空'}
            
            if content.startswith('<!DOCTYPE') or '<html' in content.lower():
                return {'success': False, 'error': '下载到的是HTML页面，不是歌词文件'}
            
            # 创建保存目录
            save_dir = "downloaded_music/lyrics"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            # 生成文件名
            if auto_naming:
                filename = f"{song_name}-{artist}.lrc"
            else:
                # 从URL提取文件名
                parsed_url = urllib.parse.urlparse(lyrics_url)
                filename = os.path.basename(parsed_url.path) or f"{song_name}_{artist}.lrc"
            
            # 清理文件名
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            filepath = os.path.join(save_dir, filename)
            
            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'filename': filename,
                'filepath': filepath,
                'size': len(content)
            }
            
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'歌词下载失败: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'歌词保存失败: {e}'}
    
    def download_cover(self, cover_url, song_name, artist, auto_naming=True):
        """下载封面图片"""
        try:
            if not cover_url:
                return {'success': False, 'error': '封面链接为空'}
            
            # 下载封面图片
            response = requests.get(cover_url, headers=self.headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # 检查内容类型
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type:
                return {'success': False, 'error': f'不是图片文件 (Content-Type: {content_type})'}
            
            # 创建保存目录
            save_dir = "downloaded_music/covers"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            # 生成文件名
            if auto_naming:
                # 使用歌曲名和歌手命名
                filename = f"{song_name} - {artist}.jpg"
            else:
                # 从URL提取文件名
                parsed_url = urllib.parse.urlparse(cover_url)
                original_filename = os.path.basename(parsed_url.path)
                
                # 如果没有扩展名或扩展名不是图片格式，添加.jpg
                if '.' not in original_filename or not re.search(r'\.(jpg|jpeg|png|gif|webp)$', original_filename, re.I):
                    filename = f"{song_name}_{artist}.jpg"
                else:
                    filename = original_filename
            
            # 清理文件名
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            filepath = os.path.join(save_dir, filename)
            
            # 保存图片
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # 获取文件大小
            file_size = os.path.getsize(filepath) // 1024
            
            return {
                'success': True,
                'filename': filename,
                'filepath': filepath,
                'size': file_size,
                'content_type': content_type
            }
            
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'封面下载失败: {e}'}
        except Exception as e:
            return {'success': False, 'error': f'封面保存失败: {e}'}
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()


def main():
    """主函数"""
    # 检查依赖
    try:
        import requests
        from bs4 import BeautifulSoup
        from selenium import webdriver
    except ImportError:
        print("正在安装依赖...")
        import subprocess
        subprocess.check_call(['pip', 'install', 
                              'requests', 
                              'beautifulsoup4', 
                              'lxml',
                              'selenium',
                              'webdriver-manager'])
        import requests
        from bs4 import BeautifulSoup
        from selenium import webdriver
    
    # 创建主窗口
    root = tk.Tk()
    
    # 创建应用程序
    app = MusicLyricsCoverDownloaderGUI(root)
    
    # 设置关闭事件
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # 运行主循环
    root.mainloop()


if __name__ == "__main__":
    main()