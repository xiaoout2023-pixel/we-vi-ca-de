import subprocess
import sys
import os
import winreg
import socket
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("微信视频捕获诊断工具")
print("=" * 60)
print()

project_root = Path(__file__).parent
log_file = project_root / "wechat_video.log"
data_file = project_root / "captured_data.json"

# 1. Check mitmdump process
print("1. 检查mitmdump进程:")
result = subprocess.run(["tasklist"], capture_output=True, text=True)
mitmdump_running = False
for line in result.stdout.splitlines():
    if "mitmdump" in line.lower() or "python" in line.lower():
        print(f"   找到: {line.strip()}")
        if "mitmdump" in line.lower():
            mitmdump_running = True

if not mitmdump_running:
    print("   ❌ 未发现mitmdump进程")
    print("   → 请先运行 python run.bat 启动服务")
else:
    print("   ✓ mitmdump正在运行")

print()

# 2. Check port 8080
print("2. 检查端口8080:")
try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        result = s.connect_ex(('127.0.0.1', 8080))
        if result == 0:
            print("   ✓ 端口8080正在监听")
        else:
            print("   ❌ 端口8080未被监听")
            print("   → mitmdump可能未启动或已退出")
except Exception as e:
    print(f"   ❌ 检查端口失败: {e}")

print()

# 3. Check proxy settings
print("3. 检查系统代理:")
try:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                        r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                        0, winreg.KEY_READ)
    enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
    server, _ = winreg.QueryValueEx(key, "ProxyServer")
    winreg.CloseKey(key)
    
    if enabled:
        print(f"   ✓ 代理已启用: {server}")
        if "127.0.0.1:8080" in server or "localhost:8080" in server:
            print("   → 代理指向本工具")
        else:
            print(f"   ⚠ 代理指向其他服务器: {server}")
    else:
        print("   ❌ 代理未启用")
        print("   → 微信视频流量不会经过mitmdump")
        print("   → 这就是为什么没有捕获到视频！")
except Exception as e:
    print(f"   ❌ 读取代理设置失败: {e}")

print()

# 4. Check log file
print("4. 检查日志文件:")
if log_file.exists():
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"   日志文件: {log_file}")
    print(f"   行数: {len(lines)}")
    
    # Check for capture activity
    has_capture = False
    for line in lines:
        if '捕获' in line or 'video' in line.lower() or 'URL' in line:
            has_capture = True
            print(f"   [捕获日志] {line.strip()}")
    
    if not has_capture:
        print("   ❌ 未发现任何捕获活动")
        print("   → 可能原因:")
        print("     1. 代理未配置（见上方检查）")
        print("     2. 微信内置播放器不走系统代理")
        print("     3. mitmdump未正确加载addon")
    
    # Show last 5 lines
    print("\n   最后5条日志:")
    for line in lines[-5:]:
        print(f"     {line.strip()}")
else:
    print(f"   ❌ 日志文件不存在: {log_file}")

print()

# 5. Check captured_data.json
print("5. 检查捕获数据文件:")
if data_file.exists():
    print(f"   ✓ 数据文件存在: {data_file}")
    with open(data_file, 'r', encoding='utf-8') as f:
        import json
        data = json.load(f)
        captured = data.get("captured_data", [])
        print(f"   捕获记录数: {len(captured)}")
        if captured:
            for item in captured:
                print(f"   - {item.get('type')}: {item.get('data', {}).get('url', 'N/A')[:80]}")
        else:
            print("   ❌ 无捕获记录")
else:
    print(f"   ❌ 数据文件不存在: {data_file}")
    print("   → 这证明没有视频被捕获")

print()

# 6. Check addon file
print("6. 检查addon文件:")
addon_path = project_root / "src" / "capture" / "mitm_addon.py"
if addon_path.exists():
    print(f"   ✓ Addon文件存在: {addon_path}")
    with open(addon_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if "VideoCaptureAddon" in content:
            print("   ✓ 包含VideoCaptureAddon类")
        if "finder.video.qq.com" in content:
            print("   ✓ 包含视频域名检测")
        if "addons = " in content:
            print("   ✓ 包含addons注册")
else:
    print(f"   ❌ Addon文件不存在: {addon_path}")

print()

# 7. Diagnosis summary
print("=" * 60)
print("诊断总结:")
print("=" * 60)

if not mitmdump_running:
    print("\n❌ 问题: mitmdump未运行")
    print("   解决: 运行 'python run.bat' 启动服务")

try:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                        r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                        0, winreg.KEY_READ)
    enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
    winreg.CloseKey(key)
    
    if not enabled:
        print("\n❌ 问题: 系统代理未启用")
        print("   这是没有捕获到视频的主要原因！")
        print("   解决:")
        print("   1. 打开 Windows 设置 → 网络和 Internet → 代理")
        print("   2. 开启手动代理")
        print("   3. 地址: 127.0.0.1  端口: 8080")
        print("   4. 保存后重新播放微信视频")
except:
    pass

print("\n⚠️ 重要提示:")
print("   微信内置播放器可能不使用系统代理")
print("   如果是这样，即使配置了代理也无法捕获视频")
print("   需要考虑其他方案（如进程级代理注入）")

print()
print("=" * 60)
print("诊断完成")
print("=" * 60)
