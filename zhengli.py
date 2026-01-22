import os
from datetime import datetime

def get_audio_files_with_details(folder_path):
    """
    读取音频文件并返回详细信息
    
    Args:
        folder_path: 要扫描的文件夹路径
    
    Returns:
        list: 包含文件信息的字典列表
    """
    audio_extensions = {'.mp3', '.flac', '.ogg'}
    audio_files = []
    
    try:
        if not os.path.exists(folder_path):
            print(f"错误：文件夹 '{folder_path}' 不存在")
            return []
        
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            if os.path.isfile(file_path):
                file_ext = os.path.splitext(filename)[1].lower()
                
                if file_ext in audio_extensions:
                    # 获取文件大小（单位：字节）
                    file_size = os.path.getsize(file_path)
                    
                    # 获取文件修改时间
                    mod_time = os.path.getmtime(file_path)
                    mod_time_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 创建文件信息字典
                    file_info = {
                        'filename': filename,
                        'full_path': file_path,
                        'extension': file_ext,
                        'size_bytes': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2),  # 转换为MB
                        'modification_time': mod_time_str
                    }
                    audio_files.append(file_info)
        
        # 按文件名排序
        audio_files.sort(key=lambda x: x['filename'].lower())
        
        return audio_files
    
    except Exception as e:
        print(f"读取文件时发生错误：{e}")
        return []

def save_to_text_file(audio_files, folder_path, output_file=None):
    """
    将音频文件信息保存到文本文件
    
    Args:
        audio_files: 音频文件信息列表
        folder_path: 扫描的文件夹路径
        output_file: 输出文件名（可选）
    """
    if not audio_files:
        print("没有音频文件需要保存")
        return False
    
    try:
        # 如果没有指定输出文件名，则使用默认名称
        if output_file is None:
            # 使用当前时间生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            folder_name = os.path.basename(os.path.normpath(folder_path))
            output_file = f"audio_files_{folder_name}_{timestamp}.txt"
        
        # 确保输出文件扩展名为.txt
        if not output_file.lower().endswith('.txt'):
            output_file += '.txt'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入文件头信息
            f.write(f"音频文件列表\n")
            f.write(f"扫描文件夹: {folder_path}\n")
            f.write(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"文件数量: {len(audio_files)}\n")
            f.write("=" * 60 + "\n\n")
            
            # 写入统计信息
            file_count_by_type = {}
            total_size_mb = 0
            
            for file_info in audio_files:
                ext = file_info['extension']
                file_count_by_type[ext] = file_count_by_type.get(ext, 0) + 1
                total_size_mb += file_info['size_mb']
            
            f.write("文件类型统计:\n")
            for ext, count in file_count_by_type.items():
                f.write(f"  {ext}: {count} 个文件\n")
            f.write(f"总大小: {total_size_mb:.2f} MB\n\n")
            f.write("=" * 60 + "\n\n")
            
            # 写入每个文件的详细信息
            f.write("文件详细信息:\n\n")
            
            for i, file_info in enumerate(audio_files, 1):
                f.write(f"{i:4d}. 文件名: {file_info['filename']}\n")
                f.write(f"     类型: {file_info['extension']}\n")
                f.write(f"     大小: {file_info['size_mb']} MB ({file_info['size_bytes']} 字节)\n")
                f.write(f"     修改时间: {file_info['modification_time']}\n")
                f.write(f"     完整路径: {file_info['full_path']}\n")
                f.write("-" * 40 + "\n")
            
            # 写入文件尾
            f.write(f"\n{'=' * 60}\n")
            f.write("扫描完成\n")
        
        print(f"文件列表已保存到: {output_file}")
        return True
        
    except Exception as e:
        print(f"保存文件时发生错误: {e}")
        return False

def save_to_csv(audio_files, folder_path, output_file=None):
    """
    将音频文件信息保存到CSV文件
    
    Args:
        audio_files: 音频文件信息列表
        folder_path: 扫描的文件夹路径
        output_file: 输出文件名（可选）
    """
    if not audio_files:
        print("没有音频文件需要保存")
        return False
    
    try:
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            folder_name = os.path.basename(os.path.normpath(folder_path))
            output_file = f"audio_files_{folder_name}_{timestamp}.csv"
        
        if not output_file.lower().endswith('.csv'):
            output_file += '.csv'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入CSV头部
            f.write("序号,文件名,文件类型,大小(MB),大小(字节),修改时间,完整路径\n")
            
            # 写入数据
            for i, file_info in enumerate(audio_files, 1):
                # 处理可能包含逗号的文件名
                filename = file_info['filename'].replace('"', '""')
                full_path = file_info['full_path'].replace('"', '""')
                
                f.write(f'{i},"{filename}",{file_info["extension"]},{file_info["size_mb"]},'
                       f'{file_info["size_bytes"]},{file_info["modification_time"]},"{full_path}"\n')
        
        print(f"CSV文件已保存到: {output_file}")
        return True
        
    except Exception as e:
        print(f"保存CSV文件时发生错误: {e}")
        return False

