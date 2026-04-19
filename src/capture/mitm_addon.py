import json
import time
import re
import os
import sys
import logging
from mitmproxy import http

# Self-contained logging setup to avoid import issues when loaded by mitmdump
_loggers = {}

def _get_logger(name):
    if name in _loggers:
        return _loggers[name]
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
        # Console handler - output ALL logs including DEBUG
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler - also save to file
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)))
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "wechat_video.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Logger initialized, outputting to console and {log_file}")
    _loggers[name] = logger
    return logger

logger = _get_logger("mitm_addon")


class VideoCaptureAddon:
    def __init__(self, data_file=None):
        self.captured_data = []
        self.all_requests_log = []
        self.request_count = 0
        self.wechat_request_count = 0
        self.video_capture_count = 0
        self.key_capture_count = 0
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_file = data_file or os.path.join(base_dir, "captured_data.json")
        self.log_dir = os.path.join(base_dir, "capture_logs")
        os.makedirs(self.log_dir, exist_ok=True)
        logger.info("=" * 60)
        logger.info("VideoCaptureAddon initialized")
        logger.info(f"Data file: {self.data_file}")
        logger.info(f"Log dir: {self.log_dir}")
        logger.info("=" * 60)

    def response(self, flow: http.HTTPFlow):
        self.request_count += 1
        user_agent = flow.request.headers.get("User-Agent", "")
        is_wechat = "WeChat" in user_agent or "MicroMessenger" in user_agent
        
        if is_wechat:
            self.wechat_request_count += 1

        request_info = {
            "timestamp": time.time(),
            "url": flow.request.url,
            "method": flow.request.method,
            "user_agent": user_agent[:100],
            "is_wechat": is_wechat,
            "status_code": flow.response.status_code if flow.response else None,
            "content_type": flow.response.headers.get("Content-Type", "") if flow.response else "",
            "content_length": flow.response.headers.get("Content-Length", "") if flow.response else "",
        }
        self.all_requests_log.append(request_info)

        # 输出每个请求的详细信息到控制台
        if is_wechat:
            logger.info(f"[#{self.request_count}] [微信] {flow.request.method} {flow.request.url}")
            logger.info(f"      UA: {user_agent[:100]}")
            logger.info(f"      CT: {request_info['content_type']}")
        else:
            # 非微信请求也输出，方便调试
            if self.request_count % 10 == 0:
                logger.info(f"[#{self.request_count}] [其他] {flow.request.method} {flow.request.url[:100]}")

        if is_wechat:
            url = flow.request.url

            if "finder.video.qq.com" in url and "stodownload" in url:
                self.video_capture_count += 1
                cookie = flow.request.headers.get("Cookie", "")
                video_info = {
                    "url": url,
                    "cookie": cookie,
                    "title": f"video_{int(time.time())}",
                    "timestamp": time.time(),
                    "type": "mp4"
                }
                logger.info(f"★★★ 捕获第{self.video_capture_count}个视频URL: {url[:80]}")
                self.captured_data.append(("video_url", video_info))
                self._save_to_file()

            elif "channels.weixin.qq.com/web/api/feed" in url:
                try:
                    response_data = json.loads(flow.response.text)
                    logger.info("★★★ 拦截到feed API响应，解析中...")
                    self._extract_from_api_response(response_data, flow)
                except Exception as e:
                    logger.error(f"解析API响应失败: {e}")
                    import traceback
                    logger.error(traceback.format_exc())

            elif ".m3u8" in url or "m3u8" in flow.request.path.lower():
                self.video_capture_count += 1
                logger.info(f"★★★ 捕获m3u8播放列表: {url[:80]}")
                video_info = {
                    "url": url,
                    "cookie": flow.request.headers.get("Cookie", ""),
                    "title": f"video_m3u8_{int(time.time())}",
                    "timestamp": time.time(),
                    "type": "m3u8"
                }
                self.captured_data.append(("video_url", video_info))
                self._save_to_file()
            else:
                # 检测可能的视频URL
                for domain in ["mp4", "video", "stodownload"]:
                    if domain in url.lower():
                        logger.info(f"[可能视频] {url[:80]}")
                        break

    def _extract_from_api_response(self, response_data, flow):
        try:
            data = response_data.get("data", {})
            object_desc = data.get("object_desc", {})
            media_list = object_desc.get("media", [])
            if not media_list:
                media_list = data.get("media", [])
            if not media_list:
                return

            for media in media_list:
                decode_key = media.get("decode_key") or media.get("decodeKey")
                url = media.get("url")
                file_size = media.get("file_size")

                if decode_key:
                    logger.info(f"Captured decode_key: {decode_key}")
                    video_id = f"key_{int(time.time())}"
                    key_info = {"video_id": video_id, "decode_key": decode_key, "timestamp": time.time()}
                    self.captured_data.append(("decode_key", key_info))
                    self._save_to_file()

                if url:
                    logger.info(f"Captured video URL from API: {url[:80]}...")
                    video_info = {
                        "url": url,
                        "cookie": flow.request.headers.get("Cookie", ""),
                        "title": object_desc.get("description", f"video_{int(time.time())}"),
                        "timestamp": time.time(),
                        "type": "mp4",
                        "file_size": file_size
                    }
                    self.captured_data.append(("video_url", video_info))
                    self._save_to_file()
        except Exception as e:
            logger.error(f"Failed to extract from API: {e}")

    def request(self, flow: http.HTTPFlow):
        pass

    def _save_to_file(self):
        data = {
            "timestamp": time.time(),
            "captured_data": [{"type": t, "data": d} for t, d in self.captured_data]
        }
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save capture data: {e}")

    def save_capture_log(self):
        timestamp = int(time.time())
        log_file = os.path.join(self.log_dir, f"capture_{timestamp}.json")
        log_data = {
            "timestamp": timestamp,
            "total_requests": len(self.all_requests_log),
            "captured_videos": len([d for d in self.captured_data if d[0] == "video_url"]),
            "captured_keys": len([d for d in self.captured_data if d[0] == "decode_key"]),
            "all_requests": self.all_requests_log,
            "captured_data": [{"type": t, "data": d} for t, d in self.captured_data]
        }
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Capture log saved to: {log_file}")
        return log_file


# Create instance and register
video_capture_addon = VideoCaptureAddon()
addons = [video_capture_addon]
