import json
import time
import re
import os
import sys
import logging
from datetime import datetime
from mitmproxy import http

# Self-contained logging setup to avoid import issues when loaded by mitmdump
_loggers = {}
_session_log_file = None

def _get_logger(name):
    global _session_log_file
    
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
        
        # File handler - save to timestamped file
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "capture_logs")
        os.makedirs(log_dir, exist_ok=True)
        
        if _session_log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            _session_log_file = os.path.join(log_dir, f"mitm_{timestamp}.log")
        
        file_handler = logging.FileHandler(_session_log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Logger initialized, outputting to console and {_session_log_file}")
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
        self.domain_stats = {}  # 统计所有域名
        self.last_stats_time = time.time()
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
            
            # 统计域名
            from urllib.parse import urlparse
            parsed = urlparse(flow.request.url)
            domain = parsed.hostname or parsed.netloc
            self.domain_stats[domain] = self.domain_stats.get(domain, 0) + 1
            
            # 每5秒输出一次域名统计
            current_time = time.time()
            if current_time - self.last_stats_time >= 5:
                self._print_domain_stats()
                self.last_stats_time = current_time

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

            # ★ 新增：拦截 finder.weixin.qq.com API响应，提取decode_key
            if "finder.weixin.qq.com" in url and flow.response and flow.response.text:
                logger.info(f"★★★ 拦截到 finder.weixin.qq.com 响应: {url[:100]}")
                try:
                    response_text = flow.response.text[:5000]
                    logger.info(f"响应内容（前5000字符）: {response_text}")
                    
                    # 尝试解析JSON
                    try:
                        response_data = json.loads(flow.response.text)
                        self._extract_decode_key_from_finder_api(response_data, flow)
                    except json.JSONDecodeError:
                        logger.info("响应不是JSON格式，可能是protobuf或其他格式")
                except Exception as e:
                    logger.error(f"处理finder.weixin.qq.com响应失败: {e}")

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

    def _print_domain_stats(self):
        """输出微信请求的域名统计"""
        if not self.domain_stats:
            return
        
        sorted_domains = sorted(self.domain_stats.items(), key=lambda x: x[1], reverse=True)
        top_domains = sorted_domains[:15]
        
        logger.info("=" * 80)
        logger.info(f"【域名统计】(总计 {len(self.domain_stats)} 个域名, {self.wechat_request_count} 个微信请求)")
        for i, (domain, count) in enumerate(top_domains, 1):
            marker = "★★★" if "finder" in domain or "video" in domain else "   "
            logger.info(f"  {marker} {i:2d}. {domain:50s} - {count:5d} 次请求")
        logger.info("=" * 80)

    def _extract_decode_key_from_finder_api(self, response_data, flow):
        """从finder.weixin.qq.com API响应中提取decode_key"""
        try:
            # 递归查找所有可能的decodeKey字段
            self._find_decode_key_recursive(response_data, flow, path="root")
        except Exception as e:
            logger.error(f"提取decode_key失败: {e}")

    def _find_decode_key_recursive(self, data, flow, path="root", depth=0):
        """递归查找JSON中的decodeKey字段"""
        if depth > 10:  # 限制递归深度
            return
            
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}"
                # 检查是否是decodeKey相关字段
                if key.lower() in ['decodekey', 'decode_key', 'decodekeylist', 'decode_keys']:
                    logger.info(f"★★★ 在 {current_path} 找到 {key}: {value}")
                    self._save_decode_key(value, flow)
                else:
                    # 继续递归
                    self._find_decode_key_recursive(value, flow, current_path, depth + 1)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._find_decode_key_recursive(item, flow, f"{path}[{i}]", depth + 1)

    def _save_decode_key(self, decode_key, flow):
        """保存decode_key到文件"""
        if not decode_key:
            return
            
        self.key_capture_count += 1
        key_info = {
            "decode_key": str(decode_key),
            "source": "finder.weixin.qq.com",
            "url": flow.request.url,
            "timestamp": time.time(),
            "capture_order": self.key_capture_count
        }
        logger.info(f"★★★ 捕获第{self.key_capture_count}个decode_key: {decode_key}")
        self.captured_data.append(("decode_key", key_info))
        self._save_to_file()

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
