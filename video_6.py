import os
import math
from typing import Callable, Dict
import numpy as np
from PIL import Image, ImageOps

# MoviePy v2.0+ Imports
from moviepy import ImageClip, AudioFileClip, CompositeAudioClip
from moviepy.audio.fx.AudioLoop import AudioLoop
from moviepy.audio.fx.MultiplyVolume import MultiplyVolume

try:
    from PIL import ImageResampling
    RESAMPLE_METHOD = ImageResampling.LANCZOS
except ImportError:
    RESAMPLE_METHOD = Image.LANCZOS

# ==========================================
# MODULE 2: Visual Effects Library (v2.0 Fixed)
# ==========================================
class VideoEffects:
    # All methods now take a static base_frame array instead of a generator
    @staticmethod
    def zoom_in(base_frame: np.ndarray, t: float, duration: float) -> np.ndarray:
        current_img = Image.fromarray(base_frame)
        base_w, base_h = current_img.size
        zoom_factor = 1.0 + 0.10 * (t / duration)
        
        new_w, new_h = math.ceil(base_w * zoom_factor), math.ceil(base_h * zoom_factor)
        new_w += new_w % 2; new_h += new_h % 2
        
        current_img = current_img.resize((new_w, new_h), RESAMPLE_METHOD)
        crop_x, crop_y = (new_w - base_w) // 2, (new_h - base_h) // 2
        return np.array(current_img.crop((crop_x, crop_y, crop_x + base_w, crop_y + base_h)))

    @staticmethod
    def zoom_out(base_frame: np.ndarray, t: float, duration: float) -> np.ndarray:
        current_img = Image.fromarray(base_frame)
        base_w, base_h = current_img.size
        zoom_factor = max(1.0, 1.10 - 0.10 * (t / duration))
        
        new_w, new_h = math.ceil(base_w * zoom_factor), math.ceil(base_h * zoom_factor)
        new_w += new_w % 2; new_h += new_h % 2
        
        current_img = current_img.resize((new_w, new_h), RESAMPLE_METHOD)
        crop_x, crop_y = (new_w - base_w) // 2, (new_h - base_h) // 2
        return np.array(current_img.crop((crop_x, crop_y, crop_x + base_w, crop_y + base_h)))

    @staticmethod
    def pan_left_to_right(base_frame: np.ndarray, t: float, duration: float) -> np.ndarray:
        current_img = Image.fromarray(base_frame)
        base_w, base_h = current_img.size
        oversize_factor = 1.20
        
        new_w, new_h = math.ceil(base_w * oversize_factor), math.ceil(base_h * oversize_factor)
        current_img = current_img.resize((new_w, new_h), RESAMPLE_METHOD)
        
        crop_x = int((new_w - base_w) * (t / duration))
        crop_y = (new_h - base_h) // 2
        return np.array(current_img.crop((crop_x, crop_y, crop_x + base_w, crop_y + base_h)))


# ==========================================
# MODULE 3: Core Video Generator
# ==========================================
class VG:
    EFFECTS_REGISTRY: Dict[str, Callable[[np.ndarray, float, float], np.ndarray]] = {
        'zoom_in': VideoEffects.zoom_in,
        'zoom_out': VideoEffects.zoom_out,
        'pan_horizontal': VideoEffects.pan_left_to_right
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
        
        # 1. Image Pre-Formatting
        img = Image.open(image_path)
        orig_w, orig_h = img.size
        target_aspect = ratio[0] / ratio[1]
        
        if orig_w / orig_h > target_aspect:
            crop_w, crop_h = int(orig_h * target_aspect), orig_h
        else:
            crop_w, crop_h = orig_w, int(orig_w / target_aspect)
            
        formatted_img = ImageOps.fit(img, (crop_w, crop_h), method=RESAMPLE_METHOD)
        base_frame = np.array(formatted_img)
        
        # 2. Base Clip Setup (Using VideoClip to bypass generator bugs)
        chosen_effect = effect.lower()
        if chosen_effect in VG.EFFECTS_REGISTRY:
            effect_function = VG.EFFECTS_REGISTRY[chosen_effect]
            def make_frame(t): return effect_function(base_frame, t, duration)
            clip = VideoClip(make_frame=make_frame).with_duration(duration)
        else:
            clip = ImageClip(base_frame).with_duration(duration)

        # 3. Audio Mixing (v2.0 Logic)
        audio_clips_to_mix = []
        
        # Voiceover (Does NOT alter duration so silence pads the end automatically)
        if voice_path and os.path.exists(voice_path):
            voice_clip = AudioFileClip(voice_path)
            audio_clips_to_mix.append(voice_clip)
            
        # Background Music (Uses v2.0 effect arrays)
        if music_path and os.path.exists(music_path):
            music_clip = AudioFileClip(music_path)
            
            if music_clip.duration and music_clip.duration < duration:
                music_clip = music_clip.with_effects([
                    AudioLoop(duration=duration),
                    MultiplyVolume(0.1)
                ])
            else:
                music_clip = music_clip.with_duration(duration).with_effects([
                    MultiplyVolume(0.1)
                ])
            audio_clips_to_mix.append(music_clip)

        # Merge Audio tracks
        if audio_clips_to_mix:
            if len(audio_clips_to_mix) > 1:
                final_audio = CompositeAudioClip(audio_clips_to_mix)
            else:
                final_audio = audio_clips_to_mix[0]
            clip = clip.with_audio(final_audio)

        # 4. Render output
        clip.write_videofile(
            output_path, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac" if audio_clips_to_mix else None,
            logger='bar'
        )
        
        # 5. Cleanup
        clip.close()
        for a_clip in audio_clips_to_mix: a_clip.close()
        img.close()
        
        return output_path