import os
import io
import pickle # <-- NEW
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow # <-- NEW
from google.auth.transport.requests import Request # <-- NEW

# ==========================================
# MODULE 1: Google Drive Operations (OAuth 2.0)
# ==========================================
class DriveManager:
    def __init__(self, credentials_file='credentials.json'):
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.creds = None
        
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
                
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, self.scopes)
                # This will open a browser window for you to log in
                self.creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('drive', 'v3', credentials=self.creds)

    def list_files(self, folder_id):
        """Fetches all files in a specific Google Drive folder."""
        files = []
        page_token = None
        while True:
            response = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType)',
                pageToken=page_token
            ).execute()
            
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return files

    def download_file(self, file_id, file_name, download_dir="temp/images"):
        """Downloads a file from Google Drive to a local directory."""
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        file_path = os.path.join(download_dir, file_name)
        request = self.service.files().get_media(fileId=file_id)
        
        with io.FileIO(file_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        return file_path

    def upload_video(self, local_file_path, target_folder_id, file_name):
        """Uploads a local video to a specific Google Drive folder."""
        file_metadata = {
            'name': file_name,
            'parents': [target_folder_id]
        }
        media = MediaFileUpload(local_file_path, mimetype='video/mp4', resumable=True)
        
        uploaded_file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        return uploaded_file.get('id')