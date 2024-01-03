# from ultralytics import settings

# # Update a setting
# settings.update({'runs_dir': r'C:\Users\tharu\Desktop\v2\static'})

import os
import shutil

detect_folder = r'C:\Users\tharu\Desktop\v2\static\detect'
static_folder = r'C:\Users\tharu\Desktop\v2\static'

for root, dirs, files in os.walk(detect_folder):
    for file in files:
        if file.lower().endswith('.jpg'):  # Consider only JPG files
            image_path = os.path.join(root, file)
            parent_folder = os.path.basename(os.path.dirname(image_path))

            destination_path = os.path.join(static_folder, f"{parent_folder}.jpg")
            shutil.move(image_path, destination_path)

print("Images moved successfully to the 'static' folder!")

# Delete the 'detect' folder and its contents after moving the images
shutil.rmtree(detect_folder)

print("The 'detect' folder has been deleted.")
