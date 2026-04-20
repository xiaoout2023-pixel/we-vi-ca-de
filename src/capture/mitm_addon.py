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
_session_timestamp = None
_session_log_file = None
_session_data_file = None

def _get_logger(name):
    global _session_timestamp, _session_log_file, _session_data_file
    
    # 生成时间戳（只在第一次调用时）
    if _session_timestamp is None:
        _session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
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
        _session_log_file = os.path.join(log_dir, f"capture_{_session_timestamp}.log")
        _session_data_file = os.path.join(log_dir, f"captured_data_{_session_timestamp}.json")
        
        file_handler = logging.FileHandler(_session_log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Session timestamp: {_session_timestamp}")
        logger.info(f"Log file: {_session_log_file}")
        logger.info(f"Data file: {_session_data_file}")
    _loggers[name] = logger
    return logger

def get_session_data_file():
    """获取当前会话的数据文件路径"""
    return _session_data_file

logger = _get_logger("mitm_addon")

JS_INJECTION_CODE = """
(function(){
    var originalFetch = window.fetch;
    window.fetch = function() {
        var args = arguments;
        var result = originalFetch.apply(this, arguments);
        result.then(function(response) {
            try {
                response.clone().json().then(function(data) {
                    function findDecodeKey(obj, depth) {
                        if (depth > 10 || !obj) return null;
                        if (typeof obj === 'object') {
                            if (obj.decode_key || obj.decodeKey) {
                                return obj.decode_key || obj.decodeKey;
                            }
                            if (obj.media && Array.isArray(obj.media)) {
                                for (var i = 0; i < obj.media.length; i++) {
                                    var key = obj.media[i].decode_key || obj.media[i].decodeKey;
                                    if (key) return key;
                                }
                            }
                            var keys = Object.keys(obj);
                            for (var j = 0; j < keys.length; j++) {
                                var found = findDecodeKey(obj[keys[j]], depth + 1);
                                if (found) return found;
                            }
                        }
                        return null;
                    }
                    var key = findDecodeKey(data, 0);
                    if (key) {
                        var xhr = new XMLHttpRequest();
                        xhr.open('POST', 'http://127.0.0.1:18080/decode_key', false);
                        xhr.send(JSON.stringify({decode_key: key}));
                    }
                });
            } catch(e) {}
        });
        return result;
    };
})();
"""


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

        # 确保session数据文件路径已初始化
        data_file_from_session = get_session_data_file()
        if data_file_from_session:
            self.data_file = data_file_from_session
        else:
            # 如果还没初始化，创建一个新的时间戳文件
            if not data_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_dir = os.path.join(base_dir, "capture_logs")
                os.makedirs(log_dir, exist_ok=True)
                self.data_file = os.path.join(log_dir, f"captured_data_{timestamp}.json")
            else:
                self.data_file = data_file

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
                # Only capture actual video responses, not thumbnails
                content_type = flow.response.headers.get("Content-Type", "") if flow.response else ""
                if "video" not in content_type.lower():
                    # Skip thumbnails (image/jpg, etc.)
                    return

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
                logger.info(f"      Cookie: {cookie[:50]}..." if cookie else "      Cookie: (empty)")
                self.captured_data.append(("video_url", video_info))
                self._save_to_file()

            elif "channels.weixin.qq.com/web/pages/feed" in url and flow.response:
                # Intercept the feed HTML page and inject JS to capture decode_key
                content_type = flow.response.headers.get("Content-Type", "")
                body = flow.response.text
                if body and "</head>" in body:
                    injection = f'<script>{JS_INJECTION_CODE}</script>'
                    body = body.replace("</head>", injection + "</head>", 1)
                    flow.response.text = body
                    logger.info("★★★ JS注入: 已注入decode_key捕获代码到feed页面")
                elif body and len(body) > 100:
                    # Even if Content-Type is empty, try to inject if it looks like HTML
                    if "<html" in body.lower() or "<!doctype" in body.lower() or "<script" in body.lower():
                        injection = f'<script>{JS_INJECTION_CODE}</script>'
                        if "</head>" in body:
                            body = body.replace("</head>", injection + "</head>", 1)
                        else:
                            body = injection + body
                        flow.response.text = body
                        logger.info("★★★ JS注入: 已注入decode_key捕获代码到feed页面(无Content-Type)")

            elif ("channels.weixin.qq.com" in url and ".js" in url and flow.response and
                  "application/javascript" in flow.response.headers.get("Content-Type", "")):
                # Inject JS into WeChat's JavaScript files
                body = flow.response.text
                if body and "decode_key" not in body:  # Only inject once
                    injection = f"\n{JS_INJECTION_CODE}\n"
                    body = injection + body
                    flow.response.text = body
                    logger.info(f"★★★ JS注入: 已注入decode_key捕获代码到JS文件: {url.split('/')[-1][:50]}")

            elif "channels.weixin.qq.com/web/api/feed" in url:
                try:
                    response_data = json.loads(flow.response.text)
                    logger.info("★★★ 拦截到feed API响应，解析中...")
                    self._extract_from_api_response(response_data, flow)
                except Exception as e:
                    logger.error(f"解析API响应失败: {e}")
                    import traceback
                    logger.error(traceback.format_exc())

            elif is_wechat and flow.response and flow.response.headers.get("Content-Type", "").startswith("application/json"):
                # 通用JSON响应扫描：查找所有微信API返回的decode_key
                self._scan_json_for_decode_key(flow)

            elif is_wechat and flow.response:
                # 也扫描非JSON响应中的decode_key（可能在HTML或JS中）
                body = flow.response.text
                if body and ('decode_key' in body or 'decodeKey' in body):
                    logger.info(f"★★★ 在非JSON响应中发现decode_key: {url[:80]}")
                    # 尝试从文本中提取decode_key
                    import re
                    # 匹配数字形式的decode_key
                    patterns = [
                        r'"decode_key"\s*:\s*(\d+)',
                        r'"decodeKey"\s*:\s*(\d+)',
                        r'decode_key["\s:=]+(\d+)',
                        r'decodeKey["\s:=]+(\d+)',
                    ]
                    for pattern in patterns:
                        matches = re.findall(pattern, body)
                        for match in matches:
                            logger.info(f"★★★ 提取到decode_key: {match}")
                            self._save_decode_key(match, flow)

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

    def _scan_json_for_decode_key(self, flow):
        """扫描所有JSON响应查找decode_key"""
        try:
            response_text = flow.response.text
            if not response_text or len(response_text) > 1000000:  # Skip very large responses
                return

            # Quick check if decode_key might be present
            if 'decode_key' not in response_text and 'decodeKey' not in response_text:
                return

            response_data = json.loads(response_text)
            self._find_decode_key_recursive(response_data, flow, path="root")
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.error(f"JSON扫描失败: {e}")

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
