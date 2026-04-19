import os
import aiohttp
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VideoDownloader:
    async def download(self, url, cookie, output_path, timeout=300):
        logger.info(f"Downloading video from: {url[:80]}...")
        headers = {
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=timeout) as resp:
                if resp.status != 200:
                    raise Exception(f"Download failed: HTTP {resp.status}")
                total_size = int(resp.headers.get('content-length', 0))
                downloaded = 0
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'wb') as f:
                    async for chunk in resp.content.iter_chunked(8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            if int(percent) % 10 == 0:
                                logger.debug(f"Download progress: {percent:.1f}%")
        file_size = os.path.getsize(output_path)
        logger.info(f"Download completed: {output_path} ({file_size / 1024 / 1024:.2f} MB)")
        return output_path
