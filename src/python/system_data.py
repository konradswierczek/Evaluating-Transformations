import platform
import sys
import socket
import os
import multiprocessing
import json
import psutil
import subprocess

def get_system_specs():
    return {
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": socket.gethostname(),
        "cpu_count_logical": os.cpu_count(),
        "cpu_count_physical": multiprocessing.cpu_count(),
    }

def get_memory_specs(meta):
    vm = psutil.virtual_memory()
    meta["ram_total_gb"] = round(vm.total / (1024**3), 2)
    return meta

def get_git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return None

def get_all_system_data():
    meta = get_system_specs()
    meta = get_memory_specs(meta)
    meta["git_commit"] = get_git_commit()
    return meta
