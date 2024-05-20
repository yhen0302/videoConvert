<script setup>
import { ref, onMounted } from "vue";
import Player from "xgplayer";
import "xgplayer/dist/index.min.css";
import HlsPlugin from "xgplayer-hls";
let videoArr = window.videoArr;
let isLoding = ref(false);
let curVideoName = ref("网络视频，加载失败请点击上方监控按钮");
let curRtspUrl = ref("");
let curHlsUrl = ref("");
onMounted(() => {
  for (let i = 0; i < videoArr.length; i++) {
    let video = videoArr[i];
    let btn = document.createElement("div");
    btn.innerHTML = video.name;
    btn.className = "btn";
    btn.id = "btn_" + i;
    btn.addEventListener("click", (e) => {
      isLoding.value = true;
      // 销毁之前按钮的流
      if (window.preUrl) {
        console.log("window.preUrl: ", window.preUrl);
        let rtsp_url = new FormData();
        rtsp_url.append("rtsp_url", window.preUrl);
        fetch("http://" + window.videoIP + "/stop", {
          method: "POST",
          body: rtsp_url,
        });
      }
      //获取当前按钮的流
      let rtsp_url = new FormData();
      rtsp_url.append("rtsp_url", video.url);
      fetch("http://" + window.videoIP + "/hls", {
        method: "POST",
        body: rtsp_url,
      })
        .then((res) => res.json())
        .then((res) => {
          console.log("res: ", res);
          if (res.code == 200) {
            player.src = res.data.url;
            player.play();
            window.preUrl = video.url;
            curVideoName.value = video.name;
            curRtspUrl.value = video.url;
            curHlsUrl.value = res.data.url;
            isLoding.value = false;
          } else if (res.code == 401) {
            curRtspUrl.value = "视频转码失败";
            curHlsUrl.value = "视频转码失败";
          }
        })
        .catch((error) => {
          console.log("error: ", error);
        });
    });

    let btnParent = document.querySelector(".btns");
    btnParent.appendChild(btn);
  }

  // 测试所有监控
  let promiseAll = document.querySelector(".promiseAll");
  promiseAll.addEventListener("click", async (e) => {
    let promiseArr = [];
    for (let i = 0; i < videoArr.length; i++) {
      let video = videoArr[i];
      let rtsp_url = new FormData();
      rtsp_url.append("rtsp_url", video.url);
      promiseArr.push(
        //发送请求后停止视频
        fetch("http://" + window.videoIP + "/hls", {
          method: "POST",
          body: rtsp_url,
        })
          .then((response) => {
            if (!response.ok) {
              throw new Error("Network response was not ok");
            }
            return response.json();
          })
          .catch((error) => {
            return { code: 500, message: error.message };
          })
          .finally(() => {
            fetch("http://" + window.videoIP + "/stop", {
              method: "POST",
              body: rtsp_url,
            });
          })
      );
    }
    try {
      let res = await Promise.all(promiseArr);
      res.forEach((i, idx) => {
        let name = videoArr[idx].name;
        let dom = document.querySelector("#btn_" + idx);
        if (i.code === 200) {
          console.log("监控启动成功");
          dom.style.backgroundColor = "green";
        } else if (i.code === 401) {
          console.log("监控启动失败");
          dom.style.backgroundColor = "red";
        } else {
          console.log("其他情况: ", i.message);
        }
      });
    } catch (error) {
      console.log("error: ", error);
    } finally {
      fetch("http://127.0.0.1:1399/stopAll", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
    }
  });

  //
  let player = new Player({
    id: "mse",
    plugins: [HlsPlugin],
    lang: "zh",
    isLive: true,
    autoplayMuted: true,
    autoplay: true,
    // url: "http://127.0.0.1:1399/stream_0/output.m3u8",
    url: "http://devimages.apple.com/iphone/samples/bipbop/gear1/prog_index.m3u8",
  });
});
</script>

<template>
  <div>
    <div class="btns"></div>
    <div class="btn promiseAll" v-show="true">点击测试所有监控</div>
    <p v-show="isLoding">正在加载中。。。</p>
    <div id="mse" style="width: 664px; height: 450px"></div>
    <p>当前监控名称为：《{{ curVideoName }}》</p>
    <p v-show="curRtspUrl">当前监控地址rtsp地址：《{{ curRtspUrl }}》</p>
    <p v-show="curHlsUrl">当前监控地址hls地址：《{{ curHlsUrl }}》</p>
  </div>
</template>

<style>
.btns {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  pointer-events: all;
  gap: 10px;
}

.btn {
  width: 100px;
  height: 20px;
  text-align: center;
  border: 1px solid #000;
  border-radius: 2px;
  cursor: pointer;
  box-shadow: 1px 1px 1px rgba(0, 0, 0, 0.3);
}

.promiseAll {
  width: 200px;
  margin: 10px auto;
}
#mse {
  margin: auto;
}
p {
  text-align: center;
}
</style>
