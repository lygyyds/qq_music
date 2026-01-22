import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser
import threading
import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import queue
from datetime import datetime


class MusicDownloadAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("明月浩空音乐 - 批量下载助手")
        self.root.geometry("1200x900")  # 稍微增加高度以容纳新的选项
        
        # 初始化变量
        self.songs_list = []
        self.current_index = 0
        self.download_folder = ""
        self.driver = None
        self.is_running = False
        self.is_paused = False
        self.queue = queue.Queue()
        
        # 新增：下载选项默认值
        self.download_song_enabled = tk.BooleanVar(value=True)
        self.download_lrc_enabled = tk.BooleanVar(value=True)
        self.auto_click_download = tk.BooleanVar(value=True)  # 自动点击下载按钮
        self.retry_on_fail = tk.BooleanVar(value=True)        # 失败后重试
        self.retry_count = tk.IntVar(value=2)                 # 重试次数
        
        # 创建界面
        self.create_widgets()
        
        # 加载配置
        self.load_config()
        
        # 初始化成功标记
        self.browser_initialized = False
        self.site_helper = None
    
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 1. 控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(1, weight=1)
        
        # 导入歌曲按钮
        ttk.Button(control_frame, text="导入歌曲列表", 
                  command=self.load_songs_file).grid(row=0, column=0, padx=(0, 10))
        
        # 歌曲数量显示
        self.songs_count_label = ttk.Label(control_frame, text="歌曲数量: 0")
        self.songs_count_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # 当前歌曲显示
        self.current_song_label = ttk.Label(control_frame, text="当前歌曲: 无")
        self.current_song_label.grid(row=0, column=2, sticky=tk.W)
        
        # 2. 下载文件夹设置
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(folder_frame, text="下载文件夹:").grid(row=0, column=0, padx=(0, 10))
        self.folder_path_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.folder_path_var, 
                 width=50).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(folder_frame, text="浏览", 
                  command=self.browse_folder).grid(row=0, column=2)
        
        # 3. 浏览器设置
        browser_frame = ttk.Frame(main_frame)
        browser_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.init_browser_button = ttk.Button(browser_frame, text="初始化浏览器", 
                                             command=self.initialize_browser_manual)
        self.init_browser_button.grid(row=0, column=0, padx=(0, 10))
        
        self.browser_status_label = ttk.Label(browser_frame, text="浏览器状态: 未初始化")
        self.browser_status_label.grid(row=0, column=1, sticky=tk.W)
        
        # 4. 下载选项设置（新增部分）
        options_frame = ttk.LabelFrame(main_frame, text="下载选项", padding="10")
        options_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 第一行选项
        ttk.Checkbutton(options_frame, text="下载歌曲文件", 
                       variable=self.download_song_enabled,
                       command=self.update_options_status).grid(row=0, column=0, padx=(0, 20))
        
        ttk.Checkbutton(options_frame, text="下载歌词文件 (.lrc)", 
                       variable=self.download_lrc_enabled,
                       command=self.update_options_status).grid(row=0, column=1, padx=(0, 20))
        
        ttk.Checkbutton(options_frame, text="自动点击下载按钮", 
                       variable=self.auto_click_download).grid(row=0, column=2, padx=(0, 20))
        
        # 第二行选项
        ttk.Checkbutton(options_frame, text="失败后重试", 
                       variable=self.retry_on_fail).grid(row=1, column=0, padx=(0, 20))
        
        ttk.Label(options_frame, text="重试次数:").grid(row=1, column=1, padx=(0, 5))
        ttk.Spinbox(options_frame, from_=0, to=5, width=5,
                   textvariable=self.retry_count).grid(row=1, column=2, padx=(0, 20))
        
        # 下载选项状态标签
        self.options_status_label = ttk.Label(options_frame, text="当前选项: 下载歌曲和歌词")
        self.options_status_label.grid(row=1, column=3, sticky=tk.W, padx=(20, 0))
        
        # 5. 进度控制
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 开始/暂停/停止按钮
        self.start_button = ttk.Button(progress_frame, text="开始", 
                                      command=self.start_process)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.pause_button = ttk.Button(progress_frame, text="暂停", 
                                      command=self.pause_process, state=tk.DISABLED)
        self.pause_button.grid(row=0, column=1, padx=(0, 10))
        
        self.stop_button = ttk.Button(progress_frame, text="停止", 
                                     command=self.stop_process, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=2, padx=(0, 10))
        
        # 跳过按钮
        self.skip_button = ttk.Button(progress_frame, text="跳过当前", 
                                     command=self.skip_current, state=tk.DISABLED)
        self.skip_button.grid(row=0, column=3, padx=(0, 10))
        
        # 手动下载完成按钮
        self.done_button = ttk.Button(progress_frame, text="我已下载完成", 
                                     command=self.mark_as_downloaded, state=tk.DISABLED)
        self.done_button.grid(row=0, column=4, padx=(0, 10))
        
        # 测试按钮
        self.test_button = ttk.Button(progress_frame, text="测试搜索", 
                                     command=self.test_search, state=tk.DISABLED)
        self.test_button.grid(row=0, column=5)
        
        # 6. 进度条和状态
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100)
        self.progress_bar.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(main_frame, text="状态: 等待开始")
        self.status_label.grid(row=6, column=0, sticky=tk.W, pady=(0, 10))
        
        # 7. 歌曲列表显示
        list_frame = ttk.LabelFrame(main_frame, text="歌曲列表", padding="10")
        list_frame.grid(row=7, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 创建Treeview
        columns = ('序号', '状态', '歌手', '歌曲名', '备注')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题
        for col in columns:
            self.tree.heading(col, text=col)
            if col == '序号':
                self.tree.column(col, width=50, anchor=tk.CENTER)
            elif col == '状态':
                self.tree.column(col, width=80, anchor=tk.CENTER)
            else:
                self.tree.column(col, width=150)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 8. 日志显示
        log_frame = ttk.LabelFrame(main_frame, text="操作日志", padding="10")
        log_frame.grid(row=8, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 9. 底部按钮
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=9, column=0, pady=(10, 0))
        
        ttk.Button(bottom_frame, text="打开网站", 
                  command=self.open_website).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(bottom_frame, text="导出结果", 
                  command=self.export_results).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(bottom_frame, text="保存配置", 
                  command=self.save_config).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(bottom_frame, text="清空日志", 
                  command=self.clear_log).grid(row=0, column=3)
    
    def update_options_status(self):
        """更新下载选项状态标签"""
        song_enabled = self.download_song_enabled.get()
        lrc_enabled = self.download_lrc_enabled.get()
        
        if song_enabled and lrc_enabled:
            status = "当前选项: 下载歌曲和歌词"
        elif song_enabled and not lrc_enabled:
            status = "当前选项: 仅下载歌曲"
        elif not song_enabled and lrc_enabled:
            status = "当前选项: 仅下载歌词"
        else:
            status = "当前选项: 不下载文件（仅搜索）"
        
        self.options_status_label.config(text=status)
        self.log_message(f"下载选项已更新: {status}")
    
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def load_songs_file(self):
        """加载歌曲文件"""
        file_path = filedialog.askopenfilename(
            title="选择歌曲文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 解析歌曲列表
                self.songs_list = self.parse_songs(content)
                
                # 更新显示
                self.update_songs_display()
                self.update_progress_display()
                
                self.log_message(f"成功导入 {len(self.songs_list)} 首歌曲")
                
            except Exception as e:
                messagebox.showerror("错误", f"读取文件失败: {e}")
                self.log_message(f"读取文件失败: {e}")
    
    def parse_songs(self, content):
        """解析歌曲文本 - 针对新格式"""
        songs = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            try:
                # 移除开头的序号（如 "1. "、"10. " 等）
                # 查找第一个空格后的内容
                if '. ' in line:
                    # 分割序号和歌曲信息
                    parts = line.split('. ', 1)
                    if len(parts) == 2:
                        song_info = parts[1].strip()
                    else:
                        song_info = line
                else:
                    song_info = line
                
                # 现在song_info应该是 "歌曲名 - 歌手" 格式
                if ' - ' in song_info:
                    parts = song_info.split(' - ', 1)
                    if len(parts) == 2:
                        song_name = parts[0].strip()
                        artist = parts[1].strip()
                        
                        # 清理歌曲名中的多余信息
                        song_name = song_name.split('（')[0].split('(')[0].strip()
                        song_name = song_name.split('_')[0].strip()  # 处理下划线
                        
                        # 清理歌手名中的多余信息
                        artist = artist.split('（')[0].split('(')[0].strip()
                        artist = artist.split('_')[0].strip()  # 处理下划线
                        
                        # 处理歌手中的特殊字符
                        if '_' in artist:
                            artist = artist.replace('_', ' ')
                        
                        songs.append({
                            'artist': artist,
                            'song_name': song_name,
                            'status': '待处理',
                            'notes': '',
                            'song_downloaded': False,
                            'lrc_downloaded': False,
                            'attempts': 0  # 尝试次数
                        })
                        
            except Exception as e:
                # 如果解析失败，记录但继续
                self.log_message(f"解析行失败: {line} - 错误: {e}")
                continue
        
        # 去重，避免重复歌曲
        unique_songs = []
        seen = set()
        
        for song in songs:
            key = f"{song['song_name']}|{song['artist']}"
            if key not in seen:
                seen.add(key)
                unique_songs.append(song)
            else:
                self.log_message(f"跳过重复歌曲: {song['song_name']} - {song['artist']}")
        
        self.log_message(f"解析完成: 共 {len(songs)} 首歌曲，去重后 {len(unique_songs)} 首")
        return unique_songs
    
    def update_songs_display(self):
        """更新歌曲列表显示"""
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 添加新项目
        for i, song in enumerate(self.songs_list):
            status = song.get('status', '待处理')
            
            # 如果同时记录了下载状态，添加到备注中
            notes = song.get('notes', '')
            if song.get('song_downloaded', False):
                notes += " 歌曲✓" if not notes else " | 歌曲✓"
            if song.get('lrc_downloaded', False):
                notes += " 歌词✓" if not notes else " | 歌词✓"
            
            self.tree.insert('', 'end', values=(
                i + 1,
                status,
                song.get('artist', ''),
                song.get('song_name', ''),
                notes
            ))
        
        # 高亮显示当前歌曲
        if self.current_index < len(self.songs_list):
            self.tree.selection_set(self.tree.get_children()[self.current_index])
            self.tree.see(self.tree.get_children()[self.current_index])
    
    def update_progress_display(self):
        """更新进度显示"""
        total = len(self.songs_list)
        if total > 0:
            processed = sum(1 for song in self.songs_list 
                          if song.get('status') in ['已下载', '已跳过', '搜索失败', '下载失败'])
            progress = (processed / total) * 100 if total > 0 else 0
            self.progress_var.set(progress)
            
            self.songs_count_label.config(text=f"歌曲数量: {total}")
            
            if self.current_index < total:
                current_song = self.songs_list[self.current_index]
                self.current_song_label.config(
                    text=f"当前歌曲: {current_song.get('artist', '')} - {current_song.get('song_name', '')}"
                )
    
    def browse_folder(self):
        """选择下载文件夹"""
        folder = filedialog.askdirectory(title="选择下载文件夹")
        if folder:
            self.folder_path_var.set(folder)
            self.log_message(f"设置下载文件夹: {folder}")
    
    def open_website(self):
        """打开网站"""
        try:
            webbrowser.open("https://s.myhkw.cn/")
            self.log_message("已打开网站: https://s.myhkw.cn/")
        except Exception as e:
            self.log_message(f"打开网站失败: {e}")
    
    def initialize_browser_manual(self):
        """手动初始化浏览器"""
        if not self.driver:
            threading.Thread(target=self.initialize_browser_thread, daemon=True).start()
        else:
            messagebox.showinfo("提示", "浏览器已经初始化")
    
    def initialize_browser_thread(self):
        """修复版的浏览器初始化方法"""
        try:
            self.log_message("正在初始化浏览器...")
            self.browser_status_label.config(text="浏览器状态: 正在初始化...")
            self.init_browser_button.config(state=tk.DISABLED)
            
            # 使用你的配置
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            driver_path = "chromedriver.exe"  # 假设在当前目录
            
            if not os.path.exists(driver_path):
                self.log_message("✗ ChromeDriver未找到")
                
                # 尝试其他位置
                possible_paths = [
                    "chromedriver.exe",
                    "./chromedriver.exe",
                    "C:/chromedriver/chromedriver.exe",
                    os.path.join(os.path.dirname(__file__), "chromedriver.exe")
                ]
                
                driver_found = False
                for path in possible_paths:
                    if os.path.exists(path):
                        driver_path = path
                        driver_found = True
                        self.log_message(f"找到ChromeDriver: {path}")
                        break
                
                if not driver_found:
                    raise Exception("请将chromedriver.exe放在程序目录")
            
            self.log_message(f"使用ChromeDriver: {driver_path}")
            
            # 设置Chrome选项 - 针对音乐网站优化
            chrome_options = Options()
            chrome_options.binary_location = chrome_path
            
            # 基础选项
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')
            
            # 避免被检测为自动化工具
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 用户代理
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36')
            
            # 禁用自动化特征
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            # 其他有用的选项
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-notifications')
            
            # 创建driver
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 执行JavaScript绕过检测
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # 设置超时时间
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            self.log_message("✓ WebDriver创建成功")
            
            # 访问网站
            self.log_message("正在访问音乐网站...")
            
            try:
                self.driver.get("https://s.myhkw.cn/")
                time.sleep(1)
                
                # 检查页面元素，确认网站结构
                try:
                    search_box = self.driver.find_element(By.ID, "j-input")
                    search_button = self.driver.find_element(By.ID, "j-submit")
                    self.log_message("✓ 确认网站结构正确")
                    self.log_message(f"搜索框ID: {search_box.get_attribute('id')}")
                    self.log_message(f"搜索按钮ID: {search_button.get_attribute('id')}")
                except:
                    self.log_message("⚠ 未找到预期的元素，网站结构可能已变化")
                
                current_url = self.driver.current_url
                page_title = self.driver.title
                
                self.log_message(f"当前URL: {current_url}")
                self.log_message(f"页面标题: {page_title}")
                
                if "myhkw" in current_url:
                    self.log_message("✓ 网站访问成功")
                else:
                    self.log_message("⚠ 可能被重定向")
                
            except Exception as e:
                self.log_message(f"网站访问异常: {e}")
            
            self.browser_initialized = True
            self.browser_status_label.config(text="浏览器状态: 已初始化")
            self.test_button.config(state=tk.NORMAL)
            self.log_message("✓ 浏览器初始化成功")
            self.queue.put(('show_message', "浏览器初始化成功!"))
            
        except Exception as e:
            error_msg = f"浏览器初始化失败: {str(e)}\n\n"
            error_msg += "可能的原因:\n"
            error_msg += "1. ChromeDriver版本不匹配\n"
            error_msg += "2. Chrome浏览器路径不正确\n"
            error_msg += "3. 网络连接问题\n\n"
            error_msg += "建议:\n"
            error_msg += "1. 检查ChromeDriver版本\n"
            error_msg += "2. 检查Chrome浏览器路径\n"
            
            self.log_message(f"初始化失败: {e}")
            self.queue.put(('show_error', error_msg))
            
        finally:
            self.init_browser_button.config(state=tk.NORMAL)
            if not self.browser_initialized:
                self.browser_status_label.config(text="浏览器状态: 初始化失败")
    
    def test_search(self):
        """测试搜索功能 - 改进版，使用正确的元素ID"""
        if not self.driver:
            messagebox.showwarning("警告", "请先初始化浏览器")
            return
        
        try:
            self.log_message("开始测试搜索...")
            self.log_message("测试歌曲: Imagine Dragons - Bones")
            
            # 刷新到主页
            self.driver.get("https://s.myhkw.cn/")
            time.sleep(1)
            
            # 查找搜索框
            search_box = self.driver.find_element(By.ID, "j-input")
            self.log_message("✓ 找到搜索框: j-input")
            
            # 输入搜索词
            search_box.clear()
            search_box.send_keys("Bones Imagine Dragons")
            self.log_message("已输入: Bones Imagine Dragons")
            
            # 查找搜索按钮
            search_button = self.driver.find_element(By.ID, "j-submit")
            self.log_message("✓ 找到搜索按钮: j-submit")
            
            # 点击搜索
            search_button.click()
            self.log_message("已点击搜索按钮")
            
            # 等待结果
            time.sleep(1)
            
            # 检查结果
            page_source = self.driver.page_source
            if "成功 Get √" in page_source:
                self.log_message("✓ 搜索成功！")
                
                # 尝试查找下载信息
                try:
                    download_button = self.driver.find_element(By.ID, "j-src-btn")
                    self.log_message("✓ 找到下载按钮: j-src-btn")
                    
                    # 获取下载信息
                    try:
                        song_name = self.driver.find_element(By.ID, "j-name").get_attribute('value')
                        artist = self.driver.find_element(By.ID, "j-author").get_attribute('value')
                        download_url = self.driver.find_element(By.ID, "j-src").get_attribute('value')
                        
                        self.log_message(f"歌曲: {song_name}")
                        self.log_message(f"歌手: {artist}")
                        self.log_message(f"下载URL: {download_url[:100]}...")
                    except:
                        pass
                        
                except:
                    self.log_message("⚠ 未找到下载按钮")
                
                messagebox.showinfo("测试成功", "搜索功能正常！\n请查看浏览器中的搜索结果。")
            else:
                self.log_message("✗ 搜索失败")
                messagebox.showwarning("测试失败", "搜索功能可能有问题")
                
        except Exception as e:
            self.log_message(f"测试搜索异常: {e}")
            messagebox.showerror("测试异常", f"发生异常: {e}")
    
    def start_process(self):
        """开始处理"""
        if not self.songs_list:
            messagebox.showwarning("警告", "请先导入歌曲列表")
            return
        
        if not self.folder_path_var.get():
            messagebox.showwarning("警告", "请选择下载文件夹")
            return
        
        if not self.browser_initialized or not self.driver:
            messagebox.showwarning("警告", "请先初始化浏览器")
            return
        
        # 检查至少选择了一个下载选项
        if not self.download_song_enabled.get() and not self.download_lrc_enabled.get():
            messagebox.showwarning("警告", "请至少选择一个下载选项（歌曲或歌词）")
            return
        
        # 创建下载文件夹
        self.download_folder = self.folder_path_var.get()
        os.makedirs(self.download_folder, exist_ok=True)
        
        # 记录当前下载选项
        self.log_message(f"下载选项: 歌曲={self.download_song_enabled.get()}, 歌词={self.download_lrc_enabled.get()}")
        self.log_message(f"自动点击: {self.auto_click_download.get()}, 重试: {self.retry_on_fail.get()}({self.retry_count.get()}次)")
        
        # 启动处理线程
        self.is_running = True
        self.is_paused = False
        
        # 更新按钮状态
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)
        self.skip_button.config(state=tk.NORMAL)
        self.done_button.config(state=tk.NORMAL)
        self.test_button.config(state=tk.DISABLED)
        
        # 启动处理线程
        self.process_thread = threading.Thread(target=self.process_songs)
        self.process_thread.daemon = True
        self.process_thread.start()
        
        self.log_message("开始处理歌曲...")
        self.log_message(f"总歌曲数: {len(self.songs_list)}")
        self.log_message(f"下载文件夹: {self.download_folder}")
    
    def process_songs(self):
        """处理歌曲的主循环"""
        # 找到第一个未处理的歌曲
        for i, song in enumerate(self.songs_list):
            if song.get('status') not in ['已下载', '已跳过', '搜索失败', '下载失败']:
                self.current_index = i
                break
        
        while self.is_running and self.current_index < len(self.songs_list):
            if self.is_paused:
                time.sleep(1)
                continue
            
            try:
                song = self.songs_list[self.current_index]
                
                # 如果已经处理过，跳过
                if song.get('status') in ['已下载', '已跳过', '搜索失败', '下载失败']:
                    self.current_index += 1
                    self.queue.put(('update_display', None))
                    continue
                
                # 更新状态
                self.queue.put(('update_status', f"正在处理: {song['artist']} - {song['song_name']}"))
                self.log_message(f"处理第 {self.current_index + 1}/{len(self.songs_list)} 首: {song['artist']} - {song['song_name']}")
                
                # 搜索歌曲
                search_success = self.search_song(song['artist'], song['song_name'])
                
                if search_success:
                    # 更新歌曲状态为"搜索中"
                    song['status'] = '搜索中'
                    self.queue.put(('update_display', None))
                    
                    # 根据设置尝试下载
                    download_success = self.download_song_with_options(song)
                    
                    if download_success:
                        song['status'] = '已下载'
                        self.log_message(f"✓ 处理完成: {song['song_name']}")
                        self.current_index += 1
                    else:
                        # 检查是否需要重试
                        if self.retry_on_fail.get() and song.get('attempts', 0) < self.retry_count.get():
                            attempts = song.get('attempts', 0)
                            song['attempts'] = attempts + 1
                            self.log_message(f"准备重试 ({attempts + 1}/{self.retry_count.get()}): {song['song_name']}")
                            time.sleep(2)  # 重试前等待
                            continue
                        else:
                            song['status'] = '下载失败'
                            self.current_index += 1
                            self.log_message(f"✗ 下载失败: {song['song_name']}")
                else:
                    self.log_message(f"搜索失败: {song['song_name']}")
                    song['status'] = '搜索失败'
                    song['notes'] = '搜索失败'
                    self.current_index += 1
                
                # 保存进度
                self.save_progress()
                
                # 更新显示
                self.queue.put(('update_display', None))
                
                # 短暂延迟，避免请求过快
                time.sleep(1)
                
            except Exception as e:
                self.log_message(f"处理歌曲时出错: {e}")
                import traceback
                self.log_message(traceback.format_exc())
                time.sleep(2)
            
        # 处理完成
        self.queue.put(('process_complete', None))
    
    def search_song(self, artist, song_name):
        """搜索歌曲 - 使用"歌曲 作者"格式搜索"""
        try:
            self.log_message(f"正在搜索: {artist} - {song_name}")
            
            # 确保浏览器窗口在前面
            try:
                self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            
            # 访问网站主页
            self.driver.get("https://s.myhkw.cn/")
            time.sleep(1)
            
            # 检查当前页面状态
            page_source = self.driver.page_source
            
            # 判断是否在搜索结果页面
            if "成功 Get √ 返回继续" in page_source:
                self.log_message("当前在搜索结果页面，需要返回搜索页面")
                
                try:
                    back_button = self.driver.find_element(By.ID, "j-back")
                    back_button.click()
                    self.log_message("已点击返回按钮")
                    time.sleep(1)
                except:
                    self.driver.get("https://s.myhkw.cn/")
                    time.sleep(1)
            
            # 查找搜索框
            try:
                search_box = self.driver.find_element(By.ID, "j-input")
                self.log_message("✓ 找到搜索框: j-input")
            except:
                self.log_message("✗ 未找到搜索框")
                return False
            
            # 清空搜索框
            search_box.clear()
            
            # 优化搜索词格式：使用"歌曲 作者"格式
            clean_song_name = song_name
            clean_artist = artist
            
            # 清理歌曲名
            # 移除括号内容、版本信息等
            clean_song_name = clean_song_name.split('(')[0].split('（')[0].strip()
            clean_song_name = clean_song_name.split('[')[0].split('【')[0].strip()
            clean_song_name = clean_song_name.split('-')[0].strip()
            
            # 移除特定版本标签
            version_indicators = ['(Live)', '(live)', '(DJ版)', '(DJ版)', '(Explicit)', 
                                '(Inst.)', '(Instrumental)', '(合唱版)', '(纯享版)',
                                '(旧版)', '(新版)', '(回忆版)', '(节奏版)', '(弹唱版)',
                                '(高燃摇滚版)', '(摇滚版)', '(Rehearsal Version)']
            
            for indicator in version_indicators:
                clean_song_name = clean_song_name.replace(indicator, '').strip()
            
            # 清理歌手名
            # 移除特殊字符和处理多个歌手的情况
            clean_artist = clean_artist.split('（')[0].split('(')[0].strip()
            clean_artist = clean_artist.split('_')[0].strip()
            
            # 处理歌手中的 "&" 和 "and"
            if '&' in clean_artist:
                # 取第一个歌手
                clean_artist = clean_artist.split('&')[0].strip()
            elif ' and ' in clean_artist.lower():
                clean_artist = clean_artist.lower().split(' and ')[0].strip().title()
            elif ' _ ' in clean_artist:
                # 取第一个歌手
                clean_artist = clean_artist.split(' _ ')[0].strip()
            
            # 构建搜索词：歌曲 作者
            if clean_artist and len(clean_artist) > 1:
                search_query = f"{clean_song_name} {clean_artist}"
            else:
                search_query = clean_song_name
            
            self.log_message(f"搜索词: {search_query}")
            
            # 逐字符输入（模拟真人输入）
            for char in search_query:
                search_box.send_keys(char)
                time.sleep(0.01)  # 稍微快一点
            
            # 选择QQ音乐源
            try:
                radio_inputs = self.driver.find_elements(By.XPATH, "//input[@type='radio']")
                if len(radio_inputs) >= 2:
                    qq_radio = radio_inputs[1]
                    if not qq_radio.is_selected():
                        qq_radio.click()
                        self.log_message("✓ 已选择QQ音乐源")
            except:
                pass
            
            # 查找搜索按钮
            try:
                search_button = self.driver.find_element(By.ID, "j-submit")
                self.log_message("✓ 找到搜索按钮: j-submit")
            except:
                self.log_message("✗ 未找到搜索按钮")
                return False
            
            # 点击搜索按钮
            try:
                search_button.click()
                self.log_message("已点击搜索按钮")
            except:
                self.driver.execute_script("arguments[0].click();", search_button)
                self.log_message("已通过JavaScript点击搜索按钮")
            
            # 等待搜索结果
            time.sleep(2)
            
            return self.check_search_result(song_name, artist)
            
        except Exception as e:
            self.log_message(f"搜索异常: {e}")
            import traceback
            self.log_message(traceback.format_exc())
            return False
    
    def check_search_result(self, song_name, artist):
        """检查搜索结果"""
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title
            page_source = self.driver.page_source
            
            self.log_message(f"搜索后URL: {current_url}")
            self.log_message(f"搜索后标题: {page_title}")
            
            # 检查是否显示搜索结果
            if "成功 Get √" in page_source:
                self.log_message("✓ 搜索成功: 显示'成功 Get √'")
                
                # 检查是否找到歌曲
                if song_name in page_source or artist in page_source:
                    self.log_message(f"✓ 在页面中找到 '{song_name}'")
                else:
                    self.log_message(f"⚠ 未在页面中找到 '{song_name}'，但搜索功能正常")
                
                return True
            elif current_url != "https://s.myhkw.cn/":
                self.log_message(f"✓ 搜索成功: URL已改变")
                return True
            else:
                self.log_message("✗ 搜索可能失败")
                return False
            
        except Exception as e:
            self.log_message(f"检查结果异常: {e}")
            return False
    
    def download_song_with_options(self, song):
        """根据用户设置的选项下载歌曲"""
        # 设置超时时间（秒）
        timeout = 60
        start_time = time.time()
        
        download_song = self.download_song_enabled.get()
        download_lrc = self.download_lrc_enabled.get()
        auto_click = self.auto_click_download.get()
        
        # 记录下载目标
        targets = []
        if download_song:
            targets.append("歌曲")
        if download_lrc:
            targets.append("歌词")
        
        if not targets:
            self.log_message("没有选择下载目标，跳过下载")
            return True
        
        self.queue.put(('update_status', f"正在下载: {song['song_name']} ({'和'.join(targets)})"))
        self.log_message(f"正在下载: {song['artist']} - {song['song_name']} ({'和'.join(targets)})")
        
        download_results = {
            'song': False,
            'lrc': False
        }
        
        try:
            # 等待页面完全加载
            time.sleep(1)
            
            # 如果启用了歌词下载，先尝试下载歌词
            if download_lrc:
                lrc_success = self.download_lrc(song)
                download_results['lrc'] = lrc_success
                song['lrc_downloaded'] = lrc_success
            
            # 如果启用了歌曲下载
            if download_song:
                song_success = self.download_song_file(song, auto_click)
                download_results['song'] = song_success
                song['song_downloaded'] = song_success
            
            # 检查下载结果
            all_success = True
            success_count = 0
            target_count = 0
            
            if download_song:
                target_count += 1
                if download_results['song']:
                    success_count += 1
                else:
                    all_success = False
                    
            if download_lrc:
                target_count += 1
                if download_results['lrc']:
                    success_count += 1
                else:
                    all_success = False
            
            # 根据下载结果更新状态
            if all_success:
                self.log_message(f"✓ 全部下载完成 ({success_count}/{target_count})")
                return True
            elif success_count > 0:
                self.log_message(f"✓ 部分下载完成 ({success_count}/{target_count})")
                # 部分成功也视为成功，继续下一首
                return True
            else:
                # 全部失败，检查是否需要手动操作
                if not auto_click:
                    self.log_message("自动下载未启用，等待手动操作...")
                    return self.wait_for_manual_download(song)
                else:
                    self.log_message("✗ 全部下载失败")
                    return False
                
        except Exception as e:
            self.log_message(f"下载过程中出错: {e}")
            import traceback
            self.log_message(traceback.format_exc())
            return False
    
    def download_song_file(self, song, auto_click=True):
        """下载歌曲文件"""
        try:
            # 查找歌曲下载按钮
            try:
                song_download_button = self.driver.find_element(By.ID, "j-src-btn")
                self.log_message("✓ 找到歌曲下载按钮: j-src-btn")
                
                # 获取歌曲下载链接
                try:
                    song_download_url = song_download_button.get_attribute('href')
                    if song_download_url:
                        self.log_message(f"歌曲下载链接: {song_download_url[:100]}...")
                        song['song_download_url'] = song_download_url
                        
                        # 保存链接到文件，供以后手动下载
                        self.save_download_link(song, song_download_url, "song")
                except:
                    pass
                
                # 根据设置决定是否自动点击
                if auto_click:
                    try:
                        song_download_button.click()
                        self.log_message("✓ 已自动点击歌曲下载按钮")
                        
                        # 等待下载开始
                        time.sleep(2)
                        self.log_message("等待歌曲下载完成...")
                        time.sleep(3)
                        
                        return True
                    except Exception as e:
                        # 尝试JavaScript点击
                        try:
                            self.driver.execute_script("arguments[0].click();", song_download_button)
                            self.log_message("✓ 已通过JavaScript点击下载按钮")
                            
                            time.sleep(3)
                            return True
                        except:
                            self.log_message(f"点击下载按钮失败: {e}")
                            return False
                else:
                    self.log_message("自动点击已禁用，请手动点击下载按钮")
                    return False
                    
            except Exception as e:
                self.log_message(f"未找到自动下载按钮: {e}")
                return False
                
        except Exception as e:
            self.log_message(f"下载歌曲文件时出错: {e}")
            return False
    
    def save_download_link(self, song, url, file_type):
        """保存下载链接到文件"""
        try:
            # 创建安全的文件名
            safe_artist = "".join(c for c in song['artist'] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_song_name = "".join(c for c in song['song_name'] if c.isalnum() or c in (' ', '-', '_')).strip()
            
            if file_type == "song":
                filename = f"{safe_song_name} - {safe_artist}_song_link.txt"
            else:
                filename = f"{safe_song_name} - {safe_artist}_lrc_link.txt"
            
            filepath = os.path.join(self.download_folder, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"歌曲: {song['song_name']}\n")
                f.write(f"歌手: {song['artist']}\n")
                f.write(f"下载链接: {url}\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            self.log_message(f"已保存{file_type}下载链接到: {filename}")
            
        except Exception as e:
            self.log_message(f"保存下载链接失败: {e}")
    
    def download_lrc(self, song):
        """下载歌词文件"""
        try:
            self.log_message("正在查找歌词下载链接...")
            
            # 查找所有链接，特别是歌词链接
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            
            for link in all_links:
                href = link.get_attribute('href')
                if href and 'api.php' in href and 'get=lrc' in href:
                    self.log_message(f"找到歌词链接: {href}")
                    
                    # 保存链接到文件
                    self.save_download_link(song, href, "lrc")
                    
                    # 下载歌词文件
                    return self.save_lrc_file(href, song)
            
            # 如果没有找到a标签的歌词链接，尝试查找其他元素
            all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'api.php')]")
            for element in all_elements:
                text = element.text
                if 'api.php' in text and 'get=lrc' in text:
                    self.log_message(f"找到歌词文本链接: {text}")
                    
                    # 提取URL
                    import re
                    url_match = re.search(r'https?://[^\s]+', text)
                    if url_match:
                        lrc_url = url_match.group(0)
                        
                        # 保存链接到文件
                        self.save_download_link(song, lrc_url, "lrc")
                        
                        return self.save_lrc_file(lrc_url, song)
            
            # 检查页面源代码中是否有歌词链接
            page_source = self.driver.page_source
            if 'get=lrc' in page_source:
                # 使用正则表达式提取歌词URL
                import re
                lrc_pattern = r'https?://[^\s"\']*api\.php[^\s"\']*get=lrc[^\s"\']*'
                matches = re.findall(lrc_pattern, page_source)
                
                if matches:
                    lrc_url = matches[0]
                    self.log_message(f"从源代码中找到歌词链接: {lrc_url}")
                    
                    # 保存链接到文件
                    self.save_download_link(song, lrc_url, "lrc")
                    
                    return self.save_lrc_file(lrc_url, song)
            
            self.log_message("未找到歌词下载链接")
            return False
            
        except Exception as e:
            self.log_message(f"查找歌词链接失败: {e}")
            return False
    
    def save_lrc_file(self, lrc_url, song):
        """保存歌词文件到本地"""
        try:
            import requests
            from urllib.parse import unquote
            
            # 创建安全的文件名
            safe_artist = "".join(c for c in song['artist'] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_song_name = "".join(c for c in song['song_name'] if c.isalnum() or c in (' ', '-', '_')).strip()
            
            # 构建歌词文件名
            lrc_filename = f"{safe_song_name} - {safe_artist}.lrc"
            lrc_path = os.path.join(self.download_folder, lrc_filename)
            
            # 检查文件是否已存在
            if os.path.exists(lrc_path):
                self.log_message(f"歌词文件已存在: {lrc_filename}")
                song['lrc_file'] = lrc_path
                song['lrc_downloaded'] = True
                return True
            
            # 下载歌词
            response = requests.get(lrc_url, timeout=10)
            
            if response.status_code == 200:
                # 保存歌词文件
                with open(lrc_path, 'w', encoding='utf-8') as f:
                    # 如果是纯文本歌词，直接保存
                    if response.text.strip():
                        f.write(response.text)
                    # 如果是二进制或其他格式，尝试解码
                    else:
                        try:
                            f.write(response.content.decode('utf-8'))
                        except:
                            f.write(response.content.decode('gbk', errors='ignore'))
                
                self.log_message(f"✓ 歌词已保存: {lrc_filename}")
                
                # 记录歌词文件路径
                song['lrc_file'] = lrc_path
                song['lrc_downloaded'] = True
                
                return True
            else:
                self.log_message(f"歌词下载失败，HTTP状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_message(f"保存歌词文件失败: {e}")
            return False
    
    def wait_for_manual_download(self, song):
        """等待用户手动下载"""
        timeout = 60
        start_time = time.time()
        
        self.log_message("等待用户手动操作...")
        self.log_message("下载完成后，请点击'我已下载完成'按钮")
        
        # 等待用户操作或超时
        while self.is_running and not self.is_paused:
            # 检查是否超时
            if time.time() - start_time > timeout:
                self.log_message(f"等待超时: {song['song_name']}")
                return False
            
            # 检查队列中是否有完成标记
            try:
                msg = self.queue.get_nowait()
                if msg[0] == 'download_complete':
                    # 用户点击完成时，根据选项记录下载状态
                    if self.download_song_enabled.get():
                        song['song_downloaded'] = True
                    if self.download_lrc_enabled.get() and not song.get('lrc_downloaded', False):
                        # 尝试下载歌词
                        self.download_lrc(song)
                    
                    self.log_message(f"已记录手动下载完成: {song['song_name']}")
                    return True
                elif msg[0] == 'skip_song':
                    song['status'] = '已跳过'
                    song['notes'] = '手动跳过'
                    self.log_message(f"已跳过: {song['song_name']}")
                    return True
            except queue.Empty:
                pass
            
            time.sleep(1)
        
        return False
    
    def update_gui_status(self, status):
        """更新GUI状态"""
        self.queue.put(('update_status', status))
    
    def mark_as_downloaded(self):
        """标记当前歌曲为已下载"""
        if self.is_running and not self.is_paused:
            self.queue.put(('download_complete', None))
            self.log_message("已标记当前歌曲为下载完成")
    
    def skip_current(self):
        """跳过当前歌曲"""
        if self.is_running and not self.is_paused:
            self.queue.put(('skip_song', None))
            self.log_message("已跳过当前歌曲")
    
    def pause_process(self):
        """暂停处理"""
        if self.is_running:
            self.is_paused = not self.is_paused
            if self.is_paused:
                self.pause_button.config(text="继续")
                self.log_message("处理已暂停")
            else:
                self.pause_button.config(text="暂停")
                self.log_message("处理继续")
    
    def stop_process(self):
        """停止处理"""
        self.is_running = False
        self.log_message("正在停止处理...")
        
        # 恢复按钮状态
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="暂停")
        self.stop_button.config(state=tk.DISABLED)
        self.skip_button.config(state=tk.DISABLED)
        self.done_button.config(state=tk.DISABLED)
        self.test_button.config(state=tk.NORMAL)
    
    def process_queue_messages(self):
        """处理队列消息"""
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                
                if msg_type == 'update_status':
                    self.status_label.config(text=f"状态: {data}")
                elif msg_type == 'update_display':
                    self.update_songs_display()
                    self.update_progress_display()
                elif msg_type == 'process_complete':
                    self.log_message("所有歌曲处理完成!")
                    self.stop_process()
                    messagebox.showinfo("完成", "所有歌曲处理完成!")
                elif msg_type == 'show_message':
                    messagebox.showinfo("提示", data)
                elif msg_type == 'show_error':
                    messagebox.showerror("错误", data)
                    
        except queue.Empty:
            pass
        
        # 每100ms检查一次队列
        self.root.after(100, self.process_queue_messages)
    
    def load_config(self):
        """加载配置"""
        config_file = "music_assistant_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if 'download_folder' in config:
                    self.folder_path_var.set(config['download_folder'])
                
                # 加载下载选项
                if 'download_song_enabled' in config:
                    self.download_song_enabled.set(config['download_song_enabled'])
                if 'download_lrc_enabled' in config:
                    self.download_lrc_enabled.set(config['download_lrc_enabled'])
                if 'auto_click_download' in config:
                    self.auto_click_download.set(config['auto_click_download'])
                if 'retry_on_fail' in config:
                    self.retry_on_fail.set(config['retry_on_fail'])
                if 'retry_count' in config:
                    self.retry_count.set(config['retry_count'])
                
                # 更新选项状态标签
                self.update_options_status()
                    
            except:
                pass
    
    def save_config(self):
        """保存配置"""
        config = {
            'download_folder': self.folder_path_var.get(),
            'download_song_enabled': self.download_song_enabled.get(),
            'download_lrc_enabled': self.download_lrc_enabled.get(),
            'auto_click_download': self.auto_click_download.get(),
            'retry_on_fail': self.retry_on_fail.get(),
            'retry_count': self.retry_count.get()
        }
        
        try:
            with open("music_assistant_config.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.log_message("配置已保存")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")
    
    def save_progress(self):
        """保存进度"""
        try:
            progress_file = os.path.join(self.download_folder, "download_progress.json")
            
            progress_data = {
                'songs': self.songs_list,
                'current_index': self.current_index,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.log_message(f"保存进度失败: {e}")
    
    def export_results(self):
        """导出结果"""
        if not self.songs_list:
            messagebox.showwarning("警告", "没有歌曲数据可导出")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="导出结果",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("歌曲下载结果报告\n")
                    f.write("=" * 50 + "\n\n")
                    
                    total = len(self.songs_list)
                    downloaded = sum(1 for song in self.songs_list 
                                   if song.get('status') == '已下载')
                    skipped = sum(1 for song in self.songs_list 
                                 if song.get('status') == '已跳过')
                    failed = sum(1 for song in self.songs_list 
                                if song.get('status') in ['搜索失败', '下载失败', '超时'])
                    
                    # 统计下载详情
                    songs_downloaded = sum(1 for song in self.songs_list 
                                         if song.get('song_downloaded', False))
                    lrc_downloaded = sum(1 for song in self.songs_list 
                                       if song.get('lrc_downloaded', False))
                    
                    f.write(f"总歌曲数: {total}\n")
                    f.write(f"已下载: {downloaded}\n")
                    f.write(f"已跳过: {skipped}\n")
                    f.write(f"失败: {failed}\n")
                    f.write(f"待处理: {total - downloaded - skipped - failed}\n\n")
                    
                    f.write(f"歌曲文件下载成功: {songs_downloaded}\n")
                    f.write(f"歌词文件下载成功: {lrc_downloaded}\n\n")
                    
                    # 详细列表
                    f.write("详细列表:\n")
                    f.write("-" * 50 + "\n")
                    
                    for i, song in enumerate(self.songs_list):
                        f.write(f"{i+1}. {song.get('artist', '')} - {song.get('song_name', '')}\n")
                        f.write(f"   状态: {song.get('status', '待处理')}\n")
                        
                        # 显示下载详情
                        details = []
                        if song.get('song_downloaded', False):
                            details.append("歌曲✓")
                        if song.get('lrc_downloaded', False):
                            details.append("歌词✓")
                        
                        if details:
                            f.write(f"   下载详情: {' '.join(details)}\n")
                        
                        if song.get('notes'):
                            f.write(f"   备注: {song.get('notes', '')}\n")
                        f.write("\n")
                
                self.log_message(f"结果已导出到: {file_path}")
                
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")
    
    def on_closing(self):
        """关闭窗口时的处理"""
        if self.is_running:
            if messagebox.askokcancel("确认", "处理正在进行中，确定要退出吗？"):
                self.stop_process()
                if self.driver:
                    try:
                        self.driver.quit()
                        self.log_message("浏览器已关闭")
                    except:
                        pass
                self.root.destroy()
        else:
            if self.driver:
                try:
                    self.driver.quit()
                    self.log_message("浏览器已关闭")
                except:
                    pass
            self.root.destroy()


def main():
    root = tk.Tk()
    app = MusicDownloadAssistant(root)
    
    # 设置关闭事件
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # 启动队列消息处理
    root.after(100, app.process_queue_messages)
    
    root.mainloop()


if __name__ == "__main__":
    print("需要安装以下库:")
    print("pip install selenium webdriver-manager")
    print("\n正在启动音乐下载助手...")
    main()