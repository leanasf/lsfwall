# After reading the Xlib manual, gods do I understand what people mean by "X11 is bloated". It took me a month just to read the first three chapters.
# With that being said, the code in here comes from stuff searched online, no code here is LLM-generated.
# All code is prone to errors. Report bugs at https://github.com/leanasf/lsfwall/issues

import argparse
import os
import sys
import time
import random

from PIL import Image
from Xlib import display, X, Xatom

# This function does the core logic of setting the wallpaper.
def setwp(path, fit="zoomed"):
    # Do initial initialization
    d = display.Display()
    screen = d.screen()
    root = screen.root

    geom = root.get_geometry()
    width = geom.width
    height = geom.height
    depth = screen.root_depth

    # Image processing logic
    with Image.open(path) as img:
        img = img.convert("RGB")
        imgw, imgh = img.size
        canvas = Image.new("RGB", (width, height), (0, 0, 0))
        # Resizing logic goes here.
        # Who even uses None, anyway? It's only here because the fit styles are supposed to match XFCE4.
        if fit == "none":
            canvas.paste(img, (0, 0))
            processed = canvas
        elif fit == "centered":
            x = (width - imgw) // 2
            y = (height - imgh) // 2
            canvas.paste(img, (x, y))
            processed = canvas
        # Choose Tiled for low-resolution images or tiles
        elif fit == "tiled":
            for x in range(0, width, imgw):
                for y in range (0, height, imgh):
                    canvas.paste(img, (x, y))
            processed = canvas
        elif fit == "stretched":
            processed = img.resize((width, height), Image.Resampling.LANCZOS)
        elif fit == "scaled":
            newh = height
            neww = int(imgw * (height / imgh))
            resized = img.resize((neww, newh), Image.Resampling.LANCZOS)
            x = (width - neww) // 2
            canvas.paste(resized, (x, 0))
            processed = canvas
        # Zoomed is the opposite of Scaled
        elif fit == "zoomed":
            neww = width
            newh = int(imgh * (width / imgw))
            resized = img.resize((neww, newh), Image.Resampling.LANCZOS)
            y = (height - newh) // 2
            canvas.paste(resized, (0, y))
            processed = canvas
        else:
            raise ValueError(f"{fit} is an invalid fit.")
        # Convert to RGBX (4b/px) to align with standard 24/32-bit X11 ZPixmap requirements
        padded = processed.convert("RGBX")
        data = padded.tobytes()

    # Basically, what this X11-speak does is create an X11 Pixmap matching screen size and depth,
    pixmap = root.create_pixmap(width, height, depth)
    gc = root.create_gc()
    # Then, push the raw pixel data into the X server pixmap
    pixmap.put_image(gc, 0, 0, width, height, X.ZPixmap, depth, 0, data)
    # Next, apply the pixmap as the root window's background
    root.change_attributes(background_pixmap = pixmap)
    root.clear_window()
    # Update the X11 root window atoms so DEs and WMs recognize the new background
    atom_root_pmap = d.intern_atom('_XROOTPMAP_ID')
    atom_esetroot_pmap = d.intern_atom('ESETROOT_PM_ID')
    root.change_property(atom_root_pmap, X.XA_PIXMAP, 32, [pixmap.id])
    root.change_property(atom_esetroot_pmap, X.XA_PIXMAP, 32, [pixmap.id])
    d.sync()
    print(f'"{path}" used as wallpaper with {fit} style.')

def run(directory, fit, interval=600):
    if interval <= 0:
        raise ValueError("Interval must be positive!")
    # Loop through images in a folder and updates the wallpaper every {interval} seconds.
    validext = ('.jpg', '.jpeg', '.png', '.bmp')
    # Of course, {validext} isn't an exhaustive list of every image codec known to man, but those 4 (mentioned above) is what 90% of people use.
    if not os.path.isdir(directory):
        raise ValueError(f"{directory} not found.")

    while True:
        try:
            # Get all image files from the directory
            images = [
                os.path.join(directory, f)
                for f in os.listdir(directory)
                if f.lower().endswith(validext)
                and os.path.isfile(os.path.join(directory, f))
            ]
            if not images:
                print("No valid images found in the directory.")
            else:
                chosen = random.choice(images)
                setwp(chosen, fit)
        except Exception as e:
            print(f"An error occurred while setting the wallpaper: {e}")
        time.sleep(interval)
if __name__ == "__main__":
    wpdir = os.path.expanduser("~/Pictures/Wallpapers")
    rotint = 1200
    run(wpdir, "zoomed", rotint)