import winreg
import ctypes
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SystemProxyController:
    def __init__(self):
        self.registry_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        self.original_proxy = None

    def enable_proxy(self, proxy="127.0.0.1:8080"):
        logger.info(f"Enabling system proxy: {proxy}")
        self.original_proxy = self._get_current_proxy()
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.registry_path,
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy)
            winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "<local>")
            winreg.CloseKey(key)
            self._notify_proxy_change()
            logger.info("System proxy enabled")
        except Exception as e:
            logger.error(f"Failed to enable proxy: {e}")
            raise

    def disable_proxy(self):
        logger.info("Disabling system proxy")
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.registry_path,
                0,
                winreg.KEY_SET_VALUE
            )
            if self.original_proxy and self.original_proxy.get("enabled"):
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, self.original_proxy["server"])
            else:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            self._notify_proxy_change()
            logger.info("System proxy disabled/restored")
        except Exception as e:
            logger.error(f"Failed to disable proxy: {e}")

    def _get_current_proxy(self):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.registry_path,
                0,
                winreg.KEY_READ
            )
            enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
            server, _ = winreg.QueryValueEx(key, "ProxyServer")
            winreg.CloseKey(key)
            return {"enabled": bool(enabled), "server": server}
        except:
            return None

    def _notify_proxy_change(self):
        try:
            ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
            ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
        except Exception as e:
            logger.warning(f"Failed to notify proxy change: {e}")
