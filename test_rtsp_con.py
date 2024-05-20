# -*- coding: utf-8 -*-
import os.path
import subprocess
from datetime import datetime
import sys
result_write_file = True

current_path = os.getcwd()


def check_rtsp_has_video(rtsp_url):
    process = None
    command = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=codec_type', '-of',
               'default=noprint_wrappers=1:nokey=1', rtsp_url]
    print(" ".join(command))
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, _ = process.communicate(timeout=timeout)
        if process.returncode == 0 and output.strip() == b"video":
            return True
        else:
            return False
    except subprocess.TimeoutExpired:
        process.kill()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        timeout = 4
    else:
        timeout = int(sys.argv[1])
    monitor_urls = []
    if not os.path.exists("rtsp_urls"):
        os.chdir("../..")
    if not os.path.exists("rtsp_urls"):
        print("缺少rtsp_urls文件")
        exit(1)
    if os.path.exists("rtsp_urls"):
        with open("rtsp_urls", "r") as f:
            for line in f:
                monitor_urls.append(str(line.replace("\n", "")))
    if not os.path.exists("ffprobe.exe"):
        os.chdir("../..")
    if not os.path.exists("ffprobe.exe"):
        print("缺少ffprobe.exe文件")
        exit(1)
    invalid_rtsp_url = []
    effective_rtsp_url = []

    for url in monitor_urls:
        print(f"正在解析rtsp地址可用性: {url}")
        has_video = check_rtsp_has_video(url)
        if has_video:
            print(f"{url} contains video data.")
            effective_rtsp_url.append(url)
        else:
            print(f"{url} does not contain video data.")
            invalid_rtsp_url.append(url)

    if result_write_file:
        current_time = datetime.now().strftime("%Y年%m月%d日 %H时%M分%S秒")
        os.chdir(current_path)
        with open(f"{current_time}测试的延迟{timeout}秒的rtsp地址.txt", 'w') as file:
            file.write("有效的 RTSP 地址:\n")
            for url in effective_rtsp_url:
                file.write(f"{url}\n")
            file.write("\n无效的 RTSP 地址:\n")
            for url in invalid_rtsp_url:
                file.write(f"{url}\n")
    else:
        print(f"无效地址为:\n{invalid_rtsp_url}\n")
        print(f"有效地址为:\n{effective_rtsp_url}\n")
