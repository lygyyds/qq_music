import os

folder = r"C:\Users\MI\Music\music_qq\Music"  # ← 修改为你的路径

for filename in os.listdir(folder):
    name, ext = os.path.splitext(filename)

    # 跳过非音频文件
    if ext.lower() not in [".mp3", ".flac", ".ogg", ".wav", ".m4a"]:
        continue

    # 如果是 "歌手 - 歌曲"
    if " - " in name:
        artist, title = name.split(" - ", 1)
        new_name = f"{title}-{artist}{ext}"

    # 如果是 "歌曲-歌手" 格式，保持不变
    else:
        continue

    old_path = os.path.join(folder, filename)
    new_path = os.path.join(folder, new_name)

    if not os.path.exists(new_path):
        os.rename(old_path, new_path)
        print(f"✔ {filename} → {new_name}")
    else:
        print(f"⚠ 跳过(重名): {new_name}")