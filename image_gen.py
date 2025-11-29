import os
import time
from google import genai
from google.genai import types

# Configuration
IMAGE_MODEL_ID = "imagen-3.0-generate-002"
TEXT_MODEL_ID = "gemini-2.0-flash"

_client = None

def get_client():
    global _client
    if _client is None:
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
    Generates a YouTube thumbnail based on user text.
    Returns the path to the generated image.
    """
    client = get_client()
    
    # 1. Refine Prompt with Gemini
    # We ask Gemini to create a good visual prompt for Imagen
    prompt_refinement_system_instruction = """
    You are an expert YouTube Thumbnail designer.
    Convert the user's request into a highly detailed English prompt for Imagen 3.
    The style should be: "High quality, 8K, YouTube Thumbnail, catchy, vibrant colors".
    
    Output ONLY the English prompt string.
    """
    
    try:
        response = client.models.generate_content(
            model=TEXT_MODEL_ID,
            contents=[prompt_refinement_system_instruction, user_text],
            config=types.GenerateContentConfig(
                temperature=0.7
            )
        )
        english_prompt = response.text.strip()
        print(f"Generated Prompt: {english_prompt}")
    except Exception as e:
        print(f"Gemini Error: {e}")
        # Fallback to user text if Gemini fails
        english_prompt = f"YouTube Thumbnail, {user_text}"

    # 2. Generate Image with Imagen 3
    output_dir = os.path.join(os.path.dirname(__file__), "static", "generated")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"thumb_{int(time.time())}.png"
    output_path = os.path.join(output_dir, filename)
    
    try:
        response = client.models.generate_images(
            model=IMAGE_MODEL_ID,
            prompt=english_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
                person_generation="ALLOW_ADULT"
            )
        )
        
        if response.generated_images:
            img_data = response.generated_images[0].image.image_bytes
            with open(output_path, "wb") as f:
                f.write(img_data)
            return output_path
        else:
            raise Exception("No image generated")
            
    except Exception as e:
        print(f"Imagen Error: {e}")
        raise e
