import os
import math
from typing import Callable, Dict
import numpy as np
from PIL import Image, ImageOps

# Core imports straight from moviepy v2.0+
from moviepy import ImageClip, AudioFileClip

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
    def slow_zoom(get_frame: Callable[[float], np.ndarray], t: float, duration: float) -> np.ndarray:
        """Resizes the frame progressively, zooming into the center by 5% over the duration."""
        current_img = Image.fromarray(get_frame(t))
        base_w, base_h = current_img.size
        
        zoom_factor = 1 + 0.05 * (t / duration)
        
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
        """Simulates a camera panning from left to right. 
        Requires an initially oversized canvas, which we achieve by scaling slightly first."""
        current_img = Image.fromarray(get_frame(t))
        base_w, base_h = current_img.size
        
        # Scale up canvas by 20% so we have room to slide the camera viewport window
        oversize_factor = 1.20
        new_w = math.ceil(base_w * oversize_factor)
        new_h = math.ceil(base_h * oversize_factor)
        
        current_img = current_img.resize((new_w, new_h), RESAMPLE_METHOD)
        
        # Calculate dynamic horizontal offset based on time elapsed
        max_pan_x = new_w - base_w
        crop_x = int(max_pan_x * (t / duration))
        crop_y = (new_h - base_h) // 2  # Keep vertical perfectly centered
        
        current_img = current_img.crop((crop_x, crop_y, crop_x + base_w, crop_y + base_h))
        return np.array(current_img)

    @staticmethod
    def black_and_white(get_frame: Callable[[float], np.ndarray], t: float, duration: float) -> np.ndarray:
        """Converts the image video into vintage monochrome grayscale style."""
        current_img = Image.fromarray(get_frame(t))
        bw_img = ImageOps.grayscale(current_img)
        # Convert back to RGB format so MoviePy doesn't crash on color-channel expectations
        return np.array(bw_img.convert("RGB"))

    @staticmethod
    def dramatic_vignette(get_frame: Callable[[float], np.ndarray], t: float, duration: float) -> np.ndarray:
        """Applies a fading dark vignette perimeter that closes in slowly over time."""
        frame = get_frame(t).astype(float)
        h, w, c = frame.shape
        
        # Generate custom radial gradient mask dynamically matching frame proportions
        x = np.linspace(-1, 1, w)
        y = np.linspace(-1, 1, h)
        x_matrix, y_matrix = np.meshgrid(x, y)
        radius = np.sqrt(x_matrix**2 + y_matrix**2)
        
        # Make the dark border shadow shrink inwards progressively
        cutoff = 1.5 - 0.6 * (t / duration)
        mask = np.clip((cutoff - radius) / 0.5, 0, 1)
        mask = np.expand_dims(mask, axis=2) # Expand to match RGB 3 channels
        
        vignette_frame = frame * mask
        return vignette_frame.astype(np.uint8)


# ==========================================
# MODULE: Core Video Generator Pipeline
# ==========================================
class VG:
    # A registry mapping human strings to the actual function signatures inside VideoEffects
    EFFECTS_REGISTRY: Dict[str, Callable[[Callable[[float], np.ndarray], float, float], np.ndarray]] = {
        'zoom': VideoEffects.slow_zoom,
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
        effect: str = 'zoom'
    ) -> str:
        """Generates an mp4 video from an image utilizing a pluggable modular effect configuration."""
        
        # 1. Pre-process the image canvas structurally to handle the specified target aspect ratio cleanly
        img = Image.open(image_path)
        orig_w, orig_h = img.size
        target_aspect = ratio[0] / ratio[1]
        
        if orig_w / orig_h > target_aspect:
            crop_w = int(orig_h * target_aspect)
            crop_h = orig_h
        else:
            crop_w = orig_w
            crop_h = int(orig_w / target_aspect)
            
        formatted_img = ImageOps.fit(img, (crop_w, crop_h), method=RESAMPLE_METHOD)
        base_frame = np.array(formatted_img)
        
        # 2. Build the baseline structural MoviePy clip
        clip = ImageClip(base_frame).with_duration(duration)
        
        # 3. Dynamic Effect Mapping Architecture
        chosen_effect = effect.lower()
        if chosen_effect in VG.EFFECTS_REGISTRY:
            effect_function = VG.EFFECTS_REGISTRY[chosen_effect]
            
            # Wrap standard transform function to explicitly include our custom third tracking argument: duration
            def custom_transform_wrapper(get_frame, t):
                return effect_function(get_frame, t, duration)
                
            clip = clip.transform(custom_transform_wrapper)
        else:
            print(f"Warning: Effect '{effect}' not found. Defaulting to static frame rendering.")

        # 4. Audio Integration
        if music_path and os.path.exists(music_path):
            audio = AudioFileClip(music_path).with_duration(duration)
            clip = clip.with_audio(audio)
            
        # 5. Render Video Output Pipeline
        clip.write_videofile(
            output_path, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac" if music_path else None,
            logger='bar'
        )
        
        # 6. Memory cleanup
        clip.close()
        if music_path: 
            audio.close()
        img.close()
        
        return output_path


# ==========================================
# Example Usage: Testing the options
# ==========================================
if __name__ == "__main__":
    MY_IMAGE = "input_photo.jpg"
    OUTPUT_VIDEO = "final_output.mp4"
    
    if os.path.exists(MY_IMAGE):
        print("Available effects keys to choose from: ", list(VG.EFFECTS_REGISTRY.keys()))
        
        # Change the 'effect' variable to test different implementations:
        # Options: 'zoom', 'pan_horizontal', 'monochrome', 'vignette_pulse'
        VG.create_video_from_image(
            image_path=MY_IMAGE,
            output_path=OUTPUT_VIDEO,
            duration=5.0,          
            ratio=(9, 16),         
            effect='pan_horizontal'  # <-- Test the new Horizontal Panning Effect here
        )
        print(f"Success! Video saved to {OUTPUT_VIDEO}")