import os
import math
from typing import Callable, Dict
import numpy as np
from PIL import Image, ImageOps

# MoviePy v2.0+ Imports
from moviepy import CompositeVideoClip, ImageClip, AudioFileClip, CompositeAudioClip,VideoFileClip
from moviepy.audio.fx.AudioLoop import AudioLoop
from moviepy.audio.fx.MultiplyVolume import MultiplyVolume
import video
try:
    from PIL import ImageResampling
    RESAMPLE_METHOD = ImageResampling.LANCZOS
except ImportError:
    RESAMPLE_METHOD = Image.LANCZOS


# ==========================================
# MODULE: Visual Effects Library
# ==========================================
class VideoEffects:
    """A collection of pure transformation effects compatible with MoviePy v2.0 transform standard."""

    @staticmethod
    def zoom_in(get_frame: Callable[[float], np.ndarray], t: float, duration: float) -> np.ndarray:
        """Progressively zooms INTO the center of the image (starts at 100%, ends at 110%)."""
        current_img = Image.fromarray(get_frame(t))
        base_w, base_h = current_img.size
        
        # Starts at 1.0, scales to 1.10 over the duration
        zoom_factor = 1.0 + 0.10 * (t / duration)
        
        new_w = math.ceil(base_w * zoom_factor)
        new_h = math.ceil(base_h * zoom_factor)
        new_w += new_w % 2
        new_h += new_h % 2
        
        current_img = current_img.resize((new_w, new_h), RESAMPLE_METHOD)
        
        crop_x = (new_w - base_w) // 2
        crop_y = (new_h - base_h) // 2
        
        current_img = current_img.crop((crop_x, crop_y, crop_x + base_w, crop_y + base_h))
        return np.array(current_img)

    @staticmethod
    def zoom_out(get_frame: Callable[[float], np.ndarray], t: float, duration: float) -> np.ndarray:
        """Progressively zooms OUT from the center (starts at 110%, ends at 100%)."""
        current_img = Image.fromarray(get_frame(t))
        base_w, base_h = current_img.size
        
        # Starts at 1.10, scales down to 1.0. 
        # The max() clamp ensures we never shrink below the canvas size and get black borders.
        zoom_factor = max(1.0, 1.10 - 0.10 * (t / duration))
        
        new_w = math.ceil(base_w * zoom_factor)
        new_h = math.ceil(base_h * zoom_factor)
        new_w += new_w % 2
        new_h += new_h % 2
        
        current_img = current_img.resize((new_w, new_h), RESAMPLE_METHOD)
        
        crop_x = (new_w - base_w) // 2
        crop_y = (new_h - base_h) // 2
        
        current_img = current_img.crop((crop_x, crop_y, crop_x + base_w, crop_y + base_h))
        return np.array(current_img)

    @staticmethod
    def pan_left_to_right(get_frame: Callable[[float], np.ndarray], t: float, duration: float) -> np.ndarray:
        """Simulates a camera panning from left to right."""
        current_img = Image.fromarray(get_frame(t))
        base_w, base_h = current_img.size
        
        oversize_factor = 1.20
        new_w = math.ceil(base_w * oversize_factor)
        new_h = math.ceil(base_h * oversize_factor)
        
        current_img = current_img.resize((new_w, new_h), RESAMPLE_METHOD)
        
        max_pan_x = new_w - base_w
        crop_x = int(max_pan_x * (t / duration))
        crop_y = (new_h - base_h) // 2
        
        current_img = current_img.crop((crop_x, crop_y, crop_x + base_w, crop_y + base_h))
        return np.array(current_img)

    @staticmethod
    def black_and_white(get_frame: Callable[[float], np.ndarray], t: float, duration: float) -> np.ndarray:
        """Converts the image video into vintage monochrome grayscale style."""
        current_img = Image.fromarray(get_frame(t))
        bw_img = ImageOps.grayscale(current_img)
        return np.array(bw_img.convert("RGB"))

    @staticmethod
    def dramatic_vignette(get_frame: Callable[[float], np.ndarray], t: float, duration: float) -> np.ndarray:
        """Applies a fading dark vignette perimeter that closes in slowly over time."""
        frame = get_frame(t).astype(float)
        h, w, c = frame.shape
        
        x = np.linspace(-1, 1, w)
        y = np.linspace(-1, 1, h)
        x_matrix, y_matrix = np.meshgrid(x, y)
        radius = np.sqrt(x_matrix**2 + y_matrix**2)
        
        cutoff = 1.5 - 0.6 * (t / duration)
        mask = np.clip((cutoff - radius) / 0.5, 0, 1)
        mask = np.expand_dims(mask, axis=2) 
        
        vignette_frame = frame * mask
        return vignette_frame.astype(np.uint8)


