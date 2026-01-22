# music下载解析工具，QQmusic

# 本程序仅供学习之用



downloaded_lyrics_selenium						//歌词下载位置

MusicTag v1.0.9.0											//软件：自动批量处理歌词歌曲封面

qqmusic_decrypt-master								//下载的QQ音乐自动解密

ceshi.py															 //网站下载批量歌曲和歌词

ceshi_1.0.py													  //网站下载批量歌曲和歌词改进版

ceshi_2.0.py													  //网站下载批量歌曲和歌词改进版加了选项

chromedriver.exe										   //网站下载批量歌曲和歌词调用网站驱动

geci.py															  //网站自动下载歌词格式“歌曲-作者”

geqv.py															 //歌曲文件名格式处理工具

image_geci.py												 //歌曲封面单独下载处理工具（还需要调试）

zhengli.py														//歌曲文件夹下文件名提取工具

zhuanhuan.py												//同名歌曲删除工具（.mp3/.flac）

## 方案一、根据qq音乐歌单, 下载对应无损FLAC歌曲到本地.

首先要有qq音乐会员，下载歌曲后经过qqmusic_decrypt-master解密成flac文件。在经过MusicTag v1.0.9.0批量处理音乐歌词和封面即可

## 方案二、网站下载批量歌曲和歌词

首先手里要有歌曲名单，根据歌单TXT文件下载歌曲。（使用ceshi_2.0.py）

### 版权问题

如果涉及版权问题，项目将立刻关闭。 自己为QQ音乐会员, 该项目为方便自己而做