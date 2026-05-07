import os
import sys
import time
import uuid
import json
import socket
import getpass
import hashlib
import platform
from datetime import datetime

import psutil
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


# =========================
# CONFIG
# =========================

OUTPUT_FILE = "system_report.json"
ENCRYPTED_FILE = "system_report.enc"
LOG_FILE = "log.txt"

EMAIL = "You need to enter your email here"
APP_PASSWORD = "here is a special password"


# =========================
# LOGGER
# =========================

def write_log(text):

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as log:

            log.write(
                f"[{datetime.now()}] {text}\n"
            )

    except:
        pass


# =========================
# SYSTEM INFO
# =========================

def get_system_info():

    try:
        ip = socket.gethostbyname(socket.gethostname())
    except:
        ip = "unknown"

    try:
        mac = ':'.join([
            f'{(uuid.getnode() >> e) & 0xff:02x}'
            for e in range(0, 48, 8)
        ][::-1])
    except:
        mac = "unknown"

    return {
        "time": datetime.now().isoformat(),
        "user": getpass.getuser(),
        "hostname": socket.gethostname(),
        "ip": ip,
        "mac": mac,
        "os": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.architecture()[0]
    }


# =========================
# DEVICE INFO
# =========================

def get_device_info():

    return {
        "machine": platform.machine(),
        "processor": platform.processor(),
        "node": platform.node(),
        "platform": platform.platform(),
        "python_version": sys.version,
        "python_executable": sys.executable
    }


# =========================
# PERFORMANCE
# =========================

def get_performance():

    try:
        ram = psutil.virtual_memory().percent
    except:
        ram = "no access"

    try:
        cpu = psutil.cpu_percent(interval=0.5)
    except:
        cpu = "no access"

    return {
        "cpu_percent": cpu,
        "ram_percent": ram
    }


# =========================
# CPU INFO
# =========================

def get_cpu_info():

    try:
        physical = psutil.cpu_count(logical=False)
    except:
        physical = "unknown"

    try:
        logical = psutil.cpu_count(logical=True)
    except:
        logical = "unknown"

    return {
        "physical_cores": physical,
        "logical_cores": logical
    }


# =========================
# BATTERY
# =========================

def get_battery():

    try:
        battery = psutil.sensors_battery()

        if battery:
            return {
                "percent": battery.percent,
                "plugged": battery.power_plugged
            }

        return {
            "battery": "not available"
        }

    except:
        return {
            "battery": "no access"
        }


# =========================
# NETWORK
# =========================

def get_network():

    try:
        interfaces = list(psutil.net_if_addrs().keys())
    except:
        interfaces = []

    try:
        connections = len(psutil.net_connections())
    except:
        connections = "no access"

    return {
        "interfaces": interfaces,
        "connections": connections
    }


# =========================
# INTERNET CHECK
# =========================

def internet_check():

    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)

        return {
            "internet": True
        }

    except:

        return {
            "internet": False
        }


# =========================
# SITE CHECK
# =========================

def check_sites():

    sites = [
        "google.com",
        "youtube.com",
        "github.com"
    ]

    results = {}

    for site in sites:

        try:
            socket.gethostbyname(site)
            results[site] = "online"

        except:
            results[site] = "offline"

    return results


# =========================
# UPTIME
# =========================

def get_uptime():

    try:
        uptime = time.time() - psutil.boot_time()

        return {
            "uptime_seconds": round(uptime, 2),
            "uptime_hours": round(uptime / 3600, 2)
        }

    except:
        return {
            "uptime": "no access"
        }


# =========================
# PROCESSES
# =========================

def get_processes():

    data = []

    try:
        for process in psutil.process_iter(['pid', 'name']):

            try:
                data.append(process.info)

            except:
                continue

    except:
        pass

    return data


# =========================
# DRIVES
# =========================

def get_drives():

    data = []

    try:
        for part in psutil.disk_partitions():

            try:
                usage = psutil.disk_usage(part.mountpoint)

                data.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "used_gb": round(usage.used / (1024 ** 3), 2),
                    "free_gb": round(usage.free / (1024 ** 3), 2),
                    "percent": usage.percent
                })

            except:
                continue

    except:
        pass

    return data


