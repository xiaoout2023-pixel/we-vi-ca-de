import winreg
import ctypes
import socket
import subprocess
import re
from src.utils.logger import get_logger

logger = get_logger(__name__)

REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"


def is_proxy_enabled():
    """检查系统代理是否已启用"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH, 0, winreg.KEY_READ)
        enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
        winreg.CloseKey(key)
        return bool(enabled)
    except Exception:
        return False


def get_proxy_server():
    """获取当前代理服务器地址"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH, 0, winreg.KEY_READ)
        server, _ = winreg.QueryValueEx(key, "ProxyServer")
        winreg.CloseKey(key)
        return server
    except Exception:
        return None


def enable_proxy(proxy="127.0.0.1:8080"):
    """启用系统代理"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy)
        winreg.CloseKey(key)
        _notify_proxy_change()
        logger.info(f"Proxy enabled: {proxy}")
        return True
    except Exception as e:
        logger.error(f"Failed to enable proxy: {e}")
        return False


def disable_proxy():
    """禁用系统代理"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        _notify_proxy_change()
        logger.info("Proxy disabled")
        return True
    except Exception as e:
        logger.error(f"Failed to disable proxy: {e}")
        return False


def _notify_proxy_change():
    """通知 Windows 代理设置已更改"""
    try:
        ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
        ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
    except Exception as e:
        logger.warning(f"Failed to notify proxy change: {e}")


def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def kill_process_on_port(port):
    """关闭占用指定端口的进程"""
    killed = []
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                pid = parts[-1]
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/PID", pid],
                        capture_output=True, timeout=5
                    )
                    killed.append(pid)
                    logger.info(f"Killed process {pid} on port {port}")
                except Exception as e:
                    logger.error(f"Failed to kill process {pid}: {e}")
    except Exception as e:
        logger.error(f"Failed to check port {port}: {e}")
    return killed
