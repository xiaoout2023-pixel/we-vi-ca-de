import subprocess
import sys
import time
import os
import signal
from pathlib import Path

project_root = Path(__file__).parent
addon_path = str(project_root / "src" / "capture" / "mitm_addon.py")

print("=" * 60)
print("Test 1: Check if mitmdump can load addon")
print("=" * 60)

cmd = [
    sys.executable, "-c",
    "from mitmproxy.tools.main import mitmdump; mitmdump()",
    "--listen-port", "8085",
    "--set", "flow_detail=0",
    "--set", "connection_strategy=lazy",
    "--set", "ssl_insecure=true",
    "-s", addon_path,
]

env = os.environ.copy()
env["PYTHONUNBUFFERED"] = "1"
env["PYTHONPATH"] = str(project_root)

print(f"Command: {' '.join(cmd)}")
print(f"PYTHONPATH: {env.get('PYTHONPATH')}")
print()

# Start mitmdump and let it output to console
print("Starting mitmdump...")
try:
    proc = subprocess.Popen(
        cmd,
        env=env,
        cwd=str(project_root)
    )
    
    print(f"PID: {proc.pid}")
    print("Waiting 5 seconds...")
    
    for i in range(5):
        time.sleep(1)
        rc = proc.poll()
        if rc is not None:
            print(f"mitmdump exited after {i+1}s with code {rc}")
            break
        print(f"  Still running... ({i+1}s)")
    else:
        print("mitmdump is still running after 5s")
        print("Terminating...")
        proc.terminate()
        proc.wait(timeout=3)
        print("Done")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("Test 2: Check addon file can be imported")
print("=" * 60)

# Test direct import
sys.path.insert(0, str(project_root))
try:
    exec(open(addon_path).read(), {"__file__": addon_path})
    print("Addon imported successfully")
except Exception as e:
    print(f"Addon import failed: {e}")
    import traceback
    traceback.print_exc()
