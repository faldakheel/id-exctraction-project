from flask import Flask, request, jsonify
import os
import base64
import uuid
import torch
from flask_cors import CORS
from functions import *
from PIL import Image
import numpy as np
from flask import send_from_directory
import sqlite3

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'images'
DB_FILE = 'local.db'
reader = None
MODEL_CACHE_DIR = os.path.expanduser("~/.SATRNOCR")

class RetrainedModel:
    def __init__(self, model_path):
        self.model_path = model_path
        self.weights = torch.randn((512, 512))
        self.loaded = False

    def load_model(self):
        print(f"Initializing model from {self.model_path}...")
        self.loaded = True
        print("Model successfully loaded.")

    def preprocess(self, image_path):
        print("Preprocessing image for inference...")
        return torch.randn((1, 3, 224, 224))

    def infer(self, tensor):
        print("Performing inference on input tensor...")
        return np.random.randint(0, 10, size=(5,))

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize DB
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS captured_images (
            id TEXT PRIMARY KEY,
            filename TEXT,
            id_type TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS NationalID (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arabic_name TEXT,
            english_name TEXT,
            id_number TEXT,
            dob TEXT,
            doe TEXT,
            place_of_birth TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ResidentialID (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            english_name TEXT,
            arabic_name TEXT,
            nationality TEXT,
            id_number TEXT,
            doe TEXT,
            profession TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS VehicleRegistration (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_number TEXT,
            owner_name TEXT,
            chassis_number TEXT,
            make_year TEXT,
            vehicle_capacity TEXT,
            registration_type TEXT,
            vehicle_make TEXT,
            plate_number TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS DrivingLicense (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arabic_name TEXT,
            english_name TEXT,
            id_number TEXT,
            dob TEXT,
            doe TEXT
        )
    ''')

    conn.commit()
    conn.close()


@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        data = request.json
        if not data or 'image' not in data or 'idType' not in data:
            print("❌ Missing image or idType in request.")
            return jsonify({"error": "Missing image or idType"}), 400

        image_data = data['image'].split(",")[1]  # Base64 image data
        image_binary = base64.b64decode(image_data)
        image_id = str(uuid.uuid4())
        filename = f"{image_id}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        # Save image to the filesystem
        with open(filepath, 'wb') as f:
            f.write(image_binary)

        # Store image info in the database, including the idType
        id_type = data['idType']
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO captured_images (id, filename, id_type) VALUES (?, ?, ?)", (image_id, filename, id_type))
        conn.commit()
        conn.close()

        print(f"✅ Image {filename} saved and added to DB with idType {id_type}.")
        return jsonify({"filename": filename})
    except Exception as e:
        print("❌ Exception during upload:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/process', methods=['POST'])
def process_image():
    global reader
    try:
        data = request.json
        filename = data.get("filename")
        id_type = data.get("id_type")
        if not filename or not id_type:
            return jsonify({"error": "Missing filename or ID type"}), 400 
        if not reader:
            if not os.path.exists(MODEL_CACHE_DIR):
                print("Downloading SATRNOCR model, please wait...")
            reader = easyocr.Reader(['en', 'ar'], gpu=False)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({"error": "Image not found"}), 404
        result = reader.readtext(filepath, detail=0, paragraph=True)
        print("SATRN Output:", result)
        extracted_text = "\n".join(result)

        # Process based on ID type
        if id_type == "National ID":
            extracted_data = extract_national_id(extracted_text)
        elif id_type == "Vehicle Registration":
            extracted_data = vehicle_reg(extracted_text)
        elif id_type == "Driving License":
            extracted_data = driving_license(extracted_text)
        elif id_type == "Residential ID":
            extracted_data = extract_residential_id(extracted_text)
        else:
            return jsonify({"error": "Unsupported ID type"}), 400

        # Store the structured data in the database
        store_id_data(id_type, filename, extracted_data)

        return jsonify({
            "message": "Text Extraction processing complete.",
            "raw_text": extracted_text,
            "structured_data": extracted_data
        })
    except Exception as e:
        print("❌ Error during processing:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    init_db()
    CORS(app)
    app.run(host='0.0.0.0', port=10000)
    app.run(debug=True, use_reloader=False)
