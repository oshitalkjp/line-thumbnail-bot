import os
from google.cloud import storage
import uuid

# Get Project ID from env
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
BUCKET_NAME = f"{PROJECT_ID}-thumbnails" # Unique bucket name

def upload_to_gcs(file_path):
    """
    Uploads a file to Google Cloud Storage and makes it public.
    Returns the public URL.
    """
    try:
        # Initialize client
        # It will automatically use GOOGLE_APPLICATION_CREDENTIALS
        storage_client = storage.Client()
        
        # Get or Create Bucket
        try:
            bucket = storage_client.get_bucket(BUCKET_NAME)
        except:
            print(f"Bucket {BUCKET_NAME} not found. Creating...")
            bucket = storage_client.create_bucket(BUCKET_NAME, location="US") # or ASIA
            
        # Blob Name (Unique)
        blob_name = f"thumbnail_{uuid.uuid4()}.png"
        blob = bucket.blob(blob_name)
        
        print(f"Uploading to GCS Bucket: {BUCKET_NAME}...")
        blob.upload_from_filename(file_path)
        
        # Make Public (Legacy method, or use IAM)
        # For simplicity, we'll try to make the object public reader
        # Note: 'publicRead' might be disabled by 'Uniform Bucket-Level Access'
        # If so, we need to use the public URL format if the bucket allows it.
        
        try:
            blob.make_public()
            url = blob.public_url
        except Exception as e:
            print(f"Could not make blob public via ACL: {e}")
            # Fallback: If Uniform Bucket Level Access is on, we can't use ACLs.
            # We assume the user might need to make the bucket public manually if this fails.
            # Or we can return a signed URL (valid for 1 hour).
            # Signed URL is SAFER and EASIER.
            
            print("Generating Signed URL...")
            url = blob.generate_signed_url(
                version="v4",
                expiration=3600, # 1 hour
                method="GET"
            )
            
        print(f"Upload successful! URL: {url}")
        return url
        
    except Exception as e:
        print(f"GCS Upload Error: {e}")
        import traceback
        traceback.print_exc()
        return None
