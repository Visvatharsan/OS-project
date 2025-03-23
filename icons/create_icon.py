import os
from PIL import Image, ImageDraw, ImageFont

# Create a 256x256 transparent image
img = Image.new('RGBA', (256, 256), color=(0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Colors
process_color = (24, 144, 180)  # Blue
resource_color = (76, 175, 80)  # Green
edge_color = (255, 193, 7)      # Yellow
background_color = (44, 62, 80, 200)  # Dark blue with transparency

# Draw a background
draw.rectangle([(20, 20), (236, 236)], fill=background_color, outline=None, width=0)

# Draw process nodes (circles)
draw.ellipse([(50, 50), (110, 110)], fill=process_color)
draw.ellipse([(150, 150), (210, 210)], fill=process_color)

# Draw resource node (square)
draw.rectangle([(150, 50), (210, 110)], fill=resource_color)

# Draw edges
draw.line([(80, 80), (180, 80)], fill=edge_color, width=5)
draw.line([(180, 180), (80, 80)], fill=edge_color, width=5)

# Add arrowheads
def draw_arrow(draw, start, end, color, width=5):
    draw.line([start, end], fill=color, width=width)
    # Calculate direction vector
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    # Normalize
    length = (dx**2 + dy**2)**0.5
    dx /= length
    dy /= length
    # Calculate perpendicular vectors for arrow head
    arrow_size = 10
    p1 = (end[0] - arrow_size*dx - arrow_size*dy*0.5, end[1] - arrow_size*dy + arrow_size*dx*0.5)
    p2 = (end[0] - arrow_size*dx + arrow_size*dy*0.5, end[1] - arrow_size*dy - arrow_size*dx*0.5)
    # Draw arrow head
    draw.polygon([end, p1, p2], fill=color)

# Draw arrows
draw_arrow(draw, (140, 80), (180, 80), edge_color)
draw_arrow(draw, (170, 170), (90, 90), edge_color)

# Save as ICO file
img.save('icons/rag_icon.ico', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("Icon created successfully at 'icons/rag_icon.ico'") 