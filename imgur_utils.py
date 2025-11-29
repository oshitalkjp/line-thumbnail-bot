import requests
import os

IMGUR_CLIENT_ID = "e83896561117277" # Public anonymous client ID or use env var

import time

def upload_to_imgur(image_path):
    """
    Uploads an image to file.io (ephemeral storage) and returns the link.
    Retries up to 3 times on failure.
    """
    url = "https://file.io"
    
    with open(image_path, "rb") as file:
        payload = {"file": file}
        
        for attempt in range(3):
            try:
                # file.io expires after 1 download by default, but we can set it to 1 day or more downloads
                # expires: 1d
                response = requests.post(url, files=payload, data={"expires": "1d"})
                
                if response.status_code == 200:
                    return response.json()["link"]
                else:
                    print(f"Upload Error (Attempt {attempt+1}): {response.text}")
            except Exception as e:
                print(f"Connection Error (Attempt {attempt+1}): {e}")
            
            time.sleep(2)
            # Re-open file for retry if needed (pointer might be at end)
            file.seek(0)
            
    return None
