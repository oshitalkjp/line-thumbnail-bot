import requests
import os

IMGUR_CLIENT_ID = "e83896561117277" # Public anonymous client ID or use env var

import time

def upload_to_imgur(image_path):
    """
    Uploads an image to tmpfiles.org (ephemeral storage) and returns the link.
    Retries up to 3 times on failure.
    """
    url = "https://tmpfiles.org/api/v1/upload"
    
    with open(image_path, "rb") as file:
        payload = {"file": file}
        
        for attempt in range(3):
            try:
                response = requests.post(url, files=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    # tmpfiles returns a URL like https://tmpfiles.org/12345/image.png
                    # But to view it directly (raw), we need to change the domain to https://tmpfiles.org/dl/12345/image.png
                    # Actually, the 'url' field is the view page. The raw download link is slightly different.
                    # Let's check the response structure. Usually data['data']['url'].
                    # For direct image display in LINE, we need the direct link.
                    # tmpfiles.org direct link format: replace "tmpfiles.org/" with "tmpfiles.org/dl/"
                    
                    original_url = data["data"]["url"]
                    direct_url = original_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                    return direct_url
                else:
                    print(f"Upload Error (Attempt {attempt+1}): {response.text}")
            except Exception as e:
                print(f"Connection Error (Attempt {attempt+1}): {e}")
            
            time.sleep(2)
            file.seek(0)
            
    return None
