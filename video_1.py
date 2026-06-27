import os
import math
from typing import Callable
import numpy as np
from PIL import Image

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
        """Generates an mp4 video from an image with a strict centered zoom effect."""
        
        # Load the image and set duration using the new 'with_duration' method
        clip = ImageClip(image_path).with_duration(duration)
        
        # Apply strict centered Zoom effect
        if effect == 'zoom':
            
            def apply_pure_zoom(get_frame: Callable[[float], np.ndarray], t: float) -> np.ndarray:
                """Resizes the frame progressively and crops from the dead center."""
                img = Image.fromarray(get_frame(t))
                base_w, base_h = img.size
                
                # Calculate zoom scale factor (starts at 1.0, scales to 1.10 over the duration)
                zoom_factor = 1 + 0.10 * (t / duration)
                
                # Find new larger pixel dimensions
                new_w = math.ceil(base_w * zoom_factor)
                new_h = math.ceil(base_h * zoom_factor)
                
                # Force dimensions to stay even numbers to prevent compression errors
                new_w += new_w % 2
                new_h += new_h % 2
                
                # Resize the source canvas smoothly using the safe filter method
                img = img.resize((new_w, new_h), RESAMPLE_METHOD)
                
                # Crop exactly from the center to eliminate camera shifting
                crop_x = (new_w - base_w) // 2
                crop_y = (new_h - base_h) // 2
                
                img = img.crop((crop_x, crop_y, crop_x + base_w, crop_y + base_h))
                return np.array(img)

            # Bind transformation to the clip
            clip = clip.transform(apply_pure_zoom)

        # Add Audio if provided
        if music_path and os.path.exists(music_path):
            audio = AudioFileClip(music_path).with_duration(duration)
            clip = clip.with_audio(audio)
            
        # Write to local disk
        clip.write_videofile(
            output_path, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac" if music_path else None,
            logger='bar' # Set to None if you want to hide progress in terminal
        )
        
        # Close clips to free memory
        clip.close()
        if music_path: 
            audio.close()
        
        return output_path


# ==========================================
# Example Usage:
# ==========================================
if __name__ == "__main__":
    # Replace these with your actual local file paths to test the code
    MY_IMAGE = "input_photo.jpg"
    MY_AUDIO = "background_music.mp3"
    OUTPUT_VIDEO = "final_output.mp4"
    
    # Make sure you have a test image ready before running this
    if os.path.exists(MY_IMAGE):
        print("Starting video generation...")
        VG.create_video_from_image(
            image_path=MY_IMAGE,
            output_path=OUTPUT_VIDEO,
            duration=7.0,          # Video length in seconds
            music_path=MY_AUDIO if os.path.exists(MY_AUDIO) else None,
            effect='zoom'
        )
        print(f"Success! Video saved to {OUTPUT_VIDEO}")
    else:
        print(f"Please put a valid image at '{MY_IMAGE}' to test the script.")
