import os
import textwrap
from PIL import Image, ImageDraw, ImageFont
import json

class TextOverlayEngine:
    def __init__(self, output_folder="output"):
        self.output_folder = output_folder
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def _wrap_text(self, text, font, max_width,factor=1.6):
        """Wraps text to fit within the specified pixel width."""
        # Get width of a character more accurately
        avg_char_width = font.getbbox("A")[2]
        chars_per_line = max(1, max_width // avg_char_width)*factor
        
        lines = []
        for line in text.split('\n'):
            lines.extend(textwrap.wrap(line, width=chars_per_line))
        return lines

    def create_overlay(self, image_path, output_name, title="", content="", 
                       font_path="", title_size=40, content_size=30, 
                       text_color="black", padding=200):
        
        with Image.open(image_path) as img:
            draw = ImageDraw.Draw(img)
            
            # Load fonts
            font_title = ImageFont.truetype(font_path, title_size)
            font_content = ImageFont.truetype(font_path, content_size)
            
            # Calculate max width for text
            max_text_width = img.width - (padding * 2)
            
            # Wrap both title and content
            wrapped_title = self._wrap_text(title, font_title, max_text_width, factor=2.5)
            wrapped_content = self._wrap_text(content, font_content, max_text_width, factor=2)
            
            # Set vertical starting point
            current_y = padding
            line_spacing = 25
            
            # Draw Title
            for line in wrapped_title:
                draw.text((img.width/2, current_y), line, font=font_title, 
                          fill="orange", anchor="mm")
                current_y += title_size + line_spacing
            
            # Add extra space between title block and content block
            current_y -= 30
            # ... (after drawing title)
            
            # Draw the separator line
            self._draw_separator(  draw, img.width / 2,  current_y, max_text_width, 
                color=text_color
            )
            
            current_y += 50 
            line_no = 0
            color = text_color
            # Draw Content
            for line in wrapped_content:
                if line_no%2 == 0:
                    color = text_color
                else:
                    color = "lightgreen"

                draw.text((img.width/2, current_y), line, font=font_content, 
                          fill=color, anchor="mm")
                current_y += content_size + line_spacing
                line_no += 1
            
            # Save the result
            save_path = os.path.join(self.output_folder, output_name)
            img.save(save_path)
            print(f"Image saved successfully at: {save_path}")
    
    def _draw_separator(self, draw, x_center, y_pos, width, color="black", thickness=7):
        """Draws a centered horizontal line as a separator."""
        line_length = width * .8  # Line covers 70% of the text width
        start_x = x_center - (line_length / 2)
        end_x = x_center + (line_length / 2)
        
        draw.line([(start_x, y_pos), (end_x, y_pos)], fill=color, width=thickness)

    def process_json(self, json_file_path, font_path, title_size=50, content_size=30, text_color="black"):
        """Reads a JSON file and generates images for each entry."""
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        count = 0
        background_image_path = "bg_black.jpg"  # Ensure this image exists in the same directory    
        for item in data:
            self.create_overlay(
                image_path=background_image_path,
                output_name=f"{count}_motivational.png",
                title=item['title'],
                content=item['description'],
                font_path=font_path,
                title_size=title_size,
                content_size=content_size,
                text_color=text_color
            )
            count += 1
        print(f"Total images generated: {count}")

if __name__ == "__main__":
    engine = TextOverlayEngine(output_folder="generated_images")
    
    # Process the entire batch from JSON
    engine.process_json(
        json_file_path="posts.json",
        font_path="arial.ttf",
        title_size=70,
        content_size=50,
        text_color="white"
    )
# Example Usage:
# if __name__ == "__main__":
#     engine = TextOverlayEngine(output_folder="generated_images")
    
#     title = "Start Before Ready"
#     content =  "You keep waiting for confidence before taking the first step, but confidence usually arrives after action. Small imperfect moves build the life you dream about. Progress always beats hesitation"
#     background_image_path = "background1.jpg"  # Ensure this image exists in the same directory
#     result_image_name = "result.png"
#     engine.create_overlay(
#         image_path=background_image_path,
#         output_name=result_image_name,
#         title=title,
#         content=content,
#         font_path="arial.ttf", 
#         title_size=50,
#         content_size=40,
#         text_color="black"
#     )
#     {
# "title": "Start Before Ready", 
# "title_font_size": 50,
# "description": "You keep waiting for confidence before taking the first step, but confidence usually arrives after action. Small imperfect moves build the life you dream about. Progress always beats hesitation",
#  "description_font_size": 40,
#  "imagePrompt": "9:16 vertical composition, minimalist pencil sketch on a very light gray background (#D3D3D3) instead of white for subtle distinction. Leave the upper 75% of the image completely empty for text. At the very bottom, draw a small person climbing simple uneven stone steps toward a distant mountain. Soft graphite lines, hand-drawn, monochrome, minimal details, subtle shading, inspirational, drawing positioned as low as possible." 
#     }