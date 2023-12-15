from flask import Flask, render_template, request, jsonify
from roboflow import Roboflow
import base64
from PIL import Image, ImageDraw
from io import BytesIO
import easyocr
import cv2
import re
# import pytesseract

app = Flask(__name__)

txtbbs = {}

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

        if(class_name == "aadharno" or class_name == "details"):
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

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/verify')
def verify():
    return render_template('index.html')

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    try:
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
        image.save("input_image.jpg")
        # from roboflow import Roboflow
        # my api key
        rf = Roboflow(api_key="2bwhxzy7AaegkJ9ubiIJ") 
        project = rf.workspace().project("docverify")
        model = project.version(1).model

        prediction_result = model.predict("input_image.jpg", confidence=40, overlap=30)

        # Get predictions from the JSON response
        predictions = prediction_result.json()["predictions"]
        print(predictions)
        details_set=[]
        for i in predictions:
            details_set.append(i['class'])
        print(details_set)
        # Overlay bounding boxes on the input image
        image_with_boxes = overlay_boxes(image.copy(), predictions)

        # Save the image with bounding boxes (optional)
        image_with_boxes.save("output_image.jpg")
        details_region = image.crop(txtbbs["details"])
        aadharno_region = image.crop(txtbbs["aadharno"])
        details_region.save("details.jpg")
        aadharno_region.save("aadharno.jpg")

        aadharno_text=extraction_of_text('aadharno.jpg')
        details_text=extraction_of_text('details.jpg')

        found_aadhar_number = aadhar_number_search(aadharno_text)
        print(aadharno_text)
        print(found_aadhar_number)
        print(details_text)

        with open("output_image.jpg", "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')


        return jsonify({"roboflow_result": base64_image,"aadharno":found_aadhar_number,"details_set":details_set})

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
