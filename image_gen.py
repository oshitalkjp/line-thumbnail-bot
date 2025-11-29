import os
import time
from google import genai
from google.genai import types

# Configuration
IMAGE_MODEL_ID = "imagen-3.0-generate-001"
TEXT_MODEL_ID = "gemini-1.5-pro-002"

_client = None

def get_client():
    global _client
    if _client is None:
        # Handle Google Credentials from JSON string (for Render)
        creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if creds_json:
            import tempfile
            # Create a temp file to store the credentials
            # We use delete=False so it persists for the process life, 
            # but ideally we should clean it up. For this bot, it's fine.
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp:
                temp.write(creds_json)
                temp_path = temp.name
            
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path
            print(f"Loaded credentials to {temp_path}")

        project = os.environ.get("GOOGLE_CLOUD_PROJECT", "youtube-ai-gen")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        _client = genai.Client(
            vertexai=True,
            project=project,
            location=location
        )
    return _client

def generate_thumbnail(user_text: str) -> str:
    """
    Generates a YouTube thumbnail using Gemini 3 Pro Image Preview.
    """
    client = get_client()
    
    # Model ID requested by user
    # Note: This might require an API Key if not available on Vertex AI yet.
    # We try to use it with the existing Vertex AI client.
    MODEL_ID = "gemini-3-pro-image-preview"

    output_dir = os.path.join(os.path.dirname(__file__), "static", "generated")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"thumb_{int(time.time())}.png"
    output_path = os.path.join(output_dir, filename)
    
    try:
        print(f"Sending request to {MODEL_ID} with prompt: {user_text[:50]}...")
        
        # Using generate_content as per user's snippet
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=f"Generate a high quality, 8K, YouTube Thumbnail: {user_text}",
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(
                    aspect_ratio="16:9",
                    image_size="4K" # Or "2048x2048" depending on support, user snippet said 4K
                )
            )
        )
        
        # Extract image from response
        # The snippet uses: image_parts = [part for part in response.parts if part.inline_data]
        # We need to adapt this to the response object structure of google-genai
        
        image_data = None
        if response.parts:
            for part in response.parts:
                if part.inline_data:
                    image_data = part.inline_data.data
                    break
        
        # If not found in parts, check if it's directly in candidates (depending on SDK version)
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
            # Fallback or detailed error logging
            print(f"Response: {response}")
            raise Exception("No image generated")

    except Exception as e:
        print(f"Gemini 3 Generation Error: {e}")
        raise e