# =========================
# STORAGE SUMMARY
# =========================

def get_storage_summary():

    try:
        usage = psutil.disk_usage("/")

        return {
            "total_gb": round(
                usage.total / (1024 ** 3), 2
            ),

            "used_gb": round(
                usage.used / (1024 ** 3), 2
            ),

            "free_gb": round(
                usage.free / (1024 ** 3), 2
            )
        }

    except:
        return {
            "storage": "no access"
        }


# =========================
# FOLDER SIZE
# =========================

def folder_size(path):

    total = 0

    try:
        for root, dirs, files in os.walk(path):

            for file in files:

                try:
                    file_path = os.path.join(root, file)
                    total += os.path.getsize(file_path)

                except:
                    pass

        return round(total / (1024 * 1024), 2)

    except:
        return 0


# =========================
# LARGE FILES
# =========================

def get_large_files(path, limit=5):

    files_data = []

    try:
        for root, dirs, files in os.walk(path):

            for file in files:

                try:
                    file_path = os.path.join(root, file)

                    size = os.path.getsize(file_path)

                    files_data.append({
                        "file": file_path,
                        "size_mb": round(
                            size / (1024 * 1024), 2
                        )
                    })

                except:
                    continue

        files_data.sort(
            key=lambda x: x["size_mb"],
            reverse=True
        )

        return files_data[:limit]

    except:
        return []


# =========================
# SAVE JSON
# =========================

def save_json(data):

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


# =========================
# ENCRYPT
# =========================

def encrypt(data):

    key = hashlib.sha256(
        b"key"
    ).digest()

    encrypted = bytes([
        b ^ key[i % len(key)]
        for i, b in enumerate(data)
    ])

    return encrypted


# =========================
# EMAIL
# =========================

def send_email(file_path):

    msg = MIMEMultipart()

    msg["From"] = EMAIL
    msg["To"] = EMAIL
    msg["Subject"] = "System Report"

    with open(file_path, "rb") as file:

        part = MIMEBase(
            "application",
            "octet-stream"
        )

        part.set_payload(file.read())

    encoders.encode_base64(part)

    part.add_header(
        "Content-Disposition",
        f"attachment; filename={file_path}"
    )

    msg.attach(part)

    server = smtplib.SMTP(
        "smtp.gmail.com",
        587
    )

    server.starttls()

    server.login(
        EMAIL,
        APP_PASSWORD
    )

    server.send_message(msg)

    server.quit()


# =========================
# MAIN
# =========================

def main():

    write_log("Program started")

    data = {

        "system": get_system_info(),

        "device_info": get_device_info(),

        "performance": get_performance(),

        "cpu_info": get_cpu_info(),

        "battery": get_battery(),

        "network": get_network(),

        "internet": internet_check(),

        "site_status": check_sites(),

        "uptime": get_uptime(),

        "processes": get_processes(),

        "drives": get_drives(),

        "storage_summary": get_storage_summary(),

        "downloads_size_mb": folder_size(
            "/storage/emulated/0/Download"
        ),

        "dcim_size_mb": folder_size(
            "/storage/emulated/0/DCIM"
        ),

        "large_files": get_large_files(
            "/storage/emulated/0/Download"
        )
    }

    write_log("Data collected")

    # SAVE JSON
    save_json(data)

    write_log("JSON saved")

    # ENCRYPTED COPY
    encrypted = encrypt(
        json.dumps(data).encode("utf-8")
    )

    with open(
        ENCRYPTED_FILE,
        "wb"
    ) as file:

        file.write(encrypted)

    write_log("Encrypted file saved")

    print("OK: files created")

    # SEND EMAIL
    send_email(OUTPUT_FILE)

    send_email(ENCRYPTED_FILE)

    write_log("Email sent")

    print("OK: email sent")


# =========================
# START
# =========================

if __name__ == "__main__":

    main()