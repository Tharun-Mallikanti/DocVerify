from flask import Flask, render_template, request, jsonify
from roboflow import Roboflow
import base64
from PIL import Image, ImageDraw
from io import BytesIO
import easyocr
import cv2
import re
from difflib import SequenceMatcher
from keras.models import load_model
import numpy as np

app = Flask(__name__)



txtbbs = {"aadharno":[0,0,0,0],"goi":[0,0,0,0],"details":[0,0,0,0],"image":[0,0,0,0],"qr":[0,0,0,0],"emblem":[0,0,0,0]}
emblem_model = load_model(r"C:\Users\tharu\Desktop\v2\emblem.h5")
goi_model = load_model(r"C:\Users\tharu\Desktop\v2\goi.h5")
SIZE = 150



def detect_emblem(image):
    emblem_region =image.crop(txtbbs["emblem"])
    emblem_region.save("static/emblem.jpg")

    # Load and preprocess the image
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
    


def detect_goi(image):
    goi_region =image.crop(txtbbs["goi"])
    goi_region.save("static/goi.jpg")
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
    

def detect_details(image,inputName):
    details_region = image.crop(txtbbs["details"])
    details_region.save("static/details.jpg")

    details_text=extraction_of_text('static/details.jpg')
    print(inputName)
    return compare_strings(details_text,inputName,0.4)


def detect_aadhar(image,inputAadhar):
    aadharno_region = image.crop(txtbbs["aadharno"])
    aadharno_region.save("static/aadharno.jpg")

    aadharno_text=extraction_of_text('static/aadharno.jpg')
    found_aadhar_number = aadhar_number_search(aadharno_text)
    print(inputAadhar)
    return compare_strings(found_aadhar_number,inputAadhar,0.7)

def detect_image(image):
    image_region =image.crop(txtbbs["image"])
    image_region.save("static/image.jpg")
    return True



def detect_qr(image):
    qr_region =image.crop(txtbbs["qr"])
    qr_region.save("static/qr.jpg")
    return True
    

def overlay_boxes(image, predictions):
    draw = ImageDraw.Draw(image)
    for prediction in predictions:
        width, height = image.size
        x_center, y_center, w, h = (
            prediction["x"],
            prediction["y"],
            prediction["width"],
            prediction["height"],
        )
        x, y = x_center - w / 2, y_center - h / 2  # Calculate top-left coordinates
        class_name = prediction["class"]

        # Set background color based on class
        class_colors = {
            "details": "blue",
            "qr": "green",
            "image": "black",
            "aadharno": "red",
            "goi": "purple",
            "emblem": "orange",
        }
        txtbbs[class_name] = [x, y, x + w, y + h]
        # Draw thick filled rectangle as background
        draw.rectangle([x, y, x + w, y + h], outline=class_colors.get(class_name, "white"), width=2)

        # Draw class name on top-left corner in white
        draw.rectangle([x, y, x+50, y+20], fill=class_colors.get(class_name, "white"))
        draw.text((x, y), class_name, fill="white")
    print(txtbbs)
    return image

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
def index():
    return render_template('home.html')

@app.route('/verify')
def verify():
    return render_template('index.html')

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    try:

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
        # from roboflow import Roboflow
        # my api key
        # rf = Roboflow(api_key="2bwhxzy7AaegkJ9ubiIJ") 
        # project = rf.workspace().project("docverify")
        # model = project.version(1).model


        rf = Roboflow(api_key="RMzZna7r8BabI0Fz7SJV")
        project = rf.workspace().project("aadhardetection")
        model = project.version(3).model

        prediction_result = model.predict("static/input_image.jpg", confidence=40, overlap=30)

        # Get predictions from the JSON response
        predictions = prediction_result.json()["predictions"]
        # print(predictions)
        details_set={}
        for i in predictions:
            details_set[i['class']]="False"
        print(details_set)
        # Overlay bounding boxes on the input image
        image_with_boxes = overlay_boxes(image.copy(), predictions)

        # Save the image with bounding boxes (optional)
        image_with_boxes.save("static/output_image.jpg")

        if(sum(txtbbs["qr"])!=0 and detect_qr(image)): details_set["qr"]="True"
        if(sum(txtbbs["aadharno"])!=0 and detect_aadhar(image,inputAadhar)): details_set["aadharno"]="True"
        if(sum(txtbbs["details"])!=0 and  detect_details(image,inputName)):  details_set["details"]="True"
        if(sum(txtbbs["image"])!=0 and  detect_image(image)): details_set["image"]="True"
        if(sum(txtbbs["emblem"])!=0 and  detect_emblem(image)): details_set["emblem"]="True" 
        if(sum(txtbbs["goi"])!=0 and  detect_goi(image)): details_set["goi"]="True"


        print(details_set)

        
        with open("static/output_image.jpg", "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')


        return jsonify({"roboflow_result": base64_image,"details_set":details_set})

    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
