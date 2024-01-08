from flask import Flask, render_template, request, jsonify
from roboflow import Roboflow
import base64
from PIL import Image, ImageDraw
from io import BytesIO
import easyocr
import cv2
import re
import os
import shutil
from difflib import SequenceMatcher
from keras.models import load_model
import numpy as np
import subprocess

app = Flask(__name__)



emblem_model = load_model(r"C:\Users\tharu\Desktop\v2\emblem.h5")
goi_model = load_model(r"C:\Users\tharu\Desktop\v2\goi.h5")
SIZE = 150
details_set={"aadharno":"False","details":"False","emblem":"False","goi":"False","image":"False","qr":"False"}
detect_set=set()


def run_yolo(image_path):
    # Replace this with the actual path to your YOLO model and configuration files
    yolo_path = 'path_to_your_yolo_files'
    yolo_command = f'yolo task=detect mode=predict model=best.pt show=true conf=0.5 source={image_path} save_crop=True'
    subprocess.run(yolo_command, shell=True)
    move_images()


def move_images():
    detect_folder = r'C:\Users\tharu\Desktop\v2\static\detect'
    static_folder = r'C:\Users\tharu\Desktop\v2\static'

    for root, dirs, files in os.walk(detect_folder):
        for file in files:
            if file.lower().endswith('.jpg'):  
                image_path = os.path.join(root, file)
                parent_folder = os.path.basename(os.path.dirname(image_path))
                detect_set.add(parent_folder)
                destination_path = os.path.join(static_folder, f"{parent_folder}.jpg")
                shutil.move(image_path, destination_path)

    print("Images moved successfully to the 'static' folder!")

    # Delete the 'detect' folder and its contents after moving the images
    shutil.rmtree(detect_folder)

    print("The 'detect' folder has been deleted.")

def delete_images():
    global details_set
    details_set={"aadharno":"False","details":"False","emblem":"False","goi":"False","image":"False","qr":"False"}
    for i,j in details_set.items():
        pth=f"static/{i}.jpg"
        if(os.path.exists(pth)):
            os.remove(pth)

def detect_emblem():
    image = cv2.imread("static/emblem.jpg")
    image = Image.fromarray(image, 'RGB')
    image = image.resize((SIZE, SIZE))
    image_array = np.array(image)  # Normalize the image data

    # Prepare the image for prediction
    input_image = np.expand_dims(image_array, axis=0)  # Add a batch dimension

    # Perform prediction
    prediction = emblem_model.predict(input_image)
    if prediction[0][0] > 0.5:
        return True
    else:
        return False
    


def detect_goi():
    # Load and preprocess the image
    image = cv2.imread("static/goi.jpg")
    image = Image.fromarray(image, 'RGB')
    image = image.resize((SIZE, SIZE))
    image_array = np.array(image)  # Normalize the image data

    # Prepare the image for prediction
    input_image = np.expand_dims(image_array, axis=0)  # Add a batch dimension

    # Perform prediction
    prediction = goi_model.predict(input_image)
    if prediction[0][0] > 0.5:
        return True
    else:
        return False
    

def detect_details(inputName):
    details_text=extraction_of_text('static/details.jpg')
    print(inputName)
    return compare_strings(details_text,inputName,0.4)


def detect_aadhar(inputAadhar):
    aadharno_text=extraction_of_text('static/aadharno.jpg')
    found_aadhar_number = aadhar_number_search(aadharno_text)
    print(inputAadhar)
    return compare_strings(found_aadhar_number,inputAadhar,0.7)

def detect_image():
    return True



def detect_qr():
    return True
    

def extraction_of_text(image):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image,paragraph=True)
    top_left = tuple(result[0][0][0])
    bottom_right = tuple(result[0][0][2])
    text = result[0][1]
    font = cv2.FONT_HERSHEY_SIMPLEX
    return text


def aadhar_number_search(text):
    aadhar_pattern = re.compile(r'\b\d{4}\s\d{4}\s\d{4}\b')
    match = aadhar_pattern.search(text)
    if match:
        return match.group()
    else:
        return None

def compare_strings(string1, string2, threshold):
    seq_matcher = SequenceMatcher(None, string1, string2)
    similarity_ratio = seq_matcher.ratio()

    if similarity_ratio >= threshold:
        return True
    else:
        return False 


@app.route('/')
def home():
    return render_template('some.html')
@app.route('/home')
def index():
    return render_template('home.html')

@app.route('/verify')
def verify():
    return render_template('index.html')

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    try:
        delete_images()
        inputName=request.json.get('inputName')
        inputAadhar=request.json.get('inputAadhar')
        inputNumber=request.json.get('inputNumber')

        print(inputName,inputAadhar,inputNumber)

        # Retrieve image data
        image_data_uri = request.json.get('image')
        

        # Extract base64-encoded part
        _, image_data_base64 = image_data_uri.split(',', 1)

        # Decode base64 image string
        image_bytes = base64.b64decode(image_data_base64)

        # Use BytesIO to create a stream from the image data
        image_stream = BytesIO(image_bytes)

        # Open the image using PIL
        image = Image.open(image_stream).convert('RGB')

        # Save the image to a file
        image.save("static/input_image.jpg")

        run_yolo("static/input_image.jpg")

        if("qr" in detect_set and detect_qr()): details_set["qr"]="True"
        if("aadharno" in detect_set and detect_aadhar(inputAadhar)): details_set["aadharno"]="True"
        if("details" in detect_set and  detect_details(inputName)):  details_set["details"]="True"
        if("image" in detect_set and  detect_image()): details_set["image"]="True"
        if("emblem" in detect_set and  detect_emblem()): details_set["emblem"]="True" 
        if("goi" in detect_set and  detect_goi()): details_set["goi"]="True"


        print(details_set)

        
        with open("static/predict.jpg", "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')


        return jsonify({"roboflow_result": base64_image,"details_set":details_set})

    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