def save_simple_list(audio_files, folder_path, output_file=None):
    """
    保存简单的文件列表（只保存文件名）
    
    Args:
        audio_files: 音频文件信息列表
        folder_path: 扫描的文件夹路径
        output_file: 输出文件名（可选）
    """
    if not audio_files:
        print("没有音频文件需要保存")
        return False
    
    try:
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            folder_name = os.path.basename(os.path.normpath(folder_path))
            output_file = f"audio_list_{folder_name}_{timestamp}.txt"
        
        if not output_file.lower().endswith('.txt'):
            output_file += '.txt'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"音频文件列表 - 共 {len(audio_files)} 个文件\n")
            f.write(f"扫描文件夹: {folder_path}\n")
            f.write(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            for i, file_info in enumerate(audio_files, 1):
                f.write(f"{i:4d}. {file_info['filename']}\n")
        
        print(f"简单列表已保存到: {output_file}")
        return True
        
    except Exception as e:
        print(f"保存简单列表时发生错误: {e}")
        return False

def main():
    """
    主函数：扫描文件夹并保存音频文件列表
    """
    print("音频文件扫描器")
    print("=" * 40)
    
    # 获取要扫描的文件夹路径
    folder_to_scan = input("请输入要扫描的文件夹路径（直接回车使用当前目录）: ").strip()
    
    if not folder_to_scan:
        folder_to_scan = os.getcwd()
    
    # 检查文件夹是否存在
    if not os.path.exists(folder_to_scan):
        print(f"错误：文件夹 '{folder_to_scan}' 不存在")
        return
    
    # 扫描音频文件
    print(f"\n正在扫描文件夹: {folder_to_scan}")
    audio_files = get_audio_files_with_details(folder_to_scan)
    
    if not audio_files:
        print("未找到任何音频文件 (.mp3, .flac, .ogg)")
        return
    
    print(f"找到 {len(audio_files)} 个音频文件")
    
    # 显示统计信息
    file_count_by_type = {}
    for file_info in audio_files:
        ext = file_info['extension']
        file_count_by_type[ext] = file_count_by_type.get(ext, 0) + 1
    
    print("\n文件类型统计:")
    for ext, count in file_count_by_type.items():
        print(f"  {ext}: {count} 个文件")
    
    # 询问保存选项
    print("\n请选择保存格式:")
    print("1. 详细文本文件（推荐）")
    print("2. CSV文件")
    print("3. 简单文件列表")
    print("4. 全部保存")
    print("5. 不保存，只显示结果")
    
    choice = input("请输入选择 (1-5): ").strip()
    
    # 获取输出文件名（可选）
    custom_name = None
    if choice in ['1', '2', '3', '4']:
        custom_name_input = input("请输入自定义文件名（直接回车使用默认名称）: ").strip()
        if custom_name_input:
            custom_name = custom_name_input
    
    # 根据选择执行保存操作
    base_name = custom_name if custom_name else None
    
    if choice == '1':
        save_to_text_file(audio_files, folder_to_scan, base_name)
    elif choice == '2':
        save_to_csv(audio_files, folder_to_scan, base_name)
    elif choice == '3':
        save_simple_list(audio_files, folder_to_scan, base_name)
    elif choice == '4':
        # 保存所有格式
        save_to_text_file(audio_files, folder_to_scan, base_name)
        
        # 为CSV和简单列表使用不同的文件名（如果提供了自定义名称）
        csv_name = f"{os.path.splitext(base_name)[0]}_csv" if base_name else None
        simple_name = f"{os.path.splitext(base_name)[0]}_list" if base_name else None
        
        save_to_csv(audio_files, folder_to_scan, csv_name)
        save_simple_list(audio_files, folder_to_scan, simple_name)
    elif choice == '5':
        # 只显示结果，不保存
        print("\n音频文件列表:")
        print("-" * 60)
        for i, file_info in enumerate(audio_files, 1):
            print(f"{i:4d}. {file_info['filename']} ({file_info['extension']}, {file_info['size_mb']} MB)")
    else:
        print("无效选择，程序退出")

def batch_save_example():
    """
    批量保存示例：扫描多个文件夹并保存结果
    """
    folders_to_scan = [
        r"C:\Music",
        r"C:\AudioBooks",
        r"D:\MyMusic"
    ]
    
    for folder in folders_to_scan:
        if os.path.exists(folder):
            print(f"\n扫描文件夹: {folder}")
            audio_files = get_audio_files_with_details(folder)
            
            if audio_files:
                save_to_text_file(audio_files, folder)
            else:
                print("未找到音频文件")
        else:
            print(f"文件夹不存在: {folder}")

if __name__ == "__main__":
    # 运行主程序
    main()
    
    # 或者运行批量保存示例
    # batch_save_example()
    
    input("\n按回车键退出...")