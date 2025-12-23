#!/usr/bin/env python3
"""
Script to create a LinkedIn Christmas post with Nimex Terminals branding.
- Removes "and happy newyear" text from Christmas image
- Adds Nimex Terminals logo
- Adds Christmas message
- Formats as LinkedIn post (1200x627px)
- Saves as PNG
"""

from PIL import Image, ImageDraw, ImageFont
import os
import sys
import numpy as np

def find_image_files():
    """Find Christmas image and logo files in workspace"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.JPG', '.JPEG', '.PNG', '.GIF', '.WEBP']
    files = {}
    all_images = []
    
    # Look for common filenames
    for root, dirs, filenames in os.walk('/workspace'):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for filename in filenames:
            # Skip hidden files and our script files
            if filename.startswith('.') or filename.endswith('.py') or filename.endswith('.html'):
                continue
                
            if any(filename.lower().endswith(ext.lower()) for ext in image_extensions):
                filepath = os.path.join(root, filename)
                filename_lower = filename.lower()
                all_images.append((filepath, filename_lower))
                
                # Try to identify Christmas image
                if 'christmas' in filename_lower and 'logo' not in filename_lower:
                    if 'christmas' not in files:
                        files['christmas'] = filepath
                # Try to identify logo
                elif ('logo' in filename_lower or 'nimex' in filename_lower) and 'logo' not in files:
                    files['logo'] = filepath
    
    # If we found images but didn't categorize them, assign them
    if all_images:
        # If no Christmas image found, use the largest image file (likely the main image)
        if 'christmas' not in files:
            # Sort by file size, largest first
            image_sizes = []
            for filepath, _ in all_images:
                try:
                    size = os.path.getsize(filepath)
                    image_sizes.append((size, filepath))
                except:
                    pass
            if image_sizes:
                image_sizes.sort(reverse=True)
                files['christmas'] = image_sizes[0][1]
        
        # If no logo found, look for smaller images that might be logos
        if 'logo' not in files:
            for filepath, filename_lower in all_images:
                if filepath != files.get('christmas'):
                    try:
                        size = os.path.getsize(filepath)
                        # Logos are typically smaller
                        if size < 5 * 1024 * 1024:  # Less than 5MB
                            files['logo'] = filepath
                            break
                    except:
                        pass
    
    return files

def remove_text_from_image(img, text_to_remove="and happy newyear"):
    """
    Remove text from image using intelligent background sampling and inpainting.
    Looks for text in common positions (bottom area) and removes it.
    """
    
    # Convert to numpy array for easier manipulation
    img_array = np.array(img)
    height, width = img_array.shape[:2]
    
    # Common positions for "and happy newyear" text
    # Usually at bottom center or bottom right
    # We'll check multiple potential areas
    text_area_height = int(height * 0.12)  # 12% of image height
    text_area_y_start = height - text_area_height - 30
    
    # Sample background from multiple areas around the text
    # Sample from left, right, and above the text area
    sample_regions = []
    
    # Sample from above
    if text_area_y_start > 50:
        sample_regions.append(img_array[max(0, text_area_y_start - 100):text_area_y_start, :])
    
    # Sample from sides (if text is centered)
    side_width = width // 4
    if text_area_y_start > 0:
        sample_regions.append(img_array[max(0, text_area_y_start - 50):text_area_y_start, :side_width])
        sample_regions.append(img_array[max(0, text_area_y_start - 50):text_area_y_start, -side_width:])
    
    # Calculate average background color from samples
    if sample_regions:
        all_pixels = np.concatenate([region.reshape(-1, 3) for region in sample_regions], axis=0)
        avg_color = tuple(map(int, np.mean(all_pixels, axis=0)))
    else:
        # Fallback: use top area
        avg_color = tuple(map(int, np.mean(img_array[:height//4, :].reshape(-1, 3), axis=0)))
    
    # Create a mask for the text area
    text_region = img_array[text_area_y_start:height, :]
    
    # Use a more sophisticated approach: blend with surrounding area
    # Create a gradient fill that matches the background
    draw = ImageDraw.Draw(img)
    
    # Draw filled rectangle with average background color
    draw.rectangle([(0, text_area_y_start), (width, height)], fill=avg_color)
    
    # Add some blending by sampling nearby pixels and creating a smooth transition
    # This helps if the background isn't uniform
    if text_area_y_start > 20:
        # Sample a few pixels from just above the text area for better matching
        blend_samples = []
        for x_offset in [width//4, width//2, 3*width//4]:
            for y_offset in range(-20, 0, 5):
                y_pos = text_area_y_start + y_offset
                if 0 <= y_pos < height and 0 <= x_offset < width:
                    blend_samples.append(img_array[y_pos, x_offset])
        
        if blend_samples:
            blend_color = tuple(map(int, np.mean(blend_samples, axis=0)))
            # Use a slight gradient for more natural look
            for i in range(text_area_height):
                alpha = i / text_area_height
                blended_color = tuple(
                    int(avg_color[j] * (1 - alpha) + blend_color[j] * alpha)
                    for j in range(3)
                )
                y_pos = text_area_y_start + i
                if y_pos < height:
                    draw.rectangle([(0, y_pos), (width, y_pos + 1)], fill=blended_color)
    
    return img

def add_logo_to_image(base_img, logo_path, position='bottom_left'):
    """Add logo to the base image"""
    try:
        logo = Image.open(logo_path)
        # Convert to RGBA if needed
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')
        
        # Resize logo (make it about 15-20% of image width)
        base_width, base_height = base_img.size
        logo_width = int(base_width * 0.15)
        logo_height = int(logo_width * (logo.height / logo.width))
        logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        
        # Position logo
        if position == 'bottom_left':
            x = 40
            y = base_height - logo_height - 40
        elif position == 'bottom_right':
            x = base_width - logo_width - 40
            y = base_height - logo_height - 40
        elif position == 'top_left':
            x = 40
            y = 40
        else:  # top_right
            x = base_width - logo_width - 40
            y = 40
        
        # Paste logo onto base image
        base_img.paste(logo, (x, y), logo)
        return base_img, (x, y, logo_width, logo_height)
    except Exception as e:
        print(f"Error adding logo: {e}")
        return base_img, None

def add_text_to_image(img, text, position='below_logo', logo_info=None):
    """Add text to the image"""
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # Try to load a nice font, fallback to default
    try:
        # Try to use a system font - make it larger for LinkedIn post
        font_size = int(height * 0.045)  # 4.5% of image height
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        try:
            font_size = int(height * 0.045)
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
        except:
            # Default font - will be smaller
            font_size = 24
            font = ImageFont.load_default()
    
    # Calculate text position
    if position == 'below_logo' and logo_info:
        x, y, logo_w, logo_h = logo_info
        # Position text below logo, aligned to logo's left edge
        text_x = x
        text_y = y + logo_h + 30  # 30px spacing below logo
    else:
        # Center bottom
        text_x = width // 2
        text_y = height - 120
    
    # Draw text with outline for better visibility
    text_color = (255, 255, 255)  # White
    outline_color = (0, 0, 0)  # Black outline
    
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center the text horizontally if needed
    if position == 'center_bottom':
        text_x = (width - text_width) // 2
    elif position == 'below_logo' and logo_info:
        # Keep text aligned with logo, but ensure it fits
        if text_x + text_width > width - 40:
            # If text would overflow, center it instead
            text_x = (width - text_width) // 2
    
    # Draw outline (draw text multiple times offset for better visibility)
    outline_width = 3
    for adj in range(-outline_width, outline_width + 1):
        for adj2 in range(-outline_width, outline_width + 1):
            if adj != 0 or adj2 != 0:
                draw.text((text_x + adj, text_y + adj2), text, font=font, fill=outline_color)
    
    # Draw main text
    draw.text((text_x, text_y), text, font=font, fill=text_color)
    
    return img

def format_as_linkedin_post(img):
    """Resize image to LinkedIn post dimensions (1200x627px)"""
    linkedin_width = 1200
    linkedin_height = 627
    
    # Calculate scaling to fill the canvas while maintaining aspect ratio
    img_width, img_height = img.size
    scale_width = linkedin_width / img_width
    scale_height = linkedin_height / img_height
    
    # Use the larger scale to fill the canvas (crop excess)
    scale = max(scale_width, scale_height)
    
    # Resize image
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Create new image with exact LinkedIn dimensions
    linkedin_img = Image.new('RGB', (linkedin_width, linkedin_height), color=(0, 0, 0))
    
    # Center the image (crop if necessary)
    paste_x = (linkedin_width - new_width) // 2
    paste_y = (linkedin_height - new_height) // 2
    linkedin_img.paste(img_resized, (paste_x, paste_y))
    
    return linkedin_img

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Create LinkedIn Christmas post with Nimex Terminals branding')
    parser.add_argument('--christmas-image', type=str, help='Path to Christmas image file')
    parser.add_argument('--logo', type=str, help='Path to Nimex Terminals logo file')
    parser.add_argument('--output', type=str, default='/workspace/christmas_linkedin_post.png', help='Output PNG file path')
    args = parser.parse_args()
    
    print("Searching for image files...")
    image_files = find_image_files()
    
    # Override with command-line arguments if provided
    if args.christmas_image:
        if os.path.exists(args.christmas_image):
            image_files['christmas'] = args.christmas_image
        else:
            print(f"ERROR: Christmas image not found at: {args.christmas_image}")
            sys.exit(1)
    
    if args.logo:
        if os.path.exists(args.logo):
            image_files['logo'] = args.logo
        else:
            print(f"WARNING: Logo not found at: {args.logo}")
            print("Continuing without logo...")
    
    if not image_files.get('christmas'):
        print("ERROR: Christmas image not found!")
        print("Please ensure a Christmas image file is in the workspace.")
        print("Looking for files with 'christmas' in the name or any image file.")
        print("\nUsage:")
        print("  python3 create_christmas_linkedin_post.py")
        print("  python3 create_christmas_linkedin_post.py --christmas-image path/to/image.jpg --logo path/to/logo.png")
        sys.exit(1)
    
    if not image_files.get('logo'):
        print("WARNING: Logo file not found!")
        print("Looking for files with 'logo' or 'nimex' in the name.")
        print("Continuing without logo...")
    
    print(f"Found Christmas image: {image_files.get('christmas')}")
    if image_files.get('logo'):
        print(f"Found logo: {image_files.get('logo')}")
    
    # Load Christmas image
    try:
        christmas_img = Image.open(image_files['christmas'])
        # Convert to RGB if needed
        if christmas_img.mode != 'RGB':
            christmas_img = christmas_img.convert('RGB')
        print(f"Loaded Christmas image: {christmas_img.size}")
    except Exception as e:
        print(f"Error loading Christmas image: {e}")
        sys.exit(1)
    
    # Remove "and happy newyear" text
    print("Removing 'and happy newyear' text...")
    christmas_img = remove_text_from_image(christmas_img, "and happy newyear")
    
    # Add logo if available
    logo_info = None
    if image_files.get('logo'):
        print("Adding logo...")
        christmas_img, logo_info = add_logo_to_image(christmas_img, image_files['logo'], position='bottom_left')
    
    # Add message text
    message = "May this christmas bring prosperity, love and success to your life"
    print(f"Adding message: '{message}'")
    christmas_img = add_text_to_image(christmas_img, message, position='below_logo' if logo_info else 'center_bottom', logo_info=logo_info)
    
    # Format as LinkedIn post
    print("Formatting as LinkedIn post (1200x627px)...")
    linkedin_post = format_as_linkedin_post(christmas_img)
    
    # Save as PNG
    output_path = args.output
    linkedin_post.save(output_path, 'PNG', quality=95)
    print(f"✓ Saved LinkedIn post to: {output_path}")
    print(f"  Dimensions: {linkedin_post.size[0]}x{linkedin_post.size[1]}px")

if __name__ == '__main__':
    main()
