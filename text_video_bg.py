import datetime
import os
import glob
import textwrap
from PIL import Image, ImageDraw, ImageFont
import json
from datetime import datetime
import numpy as np
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip,AudioFileClip
import moviepy.video.fx as fx


class TextOverlayEngine:
    def __init__(self, output_folder="output"):
        self.output_folder = output_folder
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def _wrap_text(self, text, font, max_width, factor=1.6):
        """Wraps text to fit within the specified pixel width."""
        # Get width of a character more accurately
        avg_char_width = font.getbbox("A")[2]
        chars_per_line = max(1, max_width // avg_char_width) * factor

        lines = []
        for line in text.split('\n'):
            lines.extend(textwrap.wrap(line, width=chars_per_line))
        return lines

    def create_overlay(self, bg_video_path, output_name, duration=5.0, title="", content="", 
                       font_path="", title_size=40, content_size=30, 
                       text_color="black", padding=70, wrap_factor_square=None):
        print("Background vidoe clip : ",bg_video_path)
        # 1. Open the background video to get its exact canvas dimensions
        # bg_clip = VideoFileClip(bg_video_path).subclipped(0, duration)
        duration = wrap_factor_square["duration"]
        # 1. Load the background video clip
        bg_clip = VideoFileClip(bg_video_path)
        # 2. Check if the video is shorter than the requested duration
        if bg_clip.duration < duration:
            print(f"Warning: Background video ({bg_clip.duration}s) is shorter than target duration ({duration}s). Looping video.")
            # Loop the video to fill the space, then cut it exactly at your target duration
            bg_clip = bg_clip.with_effects([fx.Loop(n=None, duration=duration)])
        else:
            # If it is long enough, safely cut it down to size
            bg_clip = bg_clip.subclipped(0, duration)
        video_w, video_h = bg_clip.size
        
        # 2. Create a completely transparent Pillow canvas matching the video dimensions
        # This will hold your text and separator line layers
        img = Image.new("RGBA", (video_w, video_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Load fonts
        font_title = ImageFont.truetype(font_path, title_size)
        font_content = ImageFont.truetype(font_path, content_size)
        
        # Calculate max width for text using video canvas width
        max_text_width = video_w - (padding * 2)
        title_wrap_factor = wrap_factor_square["title_size"]
        content_wrap_factor = wrap_factor_square["content_size"] 
       
        # Wrap both title and content
        wrapped_title = self._wrap_text(title, font_title, max_text_width, factor=title_wrap_factor)
        wrapped_content = self._wrap_text(content, font_content, max_text_width, factor=content_wrap_factor)
        
        # Set vertical starting point
        current_y = padding
        line_spacing = wrap_factor_square.get("line_spacing", 10)
        
        # Draw Title
        for line in wrapped_title:
            draw.text((video_w / 2, current_y), line, font=font_title, 
                      fill="orange", anchor="mm")
            current_y += title_size + line_spacing
        
        # Add extra space between title block and content block
        current_y -= 20
        
        # Draw the separator line
        self._draw_separator(draw, video_w / 2, current_y, max_text_width, color='red')
        
        current_y += 50 
        line_no = 0
        
        # Draw Content
        for line in wrapped_content:
            if line_no % 2 == 0:
                color = text_color
            else:
                color = "lightgreen"

            draw.text((video_w / 2, current_y), line, font=font_content, 
                      fill=color, anchor="mm")
            current_y += content_size + line_spacing
            line_no += 1
        
        # 3. Convert the transparent Pillow image with text into a MoviePy clip
        # We enforce transparency handling by separating the RGB and Alpha channels
        img_np = np.array(img)
        text_clip = (ImageClip(img_np[:, :, :3])
                     .with_duration(duration)
                     .with_mask(ImageClip(img_np[:, :, 3] / 255.0, is_mask=True)))
        
        # 4. Composite the text overlay directly on top of your background video clip
        final_video = CompositeVideoClip([bg_clip, text_clip], size=(video_w, video_h))
        merged_audio_path = "temp/music/audio_10sec.mp3"

        print(f"Rendering video to  file: {output_name}")
        merged_audio_clip = AudioFileClip(merged_audio_path)
        final_video = final_video.with_audio(merged_audio_clip)

        # 5. Export to video output destination
        save_path = os.path.join(self.output_folder, output_name)
        final_video.write_videofile(
            save_path, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac" if bg_clip.audio else None,
            logger=None
        )
        
        # 6. Clean up open media file handles
        final_video.close()
        bg_clip.close()
        img.close()
        
        print(f"Video saved successfully at: {save_path}")
        return save_path

    
    def _draw_separator(self, draw, x_center, y_pos, width, color="black", thickness=7):
        """Draws a centered horizontal line as a separator."""
        line_length = width * .8  # Line covers 70% of the text width
        start_x = x_center - (line_length / 2)
        end_x = x_center + (line_length / 2)
        
        draw.line([(start_x, y_pos), (end_x, y_pos)], fill=color, width=thickness)

    def process_json(self, json_file_path, font_path,background_video_path="temp/videos/bg1.mp4",
                      image_prefix="img_", title_size=50, content_size=30, text_color="black",
                      wrap_factor_square=None):
        
        """Reads a JSON file and generates images for each entry."""
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        count = 0
        #   background_image_path = "bg4.jpeg"  # Ensure this image exists in the same directory    
        for item in data:
            # add formatted date add time second as well with minute with second string in output_name  
            formatted_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_name = f"{image_prefix}_{formatted_date}_{count}_.mp4"
            print(f"Generating image: {output_name} for title: {item['title']}")

            self.create_overlay(
                bg_video_path=background_video_path,
                output_name=output_name,
                title=item['title'],
                content=item['description'],
                font_path=font_path,
                title_size=title_size,
                content_size=content_size,
                text_color=text_color,
                padding=config["padding_top"],
                wrap_factor_square=wrap_factor_square
            )
            count += 1
        print(f"Total images generated: {count}")


if __name__ == "__main__":
    
    # Define the folder containing your source files
    input_folder = "json" 
    
    color = "white"
    image_prefix = "motivational_"
    background_image_path = "bg4.jpg" 
    wrap_factor_vertical = {
        "title_size": 2.5,
        "content_size": 2,
        "bg_image":"bg4.jpeg",
        "title_font_size": 70,
        "content_font_size": 60,
        "output_folder" : "temp/videos/motivational_vertical",
        "background_video_path":"temp/videos/bg1.mp4",
        "color": "white",
        "image_prefix": "motivational_",
        "background_image_path": "bg_black.jpg" ,
        "padding_top": 170,
        "line_spacing":15,
        "duration":10,
    }      
    wrap_factor_square  = {
        "title_size": 1.5,
        "content_size": 1.3,
        "bg_image":"bg_black.jpg" ,
        "title_font_size": 40,
        "content_font_size": 30,
        "output_folder" : "temp/images/motivational",
        "background_video_path":"temp/videos/bg1.mp4",
        "color": "white",
        "image_prefix": "motivational_",
        "background_image_path": "bg4.jpeg" ,
        "padding_top": 70,
        "line_spacing":10,
         "duration":10,
    }

    # Process the entire batch from JSON
    # config = wrap_factor_square
    config = wrap_factor_vertical

    if not os.path.exists(config["output_folder"]):
        os.makedirs(config["output_folder"])
        
    engine = TextOverlayEngine(output_folder=config["output_folder"])

    # Find all JSON files in the specified input folder
    search_path = os.path.join(input_folder, "*.json")
    file_list = glob.glob(search_path)

    if not file_list:
        print(f"No JSON files found in {input_folder}")

    # Loop through each file and call the method
    for file_path in file_list:
        print(f"Processing file: {file_path}")
        # if file have no content, skip it
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON file: {file_path}")
                continue
            if not data:
                print(f"Skipping empty JSON file: {file_path}")
                continue

        engine.process_json(
            json_file_path=file_path,  # Now dynamically uses the current file
            font_path="arial.ttf",
            background_video_path = config["background_video_path"],
            image_prefix=config["image_prefix"],
            title_size=config["title_font_size"],
            content_size=config["content_font_size"],
            text_color=config["color"],
            wrap_factor_square=config
        )
        print(f"Finished processing file: {file_path}\n")
