import requests
import os

IMGUR_CLIENT_ID = "e83896561117277" # Public anonymous client ID or use env var

import time

def upload_to_imgur(image_path):
    """
    Uploads an image to Imgur and returns the link.
    Retries up to 3 times on failure.
    """
    url = "https://api.imgur.com/3/image"
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
    
    with open(image_path, "rb") as file:
        payload = {"image": file.read()}
        
    for attempt in range(3):
        try:
            response = requests.post(url, headers=headers, files=payload)
            if response.status_code == 200:
                return response.json()["data"]["link"]
            else:
                print(f"Imgur Upload Error (Attempt {attempt+1}): {response.text}")
        except Exception as e:
            print(f"Imgur Connection Error (Attempt {attempt+1}): {e}")
        
        time.sleep(2) # Wait 2 seconds before retrying
        
    return None
