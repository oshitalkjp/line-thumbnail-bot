import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# User provided folder ID
FOLDER_ID = "1HHBZ8dtDRGpsyBjjue_S1uK87b-0-bxi"
SCOPES = ['https://www.googleapis.com/auth/drive']

def upload_to_drive(file_path):
    """
    Uploads a file to the specified Google Drive folder and makes it public.
    Returns the direct view URL.
    """
    try:
        # Get credentials path (set by image_gen.py)
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not creds_path:
            print("Error: GOOGLE_APPLICATION_CREDENTIALS not set")
            return None

        creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [FOLDER_ID]
        }
        media = MediaFileUpload(file_path, mimetype='image/png')
        
        # Upload
        print(f"Uploading {file_metadata['name']} to Drive Folder {FOLDER_ID}...")
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        file_id = file.get('id')
        print(f"Upload successful! File ID: {file_id}")
        
        # Make public (anyone with link can view)
        permission = {
            'type': 'anyone',
            'role': 'reader',
        }
        service.permissions().create(fileId=file_id, body=permission).execute()
        print("File made public.")
        
        # Return direct link suitable for LINE
        link = f"https://drive.google.com/uc?export=view&id={file_id}"
        print(f"Returning link: {link}")
        return link
        
    except Exception as e:
        print(f"Drive Upload Error: {e}")
        import traceback
        traceback.print_exc()
        return None
