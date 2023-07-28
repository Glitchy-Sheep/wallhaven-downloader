import os
import sys

import colorama
from PIL import Image
from colorama import Fore

IMAGE_EXTENSIONS = ["png", "jpg", "jpeg"]

colorama.init()
Image.MAX_IMAGE_PIXELS = None  # disable resolution warnings


def check_image_files(root_folder):
    for root, dirs, files in os.walk(root_folder):
        for filename in files:
            ext = filename.split(".")[-1]
            if ext in IMAGE_EXTENSIONS:
                try:
                    img = Image.open(os.path.join(root, filename))
                    img.verify()
                except (IOError, SyntaxError) as e:
                    print(f"{Fore.RED} Bad file:", os.path.join(root, filename))


root_folder = sys.argv[1]

if not os.path.isdir(root_folder):
    print("Invalid folder path")
else:
    check_image_files(root_folder)
