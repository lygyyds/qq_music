import os
import re
import sys
from pathlib import Path

def rename_song_files(folder_path, dry_run=True, extensions=None):
    """
    将歌曲文件名从"作者 - 歌曲名"格式改为"歌曲名-作者"格式
    
    Args:
        folder_path: 文件夹路径
        dry_run: 是否仅预览而不实际修改（默认为True）
        extensions: 要处理的文件扩展名列表（默认为音频文件）
    """
    if extensions is None:
        extensions = {'.mp3', '.flac', '.ogg', '.wav', '.m4a', '.wma', '.aac'}
    
    if not os.path.exists(folder_path):
        print(f"错误：文件夹 '{folder_path}' 不存在")
        return
    
    print(f"扫描文件夹: {folder_path}")
    print(f"文件扩展名: {', '.join(extensions)}")
    print(f"模式: {'预览模式（不实际修改）' if dry_run else '执行模式（将实际修改文件名）'}")
    print("=" * 60)
    
    # 匹配"作者 - 歌曲名"格式的正则表达式
    # 支持各种分隔符：破折号、减号、连字符等
    patterns = [
        r'^(.*?)\s*[-—–−~∼~]\s*(.*?)(\.[^.]+)$',  # 标准格式：作者 - 歌曲名.扩展名
        r'^(.*?)\s*[-—–−~∼~]\s*(.*?)\([^)]+\)(\.[^.]+)$',  # 带括号版本
    ]
    
    renamed_count = 0
    total_files = 0
    renamed_files = []
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        # 只处理文件，不处理文件夹
        if not os.path.isfile(file_path):
            continue
            
        # 检查文件扩展名
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in extensions:
            continue
            
        total_files += 1
        
        # 尝试匹配文件名模式
        matched = False
        new_filename = filename
        
        for pattern in patterns:
            match = re.match(pattern, filename)
            if match:
                artist = match.group(1).strip()
                song_name = match.group(2).strip()
                ext = match.group(3)
                
                # 检查是否已经有短横线分隔的歌曲名
                if '-' in song_name and '(' not in song_name and ')' not in song_name:
                    # 如果歌曲名中已有短横线但不是括号内容，可能已经是目标格式
                    continue
                
                # 构建新文件名：歌曲名-作者.扩展名
                new_filename = f"{song_name}-{artist}{ext}"
                matched = True
                break
        
        if matched and new_filename != filename:
            renamed_files.append((filename, new_filename))
            renamed_count += 1
            
            if dry_run:
                print(f"将重命名: {filename}")
                print(f"     为: {new_filename}")
                print("-" * 40)
            else:
                try:
                    # 避免文件名冲突
                    counter = 1
                    original_new_filename = new_filename
                    while os.path.exists(os.path.join(folder_path, new_filename)):
                        name_part, ext_part = os.path.splitext(original_new_filename)
                        new_filename = f"{name_part}_{counter}{ext_part}"
                        counter += 1
                    
                    os.rename(
                        os.path.join(folder_path, filename),
                        os.path.join(folder_path, new_filename)
                    )
                    print(f"已重命名: {filename} -> {new_filename}")
                    
                except Exception as e:
                    print(f"重命名失败 {filename}: {e}")
    
    print("=" * 60)
    print(f"扫描完成")
    print(f"总文件数: {total_files}")
    print(f"可重命名文件: {renamed_count}")
    
    if dry_run and renamed_count > 0:
        print("\n" + "=" * 60)
        print("重要提示：当前为预览模式，未实际修改任何文件！")
        print("如需实际修改，请重新运行脚本并设置 dry_run=False")
        
        # 生成重命名列表文件
        if renamed_files:
            list_filename = f"rename_preview_{Path(folder_path).name}.txt"
            list_path = os.path.join(folder_path, list_filename)
            try:
                with open(list_path, 'w', encoding='utf-8') as f:
                    f.write("文件名重命名预览列表\n")
                    f.write(f"文件夹: {folder_path}\n")
                    f.write(f"时间: {os.path.basename(__file__)}\n")
                    f.write("=" * 60 + "\n\n")
                    
                    for old_name, new_name in renamed_files:
                        f.write(f"{old_name}\n")
                        f.write(f"  -> {new_name}\n")
                        f.write("-" * 40 + "\n")
                    
                    f.write(f"\n总计: {renamed_count} 个文件需要重命名\n")
                
                print(f"预览列表已保存到: {list_path}")
            except Exception as e:
                print(f"保存预览列表失败: {e}")

def process_specific_format(filename):
    """
    处理特定格式的文件名转换
    支持多种格式的转换
    """
    # 移除常见的文件标识符
    cleaned_name = filename.replace('_H.', '.').replace('_L.', '.')
    
    # 各种分隔符模式
    patterns = [
        # 标准格式: 作者 - 歌曲名
        r'^(.*?)\s*[-—–−~∼~]\s*(.*?)(\.[^.]+)$',
        # 带括号的歌曲名: 作者 - 歌曲名 (版本)
        r'^(.*?)\s*[-—–−~∼~]\s*(.*?)\s*\(.*?\)(\.[^.]+)$',
        # 带下划线的作者: 作者_作者 - 歌曲名
        r'^(.*?)[_]\s*(.*?)\s*[-—–−~∼~]\s*(.*?)(\.[^.]+)$',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, cleaned_name)
        if match:
            if len(match.groups()) == 3:
                artist = match.group(1).strip()
                song_name = match.group(2).strip()
                ext = match.group(3)
            else:  # 4 groups (带下划线的作者)
                artist1 = match.group(1).strip()
                artist2 = match.group(2).strip()
                song_name = match.group(3).strip()
                ext = match.group(4)
                artist = f"{artist1}_{artist2}"
            
            # 如果歌曲名已经包含"-"，可能是已经转换过的格式
            if '-' in song_name and '(' not in song_name:
                parts = song_name.split('-')
                if len(parts) == 2:
                    # 检查是否是"歌曲名-作者"格式
                    if parts[1].strip() in artist:
                        return filename  # 已经是目标格式
            
            # 处理歌曲名中的括号内容
            if '(' in song_name:
                # 将括号内容移到歌曲名后面
                song_base = song_name.split('(')[0].strip()
                paren_content = song_name[song_name.find('('):]
                new_song_name = f"{song_base}-{artist}{paren_content}"
            else:
                new_song_name = f"{song_name}-{artist}"
            
            return new_song_name + ext
    
    return filename  # 无法匹配，返回原文件名

