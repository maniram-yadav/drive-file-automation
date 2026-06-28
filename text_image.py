import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

class TextOverlayEngine:
    def __init__(self, output_folder="output"):
        self.output_folder = output_folder
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def _wrap_text(self, text, font, max_width):
        """Wraps text to fit within the specified pixel width."""
        # Get width of a character more accurately
        avg_char_width = font.getbbox("A")[2]
        chars_per_line = max(1, max_width // avg_char_width)*1.6
        
        lines = []
        for line in text.split('\n'):
            lines.extend(textwrap.wrap(line, width=chars_per_line))
        return lines

    def create_overlay(self, image_path, output_name, title="", content="", 
                       font_path="", title_size=40, content_size=30, 
                       text_color="black", padding=130):
        
        with Image.open(image_path) as img:
            draw = ImageDraw.Draw(img)
            
            # Load fonts
            font_title = ImageFont.truetype(font_path, title_size)
            font_content = ImageFont.truetype(font_path, content_size)
            
            # Calculate max width for text
            max_text_width = img.width - (padding * 2)
            
            # Wrap both title and content
            wrapped_title = self._wrap_text(title, font_title, max_text_width)
            wrapped_content = self._wrap_text(content, font_content, max_text_width)
            
            # Set vertical starting point
            current_y = padding
            line_spacing = 15
            
            # Draw Title
            for line in wrapped_title:
                draw.text((img.width/2, current_y), line, font=font_title, 
                          fill=text_color, anchor="mm")
                current_y += title_size + line_spacing
            
            # Add extra space between title block and content block
            current_y += 20
            
            # Draw Content
            for line in wrapped_content:
                draw.text((img.width/2, current_y), line, font=font_content, 
                          fill=text_color, anchor="mm")
                current_y += content_size + line_spacing
            
            # Save the result
            save_path = os.path.join(self.output_folder, output_name)
            img.save(save_path)
            print(f"Image saved successfully at: {save_path}")

# Example Usage:
if __name__ == "__main__":
    engine = TextOverlayEngine(output_folder="generated_images")
    
    engine.create_overlay(
        image_path="background.jpg",
        output_name="result.png",
        title="This is a very long title that will now wrap automatically",
        content="This is the content section. It will also wrap automatically if it exceeds the width of the image while maintaining padding.",
        font_path="arial.ttf", 
        title_size=50,
        content_size=40,
        text_color="black"
    )