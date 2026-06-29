import os
import textwrap
from PIL import Image, ImageDraw, ImageFont
import json

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

    def create_overlay(self, image_path, output_name, title="", content="", 
                       font_path="", title_size=40, content_size=30, 
                       text_color="black", padding=70, wrap_factor_square=None):
        
        with Image.open(image_path) as img:
            draw = ImageDraw.Draw(img)
            
            # Load fonts
            font_title = ImageFont.truetype(font_path, title_size)
            font_content = ImageFont.truetype(font_path, content_size)
            
            # Calculate max width for text
            max_text_width = img.width - (padding * 2)
            title_wrap_factor =  wrap_factor_square["title_size"]
            content_wrap_factor = wrap_factor_square["content_size"] 
           
            # Wrap both title and content
            wrapped_title = self._wrap_text(title, font_title, max_text_width, factor=title_wrap_factor)
            wrapped_content = self._wrap_text(content, font_content, max_text_width, factor=content_wrap_factor)
            
            # Set vertical starting point
            current_y = padding
            line_spacing = wrap_factor_square.get("line_spacing", 10)  # Default line spacing if not provided
            
            # Draw Title
            for line in wrapped_title:
                draw.text((img.width/2, current_y), line, font=font_title, 
                          fill="orange", anchor="mm")
                current_y += title_size + line_spacing
            
            # Add extra space between title block and content block
            current_y -= 20
            # ... (after drawing title)
            
            # Draw the separator line
            self._draw_separator(  draw, img.width / 2,  current_y, max_text_width, 
                color='red'
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

    def process_json(self, json_file_path, font_path,background_image_path="bg4.jpeg",
                      image_prefix="img_", title_size=50, content_size=30, text_color="black",
                      wrap_factor_square=None):
        
        """Reads a JSON file and generates images for each entry."""
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        count = 0
        #   background_image_path = "bg4.jpeg"  # Ensure this image exists in the same directory    
        for item in data:
            self.create_overlay(
                image_path=background_image_path,
                output_name=f"{image_prefix}{count}.png",
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
    
    file = "posts.json"
    
    color = "white"
    image_prefix = "motivational_"
    background_image_path = "bg4.jpg" 
    wrap_factor_vertical = {
        "title_size": 2.5,
        "content_size": 2,
        "bg_image":"bg4.jpeg",
        "title_font_size": 70,
        "content_font_size": 60,
        "output_folder" : "temp/images/motivational_vertical",
        "file": "posts.json",
        "color": "white",
        "image_prefix": "motivational_",
        "background_image_path": "bg_black.jpg" ,
        "padding_top": 180,
        "line_spacing":20
    }      
    wrap_factor_square  = {
        "title_size": 1.5,
        "content_size": 1.3,
        "bg_image":"bg_black.jpg" ,
        "title_font_size": 40,
        "content_font_size": 30,
        "output_folder" : "temp/images/motivational",
        "file": "posts.json",
        "color": "white",
        "image_prefix": "motivational_",
        "background_image_path": "bg4.jpeg" ,
        "padding_top": 70,
        "line_spacing":10

    }

    # Process the entire batch from JSON
    config = wrap_factor_square

    if not os.path.exists(config["output_folder"]):
        os.makedirs(config["output_folder"])
    engine = TextOverlayEngine(output_folder=config["output_folder"])

    engine.process_json(
        json_file_path=file,
        font_path="arial.ttf",
        background_image_path = config["background_image_path"],
        image_prefix=config["image_prefix"],
        title_size=config["title_font_size"],
        content_size=config["content_font_size"],
        text_color=config["color"],
        wrap_factor_square=config
    )
