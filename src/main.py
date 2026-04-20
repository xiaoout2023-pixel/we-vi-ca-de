import os
import sys
import time
import asyncio
import json
from pathlib import Path
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import get_logger
from src.utils.file_utils import clean_directory, ensure_directory, sanitize_filename
from src.utils.proxy_utils import is_port_in_use, kill_process_on_port, is_proxy_enabled, get_proxy_server, disable_proxy, enable_proxy
from src.capture.session_manager import SessionManager
from src.download.video_downloader import VideoDownloader
from src.decode.video_decoder import VideoDecoder

logger = get_logger(__name__)

OUTPUT_DIR = "output"
TEMP_DIR = "temp"
PROXY_PORT = 8080
CAPTURE_LOGS_DIR = str(Path(__file__).parent.parent / "src" / "capture_logs")


def find_latest_capture_data_file():
    """Find the most recent captured_data_*.json file in capture_logs/"""
    if not os.path.exists(CAPTURE_LOGS_DIR):
        return None
    files = [f for f in os.listdir(CAPTURE_LOGS_DIR) if f.startswith("captured_data_") and f.endswith(".json")]
    if not files:
        return None
    files.sort(reverse=True)  # Sort by filename (timestamp) descending
    return os.path.join(CAPTURE_LOGS_DIR, files[0])

def check_environment():
    logger.info("Checking environment...")
    try:
        import mitmproxy
        try:
            version = mitmproxy.version.VERSION
        except AttributeError:
            version = getattr(mitmproxy, '__version__', 'unknown')
        logger.info(f"mitmproxy version: {version}")
    except ImportError:
        logger.error("mitmproxy not installed. Run: pip install mitmproxy")
        sys.exit(1)
    try:
        import aiohttp
        logger.info("aiohttp: OK")
    except ImportError:
        logger.error("aiohttp not installed. Run: pip install aiohttp")
        sys.exit(1)
    ensure_directory(OUTPUT_DIR)
    ensure_directory(TEMP_DIR)
    logger.info("Environment check passed")


def check_and_cleanup_port(port):
    """检查端口是否被占用，如被占用则清理"""
    if is_port_in_use(port):
        print(f"警告: 端口 {port} 已被占用")
        print("正在清理...")
        killed = kill_process_on_port(port)
        if killed:
            print(f"已关闭占用端口的进程: {', '.join(killed)}")
            time.sleep(1)
            if is_port_in_use(port):
                print(f"端口 {port} 仍被占用，请手动清理后重试")
                print("或运行 clean.bat 进行清理")
                return False
        else:
            print("未找到占用进程，端口可能刚被释放")
            time.sleep(1)
            if is_port_in_use(port):
                print(f"端口 {port} 仍被占用，请手动清理")
                return False
    return True


def read_captured_data(data_file):
    if not os.path.exists(data_file):
        return []
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("captured_data", [])
    except:
        return []


async def monitor_capture(session_manager, data_file, stop_event):
    last_count = 0
    last_log_time = 0
    while not stop_event.is_set():
        captured_data = read_captured_data(data_file)
        current_count = len(captured_data)
        
        # 有新数据时同步
        if current_count > last_count:
            new_items = captured_data[last_count:]
            for item in new_items:
                event_type = item.get("type")
                event_data = item.get("data", {})
                if event_type == "video_url":
                    session_manager.add_video_url(
                        event_data.get("url", ""),
                        event_data.get("cookie", ""),
                        event_data.get("title"),
                        event_data.get("type", "mp4"),
                        event_data.get("file_size")
                    )
                elif event_type == "decode_key":
                    session_manager.add_decode_key(
                        event_data.get("decode_key", ""),
                        event_data.get("video_id")
                    )
            last_count = current_count
            logger.info(f"Synced {len(new_items)} new capture(s)")
        
        # 每5秒显示一次状态
        current_time = time.time()
        if current_time - last_log_time >= 5:
            videos = sum(1 for d in captured_data if d.get("type") == "video_url")
            keys = sum(1 for d in captured_data if d.get("type") == "decode_key")
            print(f"\r[捕获中] 视频URL: {videos} 条 | decode_key: {keys} 条 | 按Ctrl+C结束", end="", flush=True)
            last_log_time = current_time

        await asyncio.sleep(0.5)


