### 修改后端转码配置：./config.json

### 运行后端转码：双击./start_main.vbs

### rtsp_urls 文件为需要测试 rtsp 的所有 url

### cmd 运行 rtsp_url 有效性：./dist/test_rtsp_con/test_rtsp_con.exe 4 (超时时间(默认 4 秒))

### 输出结果当前的文件夹的 txt 文件

### 前端请求路径:

发起转码：/hls POST 请求 Body(application/form-data) 参数: rtsp_url rtsp://账号:密码@IP:554/cam/realmonitor?channel=1&subtype=0

停止转码：/stop POST 请求 Body(application/form-data) 参数: rtsp_url rtsp://账号:密码@IP:554/cam/realmonitor?channel=1&subtype=0

停止所有视频转码：/stopAll POST 无参数

### 修改前端播放配置：./xgplayer/public/public.js

### 运行前端播放：npm run dev 或者打包之后 nginx 代理