def batch_rename_advanced(folder_path, dry_run=True):
    """
    高级批量重命名，支持更多格式
    """
    if not os.path.exists(folder_path):
        print(f"错误：文件夹 '{folder_path}' 不存在")
        return
    
    extensions = {'.mp3', '.flac', '.ogg', '.wav', '.m4a', '.wma', '.aac'}
    
    print("高级文件名格式转换")
    print(f"文件夹: {folder_path}")
    print(f"模式: {'预览模式' if dry_run else '执行模式'}")
    print("=" * 60)
    
    files_to_rename = []
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if not os.path.isfile(file_path):
            continue
        
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in extensions:
            continue
        
        new_filename = process_specific_format(filename)
        
        if new_filename != filename:
            files_to_rename.append((filename, new_filename))
            
            if dry_run:
                print(f"{filename}")
                print(f"  -> {new_filename}")
                print("-" * 40)
    
    if not dry_run:
        print("开始实际重命名文件...")
        success_count = 0
        error_count = 0
        
        for old_name, new_name in files_to_rename:
            try:
                # 处理文件名冲突
                counter = 1
                original_new_name = new_name
                while os.path.exists(os.path.join(folder_path, new_name)):
                    name_part, ext_part = os.path.splitext(original_new_name)
                    new_name = f"{name_part}_{counter}{ext_part}"
                    counter += 1
                
                os.rename(
                    os.path.join(folder_path, old_name),
                    os.path.join(folder_path, new_name)
                )
                print(f"✓ {old_name} -> {new_name}")
                success_count += 1
                
            except Exception as e:
                print(f"✗ 重命名失败 {old_name}: {e}")
                error_count += 1
        
        print("=" * 60)
        print(f"重命名完成: 成功 {success_count}, 失败 {error_count}")
    
    else:
        print("=" * 60)
        print(f"可重命名文件: {len(files_to_rename)}")
        
        if files_to_rename:
            print("\n提示：当前为预览模式，未实际修改文件")
            print("如需实际修改，请重新运行并设置 dry_run=False")
            
            # 保存操作日志
            log_file = os.path.join(folder_path, f"rename_log_{Path(folder_path).name}.txt")
            try:
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write("文件名重命名操作日志\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for i, (old, new) in enumerate(files_to_rename, 1):
                        f.write(f"{i:3d}. {old}\n")
                        f.write(f"     -> {new}\n\n")
                
                print(f"操作日志已保存到: {log_file}")
            except Exception as e:
                print(f"保存日志失败: {e}")

def interactive_mode():
    """交互式模式"""
    print("歌曲文件名格式转换工具")
    print("=" * 50)
    print("功能：将 '作者 - 歌曲名' 格式转换为 '歌曲名-作者' 格式")
    print()
    
    # 获取文件夹路径
    folder_path = input("请输入文件夹路径（直接回车使用当前目录）: ").strip()
    if not folder_path:
        folder_path = os.getcwd()
    
    if not os.path.exists(folder_path):
        print(f"错误：文件夹 '{folder_path}' 不存在")
        return
    
    # 选择模式
    print("\n请选择模式:")
    print("1. 预览模式（仅显示将要重命名的文件，不实际修改）")
    print("2. 执行模式（实际修改文件名）")
    print("3. 高级模式（支持更多格式，仅预览）")
    print("4. 高级模式（支持更多格式，实际修改）")
    
    choice = input("请选择 (1-4): ").strip()
    
    if choice == '1':
        rename_song_files(folder_path, dry_run=True)
    elif choice == '2':
        # 确认操作
        confirm = input("\n警告：这将实际修改文件名！是否继续？(y/N): ").strip().lower()
        if confirm == 'y' or confirm == 'yes':
            rename_song_files(folder_path, dry_run=False)
        else:
            print("操作已取消")
    elif choice == '3':
        batch_rename_advanced(folder_path, dry_run=True)
    elif choice == '4':
        confirm = input("\n警告：这将实际修改文件名！是否继续？(y/N): ").strip().lower()
        if confirm == 'y' or confirm == 'yes':
            batch_rename_advanced(folder_path, dry_run=False)
        else:
            print("操作已取消")
    else:
        print("无效选择")

def quick_rename(folder_path):
    """快速重命名（无交互）"""
    print(f"正在处理文件夹: {folder_path}")
    batch_rename_advanced(folder_path, dry_run=False)

if __name__ == "__main__":
    # 使用方法1：直接修改特定文件夹（修改下面的路径）
    # folder_to_process = r"C:\Users\MI\Music\music_qq\Music"
    # quick_rename(folder_to_process)
    
    # 使用方法2：交互式模式（推荐）
    interactive_mode()
    
    input("\n按回车键退出...")