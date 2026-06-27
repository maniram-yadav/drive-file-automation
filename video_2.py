import os
import math
from typing import Callable
import numpy as np
from PIL import Image, ImageOps

# Core imports straight from moviepy v2.0+
from moviepy import ImageClip, AudioFileClip

# Safely handle older Pillow versions that do not have ImageResampling
try:
    from PIL import ImageResampling
    RESAMPLE_METHOD = ImageResampling.LANCZOS
except ImportError:
    RESAMPLE_METHOD = Image.LANCZOS


class VG:
    @staticmethod
    def create_video_from_image(
        image_path: str, 
        output_path: str, 
        duration: float = 5.0, 
        ratio: tuple = (9, 16), 
        music_path: str = 'audio.mp3', 
        effect: str = 'zoom'
    ) -> str:
        """Generates an mp4 video from an image, forcing a strict ratio and zoom effect."""
        
        # 1. Pre-process the image to be exactly 9:16 before video generation
        img = Image.open(image_path)
        orig_w, orig_h = img.size
        target_aspect = ratio[0] / ratio[1]  # 9/16 = 0.5625
        
        # Calculate maximum crop dimensions without stretching or losing quality
        if orig_w / orig_h > target_aspect:
            # Image is too wide, we crop the sides
            crop_w = int(orig_h * target_aspect)
            crop_h = orig_h
        else:
            # Image is too tall, we crop the top and bottom
            crop_w = orig_w
            crop_h = int(orig_w / target_aspect)
            
        # ImageOps.fit automatically does a perfect center-crop to our new dimensions
        formatted_img = ImageOps.fit(img, (crop_w, crop_h), method=RESAMPLE_METHOD)
        
        # Convert our perfectly formatted 9:16 PIL image into a NumPy array for MoviePy
        base_frame = np.array(formatted_img)
        
        # 2. Load the pre-formatted frame into MoviePy
        clip = ImageClip(base_frame).with_duration(duration)
        
        # 3. Apply strict centered Zoom effect
        if effect == 'zoom':
            
            def apply_pure_zoom(get_frame: Callable[[float], np.ndarray], t: float) -> np.ndarray:
                """Resizes the frame progressively and crops from the dead center."""
                current_img = Image.fromarray(get_frame(t))
                base_w, base_h = current_img.size
                
                # Calculate zoom scale factor 
                # Reduced to 0.05 (5%) for a very slow, smooth zoom
                zoom_factor = 1 + 0.10 * (t / duration)
                
                # Find new larger pixel dimensions
                new_w = math.ceil(base_w * zoom_factor)
                new_h = math.ceil(base_h * zoom_factor)
                
                # Force dimensions to stay even numbers to prevent compression errors
                new_w += new_w % 2
                new_h += new_h % 2
                
                # Resize the source canvas smoothly using the safe filter method
                current_img = current_img.resize((new_w, new_h), RESAMPLE_METHOD)
                
                # Crop exactly from the center to eliminate camera shifting
                crop_x = (new_w - base_w) // 2
                crop_y = (new_h - base_h) // 2
                
                current_img = current_img.crop((crop_x, crop_y, crop_x + base_w, crop_y + base_h))
                return np.array(current_img)

            # Bind transformation to the clip
            clip = clip.transform(apply_pure_zoom)

        # 4. Add Audio if provided
        if music_path and os.path.exists(music_path):
            audio = AudioFileClip(music_path).with_duration(duration)
            clip = clip.with_audio(audio)
            
        # 5. Write to local disk
        clip.write_videofile(
            output_path, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac" if music_path else None,
            logger='bar' 
        )
        
        # 6. Close clips to free memory
        clip.close()
        if music_path: 
            audio.close()
        img.close() # Free the original PIL image
        
        return output_path


# ==========================================
# Example Usage:
# ==========================================
if __name__ == "__main__":
    MY_IMAGE = "input_photo.jpg"
    MY_AUDIO = "background_music.mp3"
    OUTPUT_VIDEO = "final_output.mp4"
    
    if os.path.exists(MY_IMAGE):
        print("Starting 9:16 slow-zoom video generation...")
        VG.create_video_from_image(
            image_path=MY_IMAGE,
            output_path=OUTPUT_VIDEO,
            duration=7.0,          
            ratio=(9, 16),         # Ratio is explicitly passed here
            music_path=MY_AUDIO if os.path.exists(MY_AUDIO) else None,
            effect='zoom'
        )
        print(f"Success! Video saved to {OUTPUT_VIDEO}")
    else:
        print(f"Please put a valid image at '{MY_IMAGE}' to test the script.")