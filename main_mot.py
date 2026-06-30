import os
import io
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2 import service_account
from moviepy import ImageClip, AudioFileClip
import video_mot
import video
import video_animal

from pathlib import Path

def find_missing_videos(image_folder_path, video_folder_path):
    img_dir = Path(image_folder_path)
    vid_dir = Path(video_folder_path)
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.flv'}
    
    video_stems = {
        f.stem for f in vid_dir.iterdir() 
        if f.is_file() and f.suffix.lower() in video_extensions
    }
    
    # Find image file names where the stem is not in the video stems
    missing_videos = [
        f.name for f in img_dir.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions and f.stem not in video_stems
    ]
    
    return missing_videos


# ==========================================
# MODULE 3: Main Orchestration
# ==========================================
def process_media():


    missing_videos = find_missing_videos('temp/images/motivational_vertical', 'temp/videos/motivational')
    print(f"Missing videos for images: {missing_videos}")
    print(f"Total missing videos: {len(missing_videos)}")
    # Process each pending image
    for img in missing_videos:
        base_name = os.path.splitext(img)[0]
        video_name = f"{base_name}.mp4"
        
        print(f"\nProcessing: {img} -> {video_name}")
        
        local_vid_path = os.path.join("temp", "videos","motivational", video_name)
        local_img_path = os.path.join("temp", "images","motivational_vertical", img)

        print(f"Local video path: {local_vid_path} {img}")
        print("Generating video...")
        try:
            video.VG.create_video_from_image(
                image_path=local_img_path,
                output_path=local_vid_path,
                duration=10.0,              # Default duration
                music_path='audio.mp3',          # No music by default
                voice_path='like.mp3',          # No voice by default
                effect='na'         # Default effect
            )
        
        except Exception as e:
            print(f"Error processing {img}: {str(e)}")
            
        finally:
            print("Cleaning up local files...")
            # 4. Clean up local files
            # if os.path.exists(local_img_path):
                # os.remove(local_img_path)
            # if os.path.exists(local_vid_path):
            #     os.remove(local_vid_path)

# ==========================================
# EXECUTION ENTRY POINT
# ==========================================
if __name__ == "__main__":
    
    if not os.path.exists("temp"):
        os.makedirs("temp")
        os.makedirs("temp/images")
        os.makedirs("temp/videos")
        os.makedirs("temp/music")
        
    process_media()