class DecodeKeyReceiver:
    """HTTP server to receive decode_key from injected JS in the web player"""
    def __init__(self, session_manager, port=18080):
        self.session_manager = session_manager
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        receiver = self
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                if self.path == '/decode_key':
                    content_length = int(self.headers.get('Content-Length', 0))
                    body = self.rfile.read(content_length)
                    try:
                        data = json.loads(body)
                        decode_key = data.get('decode_key')
                        if decode_key:
                            logger.info(f"通过JS注入获取decode_key: {decode_key}")
                            receiver.session_manager.add_decode_key(decode_key)
                            self.send_response(200)
                            self.send_header('Content-Type', 'text/plain')
                            self.end_headers()
                            self.wfile.write(b'OK')
                    except Exception as e:
                        logger.error(f"处理decode_key失败: {e}")
                        self.send_response(400)
                        self.end_headers()
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                pass  # Suppress default logging

        self.server = HTTPServer(('127.0.0.1', self.port), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        logger.info(f"decode_key接收服务器已启动: http://127.0.0.1:{self.port}")

    def stop(self):
        if self.server:
            self.server.shutdown()


async def main():
    print("=" * 60)
    print("微信视频捕获解密工具 v1.0")
    print("支持：个人微信 / 企业微信")
    print("=" * 60)

    check_environment()
    session_manager = SessionManager()

    # Start decode_key receiver server (for JS injection)
    decode_key_server = DecodeKeyReceiver(session_manager, port=18080)
    decode_key_server.start()
    print("decode_key接收服务器已启动 (端口 18080)")

    addon_path = str(Path(__file__).parent / "capture" / "mitm_addon.py")
    project_root = str(Path(__file__).parent.parent)

    print(f"\n[0/4] 检查环境...")
    if not check_and_cleanup_port(PROXY_PORT):
        print("\n清理失败，请运行 clean.bat 手动清理后重试")
        return
    print(f"端口 {PROXY_PORT} 可用")

    original_proxy_enabled = is_proxy_enabled()
    original_proxy_server = get_proxy_server()
    proxy_was_enabled = original_proxy_enabled

    if original_proxy_enabled:
        print(f"检测到代理已开启: {original_proxy_server}")
        if original_proxy_server != f"127.0.0.1:{PROXY_PORT}":
            print("注意: 当前代理不是指向本工具，退出时会恢复原代理设置")

    # Remove old capture data files before starting
    if os.path.exists(CAPTURE_LOGS_DIR):
        for f in os.listdir(CAPTURE_LOGS_DIR):
            if f.startswith("captured_data_") and f.endswith(".json"):
                os.remove(os.path.join(CAPTURE_LOGS_DIR, f))

    print(f"\n[1/4] 正在启动 mitmdump (端口 {PROXY_PORT})...")
    
    # 输出详细调试信息
    print("\n" + "=" * 60)
    print("启动调试信息:")
    print(f"  Python 路径: {sys.executable}")
    print(f"  项目根目录: {project_root}")
    print(f"  Addon 路径: {addon_path}")
    print(f"  工作目录: {os.getcwd()}")
    print(f"  Python PATH: {os.environ.get('PYTHONPATH', '未设置')}")
    print()
    
    # Use mitmdump from mitmproxy.tools.main instead of python -m mitmproxy.tools.dump
    # because the latter doesn't have a proper __main__ entry point
    cmd = [
        sys.executable, "-c",
        "from mitmproxy.tools.main import mitmdump; mitmdump()",
        "--listen-port", str(PROXY_PORT),
        "--set", "flow_detail=0",
        "--set", "connection_strategy=lazy",
        "--set", "ssl_insecure=true",
        "-s", addon_path,
    ]
    
    print(f"完整命令行:")
    print(f"  {' '.join(cmd)}")
    print()
    
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = project_root
    
    # 打印所有环境变量
    print("关键环境变量:")
    for key in ["PYTHONPATH", "PYTHONUNBUFFERED", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY"]:
        if key in env:
            print(f"  {key}={env[key]}")
    print("=" * 60)
    print()
    
    try:
        # 不重定向输出，让mitmdump日志直接打印到控制台
        mitm_process = subprocess.Popen(
            cmd,
            env=env,
            cwd=project_root
        )
    except Exception as e:
        print(f"\n启动 mitmdump 失败: {e}")
        logger.error(f"启动 mitmdump 失败: {e}")
        import traceback
        traceback.print_exc()
        return

    time.sleep(3)
    rc = mitm_process.poll()
    if rc is not None:
        print(f"\nmitmdump 启动失败 (退出码: {rc})")
        print("请查看上方输出的mitmdump日志了解详细错误信息")
        print(f"可能原因:")
        print(f"  1. 端口 {PROXY_PORT} 已被占用")
        print("  2. mitmproxy 未正确安装")
        print("  3. addon文件加载错误")
        print(f"\n请尝试手动运行:")
        print(f"  mitmdump --listen-port {PROXY_PORT} -s {addon_path}")
        return

    print("mitmdump 已启动")

    print(f"\n[2/4] 正在配置系统代理...")
    if original_proxy_enabled:
        print(f"原代理: {original_proxy_server}")

    proxy_configured = enable_proxy(f"127.0.0.1:{PROXY_PORT}")
    if proxy_configured:
        print(f"系统代理已设置: 127.0.0.1:{PROXY_PORT}")
        print("微信流量将经过mitmdump进行捕获")
    else:
        print("系统代理设置失败，请检查权限")
        print("可尝试手动设置代理")

    stop_event = asyncio.Event()

    # Find the capture data file (will be created by mitmdump addon)
    print("等待捕获数据文件...")
    capture_data_file = None
    for _ in range(20):  # Wait up to 10 seconds
        await asyncio.sleep(0.5)
        capture_data_file = find_latest_capture_data_file()
        if capture_data_file:
            print(f"找到数据文件: {capture_data_file}")
            break
    else:
        print("警告: 未找到数据文件，使用默认路径")
        capture_data_file = os.path.join(CAPTURE_LOGS_DIR, "captured_data.json")

    monitor_task = asyncio.create_task(monitor_capture(session_manager, capture_data_file, stop_event))

    print("\n" + "=" * 60)
    print("等待捕获数据...")
    print("在微信中播放视频即可自动捕获")
    print("=" * 60)

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n用户中断捕获")
    except Exception as e:
        print(f"\n发生错误: {e}")
        logger.error(f"Capture error: {e}")
    finally:
        print("\n正在清理...")
        stop_event.set()

        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

        try:
            mitm_process.terminate()
            mitm_process.wait(timeout=5)
        except:
            mitm_process.kill()
            try:
                mitm_process.wait(timeout=3)
            except:
                pass
        logger.info("mitmdump stopped")
        print("mitmdump 已关闭")

        kill_process_on_port(PROXY_PORT)
        print(f"端口 {PROXY_PORT} 已释放")

        if proxy_configured:
            if original_proxy_enabled and original_proxy_server:
                enable_proxy(original_proxy_server)
                print(f"已恢复原代理: {original_proxy_server}")
            else:
                disable_proxy()
                print("代理已禁用")

    print("\n[3/4] 正在处理捕获的视频...")
    ready_videos = session_manager.get_ready_videos()

    if not ready_videos:
        print("\n未捕获到视频。请确保:")
        print(f"  1. 已正确配置代理为 127.0.0.1:{PROXY_PORT}")
        print("  2. 已安装 mitmproxy 证书")
        print("  3. 在微信中播放了视频")
        print("\n安装证书方法:")
        print("  1. 配置代理后，在浏览器访问 http://mitm.it")
        print("  2. 下载 Windows 证书")
        print("  3. 双击安装证书到受信任的根证书颁发机构")
        print("\n捕获日志: capture_logs/ 目录")
        logger.info("No videos captured")
        return

    logger.info(f"Found {len(ready_videos)} video(s) to process")

    for i, video in enumerate(ready_videos, 1):
        print(f"\n{'='*60}")
        print(f"视频 {i}/{len(ready_videos)}: {video['title']}")
        print(f"{'='*60}")

        try:
            title = sanitize_filename(video.get("title", f"video_{int(time.time())}"))
            encrypted_file = os.path.join(TEMP_DIR, f"{title}_encrypted.mp4")
            downloader = VideoDownloader()
            await downloader.download(
                video["url"],
                video.get("cookie", ""),
                encrypted_file
            )
            print(f"下载完成: {encrypted_file}")

            decrypted_file = os.path.join(OUTPUT_DIR, f"{title}_decrypted.mp4")
            decoder = VideoDecoder()
            decoder.decrypt(
                encrypted_file,
                video["decode_key"],
                decrypted_file
            )
            print(f"解密完成: {decrypted_file}")

            if os.path.exists(encrypted_file):
                os.remove(encrypted_file)
                logger.info(f"Cleaned temp file: {encrypted_file}")

        except Exception as e:
            logger.error(f"Failed to process video: {e}")
            print(f"处理失败: {e}")
            continue

    print(f"\n{'='*60}")
    print("全部处理完成！")
    print(f"输出目录: {os.path.abspath(OUTPUT_DIR)}")
    print(f"捕获日志: capture_logs/ 目录")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
