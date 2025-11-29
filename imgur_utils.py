import requests
import os

IMGUR_CLIENT_ID = "e83896561117277" # Public anonymous client ID or use env var

def upload_to_imgur(image_path):
    """
    Uploads an image to Imgur and returns the link.
    """
    url = "https://api.imgur.com/3/image"
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
    
    with open(image_path, "rb") as file:
        payload = {"image": file.read()}
        
    response = requests.post(url, headers=headers, files=payload)
    if response.status_code == 200:
        return response.json()["data"]["link"]
    else:
        print(f"Imgur Upload Error: {response.text}")
        return None
