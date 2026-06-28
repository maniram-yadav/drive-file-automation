

import os
import io
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2 import service_account
from moviepy import ImageClip, AudioFileClip
  # Import the VG class from video.py
import video_animal
import gdrive
# ==========================================
# MODULE 1: Google Drive Operations
# ==========================================
class DriveManager:
    def __init__(self, service_account_file):
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=self.scopes)
        self.service = build('drive', 'v3', credentials=self.credentials)

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
            # print(f"Fetched response {response}.")
            print(f"Fetched {len(response.get('files', []))} files from folder {folder_id}.")
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return files

    def download_file(self, file_id, file_name, download_dir="temp"):
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


# ==========================================
# MODULE 3: Main Orchestration
# ==========================================
def process_media(service_account_file, image_folder_id, video_folder_id):
    # drive = drive.DriveManager(service_account_file)
    drive = gdrive.DriveManager()
    
    print("Fetching file lists from Drive...")
    images_in_drive = drive.list_files(image_folder_id)
    videos_in_drive = drive.list_files(video_folder_id)
    print(f"Found {len(images_in_drive)} images and {len(videos_in_drive)} videos in Drive.")
    print("Identifying pending videos to generate...")

    # Create a set of existing video names (exact match, without extensions)
    existing_video_names = {os.path.splitext(vid['name'])[0] for vid in videos_in_drive}
    
    # Filter images that do not have a matching video
    pending_images = []
    for img in images_in_drive:
        if img['mimeType'].startswith('image/'):
            img_name_no_ext = os.path.splitext(img['name'])[0]
            if img_name_no_ext not in existing_video_names:
                pending_images.append(img)
            
    print(f"Found {len(images_in_drive)} images and {len(videos_in_drive)} videos.")
    print(f"Pending videos to generate: {len(pending_images)}")

    # Process each pending image
    for img in pending_images:
        base_name = os.path.splitext(img['name'])[0]
        video_name = f"{base_name}.mp4"
        
        print(f"\nProcessing: {img['name']} -> {video_name}")
        
        # 1. Download Image
        local_img_path = drive.download_file(img['id'], img['name'])
        local_vid_path = os.path.join("temp", "videos", video_name)
        
        # 2. Generate Video
        print("Generating video...")
        try:
            video_animal.VG.create_video_from_image(
                image_path=local_img_path,
                output_path=local_vid_path,
                duration=5.0,              # Default duration
                music_path='audio.mp3',          # No music by default
                voice_path='like.mp3',          # No voice by default
                effect='zoom_out'         # Default effect
            )
        
            # 3. Upload Video
            
            # print("Uploading to Drive...")
            # drive.upload_video(local_vid_path, video_folder_id, video_name)
            # print(f"Success! {video_name} uploaded.")
            
        except Exception as e:
            print(f"Error processing {img['name']}: {str(e)}")
            
        finally:
            print("Cleaning up local files...")
            # 4. Clean up local files
            if os.path.exists(local_img_path):
                os.remove(local_img_path)
            # if os.path.exists(local_vid_path):
            #     os.remove(local_vid_path)

# ==========================================
# EXECUTION ENTRY POINT
# ==========================================
if __name__ == "__main__":
    # Configure your settings here
    SERVICE_ACCOUNT_JSON = 'service-account.json'
    IMAGE_DRIVE_FOLDER_ID = '1030W_wT8XziX0oxm9My2H_HTBxOsUw5k'
    VIDEO_DRIVE_FOLDER_ID = '1NqXAFmY3SkhYfGQRngWDmz4GCLXTpbNP'
    
    # Ensure a local temp directory exists
    if not os.path.exists("temp"):
        os.makedirs("temp")
        os.makedirs("temp/images")
        os.makedirs("temp/videos")
        os.makedirs("temp/music")
        
    process_media(
        service_account_file=SERVICE_ACCOUNT_JSON,
        image_folder_id=IMAGE_DRIVE_FOLDER_ID,
        video_folder_id=VIDEO_DRIVE_FOLDER_ID
    )