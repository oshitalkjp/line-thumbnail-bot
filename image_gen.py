import os
import time
from google import genai
from google.genai import types

# Configuration
# Configuration
# User strictly requested this model via AI Studio API
IMAGE_MODEL_ID = "gemini-3-pro-image-preview"

_client = None

def get_client():
    global _client
    if _client is None:
        # Use AI Studio API Key
        api_key = os.environ.get("GOOGLE_API")
        if not api_key:
            print("Warning: GOOGLE_API environment variable not set.")
        
        _client = genai.Client(api_key=api_key)
    return _client

def generate_thumbnail(user_text: str) -> str:
    """
    Generates a YouTube thumbnail using Gemini 3 Pro Image Preview via AI Studio.
    """
    client = get_client()
    
    output_dir = os.path.join(os.path.dirname(__file__), "static", "generated")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"thumb_{int(time.time())}.png"
    output_path = os.path.join(output_dir, filename)
    
    try:
        # User requested Japanese prompt and strict usage of this model
        prompt = f"高品質なYouTubeサムネイル, 8K, 鮮やかな色: {user_text}"
        print(f"Sending request to {IMAGE_MODEL_ID} with prompt: {prompt[:50]}...")
        
        response = client.models.generate_content(
            model=IMAGE_MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(
                    aspect_ratio="16:9",
                    image_size="4K"
                )
            )
        )
        
        # Extract image from response
        image_data = None
        if response.parts:
            for part in response.parts:
                if part.inline_data:
                    image_data = part.inline_data.data
                    break
        
        if not image_data and response.candidates:
             for part in response.candidates[0].content.parts:
                 if part.inline_data:
                     image_data = part.inline_data.data
                     break

        if image_data:
            print(f"Image generated! Size: {len(image_data)} bytes")
            with open(output_path, "wb") as f:
                f.write(image_data)
            print(f"Image saved locally to: {output_path}")
            return output_path
        else:
            print("Gemini returned no inline image data.")
            print(f"Response: {response}")
            raise Exception("No image generated")

    except Exception as e:
        print(f"Gemini 3 Generation Error: {e}")
        raise e
