import time
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SessionManager:
    def __init__(self):
        self.videos = {}
        self.ready_videos = []
        self.latest_decode_key = None
        self.latest_cookie = None

    def add_video_url(self, url, cookie, title=None, video_type="mp4", file_size=None):
        video_id = self._extract_video_id(url)
        if not video_id:
            video_id = f"video_{int(time.time())}"
        self.videos[video_id] = {
            "url": url,
            "cookie": cookie,
            "title": title or f"video_{int(time.time())}",
            "type": video_type,
            "file_size": file_size,
            "timestamp": time.time()
        }
        self.latest_cookie = cookie
        logger.info(f"Added video URL: {video_id}")
        self._check_match(video_id)

    def add_decode_key(self, decode_key, video_id=None):
        self.latest_decode_key = decode_key
        matched = False
        if video_id and video_id in self.videos:
            self.videos[video_id]["decode_key"] = decode_key
            self._check_match(video_id)
            matched = True
        if not matched:
            for vid, video in self.videos.items():
                if "decode_key" not in video or not video.get("decode_key"):
                    video["decode_key"] = decode_key
                    self._check_match(vid)
                    break
        logger.info(f"Added decode_key: {decode_key}")

    def add_cookie(self, cookie):
        self.latest_cookie = cookie
        for video_id, video in self.videos.items():
            if not video.get("cookie"):
                video["cookie"] = cookie
                self._check_match(video_id)

    def _check_match(self, video_id):
        video = self.videos.get(video_id)
        if not video:
            return
        if not video.get("decode_key"):
            if self.latest_decode_key:
                video["decode_key"] = self.latest_decode_key
            else:
                return
        if not video.get("cookie"):
            if self.latest_cookie:
                video["cookie"] = self.latest_cookie
        if video.get("url") and video.get("decode_key"):
            if video not in self.ready_videos:
                self.ready_videos.append(video)
                logger.info(f"Video ready for processing: {video['title']}")

    def get_ready_videos(self):
        return self.ready_videos.copy()

    def clear(self):
        self.videos.clear()
        self.ready_videos.clear()
        self.latest_decode_key = None
        self.latest_cookie = None

    def _extract_video_id(self, url):
        import re
        match = re.search(r'idx=(\d+)', url)
        if match:
            return f"idx_{match.group(1)}"
        match = re.search(r'm=([a-f0-9]+)', url)
        if match:
            return f"m_{match.group(1)[:8]}"
        return None