# ==========================================
# MODULE: Core Video Generator Pipeline
# ==========================================
class VG:
    # UPDATED REGISTRY with exact string keys for the new zoom effects
    EFFECTS_REGISTRY: Dict[str, Callable[[Callable[[float], np.ndarray], float, float], np.ndarray]] = {
        'zoom_in': VideoEffects.zoom_in,
        'zoom_out': VideoEffects.zoom_out,
        'pan_horizontal': VideoEffects.pan_left_to_right,
        'monochrome': VideoEffects.black_and_white,
        'vignette_pulse': VideoEffects.dramatic_vignette
    }

    @staticmethod
    def create_video_from_image(
        image_path: str, 
        output_path: str, 
        duration: float = 5.0, 
        ratio: tuple = (9, 16), 
        music_path: str = None, 
        voice_path: str = None,
        effect: str = 'zoom_out'
    ) -> str:
        """Generates an mp4 video from an image utilizing pluggable effects and audio mixing."""
        
        # # 1. Pre-process Image Ratio
        img = Image.open(image_path)
        orig_w, orig_h = img.size
        target_aspect = ratio[0] / ratio[1]  # e.g., 9 / 16 = 0.5625
        img_aspect = orig_w / orig_h

        # Calculate canvas dimensions to fit the image safely
        if img_aspect > target_aspect:
            # Image is wider than target aspect ratio (bounded by width)
            crop_w = orig_w
            crop_h = int(orig_w / target_aspect)
        else:
            # Image is taller than target aspect ratio (bounded by height)
            crop_w = int(orig_h * target_aspect)
            crop_h = orig_h
        # crop_w = orig_w
        # crop_h = int(crop_w * 16 / 9)
        print(f"Original image size: {orig_w}x{orig_h}. Target crop size: {crop_w}x{crop_h} for ratio {ratio[0]}:{ratio[1]}.")

        # formatted_img = ImageOps.fit(img, (crop_w, crop_h), method=Image.Resampling.LANCZOS)
       
             # Convert the raw un-cropped image into a MoviePy clip
        img_clip = ImageClip(np.array(img)).with_duration(duration)
        
        # Center the complete image inside your canvas frame (extra space allowed)
        centered_img = img_clip.with_position("center")
       
        # Create a final composite clip with the required canvas dimensions
        clip = CompositeVideoClip([centered_img], size=(crop_w, crop_h)).with_duration(duration)
        
        print(f"Image pre-processed to {crop_w}x{crop_h} for target ratio {ratio[0]}:{ratio[1]}.")
        # 2. Apply Visual Effects
        chosen_effect = effect.lower()
        if chosen_effect in VG.EFFECTS_REGISTRY:
            effect_function = VG.EFFECTS_REGISTRY[chosen_effect]
            clip = clip.transform(lambda get_frame, t: effect_function(get_frame, t, duration))
        
        # print(f"Applied visual effect: {chosen_effect}.")
        
        merged_audio_path = "temp/music/audio_5sec.mp3"

        print(f"Rendering video to  file: {output_path}")
        merged_audio_clip = AudioFileClip(merged_audio_path)
        clip = clip.with_audio(merged_audio_clip)

        # 4. Render output
        clip.write_videofile(
            output_path,
            fps=24, 
            codec="libx264", 
            audio_codec="aac" if merged_audio_clip else None,
            logger=None
        )
        
        # 5. Cleanup
        clip.close()
        merged_audio_clip.close()
        
        
        img.close()
        # video.VG.merge_audio_video(video_path=output_path_with_suffix, audio_path=music_path, output_path=output_path, target_duration=duration)
        return output_path
    
    
    @staticmethod
    def merge_audio_video(video_path: str, audio_path: str, output_path: str, target_duration: float):
        """
        Merges an audio file and a video file and trims them to an exact duration.
        """
        # 1. Verify files exist before starting
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Could not find video at {video_path}")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Could not find audio at {audio_path}")

        print(f"Loading media... Target duration: {target_duration} seconds.")

        # 2. Load the original media files
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)

        # Safety Check: Ensure the requested duration isn't longer than the actual files
        actual_duration = min(target_duration, video_clip.duration, audio_clip.duration)
        if actual_duration < target_duration:
            print(f"Warning: Media is shorter than target. Adjusting duration to {actual_duration}s")

        # 3. Trim both clips to the exact duration
        # .subclip(start_time, end_time) is the safest way to slice media in v2.0
        trimmed_audio = audio_clip.subclipped(0, actual_duration)

        # 4. Attach the trimmed audio to the trimmed video
        final_video = video_clip.with_audio(trimmed_audio)

        # 5. Render to disk
        print("Rendering final video...")
        final_video.write_videofile(
            output_path,
            fps=24,             # Standard cinematic framerate
            codec="libx264",    # Standard MP4 video codec
            audio_codec="aac",  # Standard MP4 audio codec
            logger='bar'        # Show progress bar in terminal
        )

        # 6. Memory Cleanup (Crucial to release file locks on Windows)
        video_clip.close()
        audio_clip.close()
        trimmed_audio.close()
        final_video.close()

        print(f"Success! Saved to {output_path}")
        return output_path
# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    MY_IMAGE = "input_photo.jpg"
    OUTPUT_VIDEO = "final_output.mp4"
    
    if os.path.exists(MY_IMAGE):
        print("Available effects keys to choose from: ", list(VG.EFFECTS_REGISTRY.keys()))
        
        # Now you can use 'zoom_in' or 'zoom_out'
        VG.create_video_from_image(
            image_path=MY_IMAGE,
            output_path=OUTPUT_VIDEO,
            duration=5.0,          
            ratio=(9, 16),         
            effect='zoom_out'  # <-- Trying out the Zoom Out effect
        )
        print(f"Success! Video saved to {OUTPUT_VIDEO}")