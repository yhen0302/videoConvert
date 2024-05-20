import atexit
import json
import os
import shutil
import subprocess
import threading
import time

import cv2
from flask import Flask, request, send_from_directory
from flask_cors import CORS

m3u8_directory = ""
ffmpeg_processes = {}
file_name = "output.m3u8"
rtsp_url_path = {}
DEBUG = True
success_code = 200
lock = False
sleep_time = 0.2
valid_rtsp_url = []
not_valid_rtsp_url = []
app = Flask(__name__)


class Response(object):
    @staticmethod
    def __success__(code=success_code, msg="success", data=None):
        return {"code": code, "message": msg, "data": data}

    @staticmethod
    def __fail__(code=401, msg="fail", data=None):
        return {"code": code, "message": msg, "data": data}


def periodic_cleanup():
    interval = config_json.get("clearVideoIntervalTime", 60)
    while True:
        if m3u8_directory == "" or not os.path.exists(m3u8_directory):
            continue
        for stream_dir in os.listdir(m3u8_directory):
            stream_path = os.path.join(m3u8_directory, stream_dir)
            if os.path.isdir(stream_path):
                for root, dirs, files in os.walk(stream_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_modified_time = os.path.getmtime(file_path)
                            current_time = time.time()
                            time_difference = current_time - file_modified_time
                            if time_difference > interval:
                                try:
                                    os.remove(file_path)
                                    print(f"删除文件: {file_path}")
                                except Exception as e:
                                    if DEBUG:
                                        print(f"删除文件失败: {file_path}, 错误信息: {str(e)}")
                        except Exception as e:
                            if DEBUG:
                                print(f"获取文件修改时间失败: {file_path}, 错误信息: {str(e)}")

        time.sleep(interval)


def run_ffmpeg_command(rtsp_url, m3u8_file_path):
    if not os.path.exists(os.path.dirname(m3u8_file_path)):
        os.makedirs(os.path.dirname(m3u8_file_path))
    ffmpeg_command = [
        "ffmpeg",
        "-i", rtsp_url,
        "-c:v", "copy",
        "-g", g,
        "-hls_time", hls_time,
        "-hls_list_size", hls_list_size,
        m3u8_file_path
    ]
    print(" ".join(ffmpeg_command))
    ffmpeg_processes[rtsp_url] = subprocess.Popen(ffmpeg_command)


def check_video_transfer(rtsp_url):
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        return False
    ret, frame = cap.read()
    if not ret:
        return False
    cap.release()
    return True


@app.route('/hls', methods=['POST'])
def hls():
    rtsp_url = request.form.get("rtsp_url")
    if rtsp_url is None:
        return Response.__fail__(msg="rtsp_url is not null")
    if DEBUG:
        print(f"正在解析地址可用性: {rtsp_url}")
    if not check_video_transfer(rtsp_url):
        if rtsp_url in valid_rtsp_url:
            valid_rtsp_url.remove(rtsp_url)
        if rtsp_url not in not_valid_rtsp_url:
            not_valid_rtsp_url.append(rtsp_url)
        return Response.__fail__(msg="该视频地址没有数据传输,请检查地址是否为有效视频流地址")
    else:
        if rtsp_url not in valid_rtsp_url:
            valid_rtsp_url.append(rtsp_url)
        if rtsp_url in not_valid_rtsp_url:
            not_valid_rtsp_url.remove(rtsp_url)
    if not os.path.exists(m3u8_directory):
        os.makedirs(m3u8_directory)
    global lock
    while lock:
        time.sleep(sleep_time)
    lock = True
    stopAll()
    if rtsp_url in rtsp_url_path.keys():
        proc = ffmpeg_processes.get(rtsp_url)
        if proc is not None:
            response = stop_stream(rtsp_url)
            if response.get("code") != success_code:
                lock = False
                return response

        path = rtsp_url_path.get(rtsp_url)
        stream_name = os.path.basename(path)
        hls_stream_len = os.path.join(m3u8_directory, stream_name)

    else:
        stream_name = f"stream_{str(len(rtsp_url_path))}"
        hls_stream_len = os.path.join(m3u8_directory, stream_name)
        while os.path.exists(hls_stream_len):
            if not remove_dir(hls_stream_len):
                rtsp_url_path.__setitem__(stream_name, None)
                stream_name = f"stream_{str(len(rtsp_url_path))}"
                hls_stream_len = os.path.join(m3u8_directory, stream_name)

    if not os.path.exists(hls_stream_len):
        os.makedirs(hls_stream_len)
    m3u8_file_path = os.path.join(hls_stream_len, file_name)
    thread = threading.Thread(target=run_ffmpeg_command, args=(rtsp_url, m3u8_file_path))
    thread.daemon = True
    thread.start()
    rtsp_url_path.__setitem__(rtsp_url, hls_stream_len)
    maximumDelayTime = pollingTimes
    while maximumDelayTime > 0:
        if os.path.exists(m3u8_file_path):
            http_url = f"http://{ip}:{port}/{stream_name}/{file_name}"
            lock = False
            return Response.__success__(data={"url": http_url})
        else:
            time.sleep(0.2)
            maximumDelayTime -= 1
    msg = f"转换失败,未查找到转换后的文件，请查看{os.path.dirname(m3u8_file_path)}文件是否存在，如果存在请增加config.json中的pollingTimes值再重试"
    print(msg)
    lock = False
    return Response.__fail__(msg=msg)


@app.route('/getValidRtspUrl', methods=["GET"])
def getValidRtspUrl():
    return Response.__success__(data={"valid_rtsp_url": valid_rtsp_url})


@app.route('/getNotValidRtspUrl', methods=["GET"])
def getNotValidRtspUrl():
    return Response.__success__(data={"not_valid_rtsp_url": not_valid_rtsp_url})


def remove_dir(dir_path):
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        print(f"{dir_path}不存在或不是文件夹")
    try:
        shutil.rmtree(dir_path)
        return True
    except Exception as e:
        if DEBUG:
            print(f"删除{dir_path}文件失败")
    return False


def remove_file(file_path):
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        print(f"{file_path}不存在或不是文件")
    os.remove(file_path)


@app.route('/stop', methods=['POST'])
def stop():
    rtsp_url = request.form.get("rtsp_url")
    if rtsp_url is None:
        return Response.__fail__(msg="rtsp_url is not null")
    return stop_stream(rtsp_url)


@app.route('/stopAll', methods=['POST', 'GET'])
def stopAll():
    for rtsp_url in ffmpeg_processes:
        proc = ffmpeg_processes.__getitem__(rtsp_url)
        proc.terminate()
        output_m3u8_file_path = rtsp_url_path.get(rtsp_url)
        remove_dir(output_m3u8_file_path)
    return Response.__success__()


def stop_stream(rtsp_url):
    proc = ffmpeg_processes.get(rtsp_url)
    if proc is None:
        return Response.__fail__(msg=f"该链接没有运行的转码服务")
    proc.terminate()
    output_m3u8_file_path = rtsp_url_path.get(rtsp_url)
    remove_dir(output_m3u8_file_path)
    return Response.__success__()


@app.route('/<path:path>')
def serve_files(path):
    if os.path.isfile(os.path.join(m3u8_directory, path)):
        return send_from_directory(m3u8_directory, path)
    else:
        print(f"没有{path}这个文件")
        return Response.__fail__(msg=f"not found {path}")


@app.route('/testCon', methods=["GET", "POST"])
def testCon():
    return Response.__success__()


def cleanup():
    for path in rtsp_url_path.values():
        if path and os.path.exists(path):
            try:
                shutil.rmtree(path)
                if DEBUG:
                    print(f"删除文件成功 {path}")
            except Exception as e:
                if DEBUG:
                    print(f"删除文件失败 {path}")


if __name__ == '__main__':
    if not os.path.exists("config.json"):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(current_dir)
        os.chdir("../../..")
    if not os.path.exists("config.json"):
        print("config.json没有找到")
        exit(1)

    with open("config.json", "r") as f:
        try:
            config_json = json.load(f)
        except Exception as e:
            print("config.json文件数据有误")
            exit(1)

    port = config_json.get("port", None)
    if port is None:
        print("port未配置")
        exit(1)

    DEBUG_value = config_json.get("DEBUG", "False")
    DEBUG = DEBUG_value.lower() == "true"
    if DEBUG:
        print(f"当前工作环境{os.getcwd()}")
    ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg.exe")
    ffplay_path = os.path.join(os.getcwd(), "ffplay.exe")
    ffprobe_path = os.path.join(os.getcwd(), "ffprobe.exe")
    if not os.path.exists(ffmpeg_path) or not os.path.exists(ffplay_path) or not os.path.exists(ffprobe_path):
        print(f"ffmpeg文件缺失，请检查下列文件是否存在\n{ffmpeg_path}\n{ffplay_path}\n{ffprobe_path}")
        exit(1)
    cleanup_thread = threading.Thread(target=periodic_cleanup)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    atexit.register(cleanup)

    ip = config_json.get("ip", "127.0.0.1")
    pollingTimes = config_json.get("pollingTimes", 20)

    m3u8FileSavePath = str(config_json.get("m3u8FileSavePath", os.getcwd()))
    hls_time = str(config_json.get("hls_time", "1"))
    hls_list_size = str(config_json.get("hls_list_size", "4"))
    g = str(config_json.get("g", "10"))
    if DEBUG:
        print("m3u8FileSavePath = " + m3u8FileSavePath)
        print("hls_time = " + hls_time)
        print("hls_list_size = " + hls_list_size)
        print("g = " + g)
    if not os.path.exists(m3u8FileSavePath):
        os.makedirs(m3u8FileSavePath)
    m3u8_directory = os.path.join(m3u8FileSavePath, "m3u8")
    CORS(app, resources=r'/*')
    app.run(host=ip, port=port)
