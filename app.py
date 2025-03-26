import os
import json
import exifread
from flask import Flask, request, redirect, url_for, jsonify, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
JSON_FILE = 'data.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file has a valid extension"""
    if '.' not in filename:
        return False  # No file extension found

    extension = filename.rsplit('.', 1)[1].lower()  # Extract file extension
    return extension in ALLOWED_EXTENSIONS  # Check if it's allowed


def extract_gps(image_path):
    with open(image_path, 'rb') as img_file:
        tags = exifread.process_file(img_file)
        if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
            lat_values = tags['GPS GPSLatitude'].values
            lon_values = tags['GPS GPSLongitude'].values
            lat = sum(float(val) / 60**i for i, val in enumerate(lat_values))
            lon = sum(float(val) / 60**i for i, val in enumerate(lon_values))
            return round(lat, 6), round(lon, 6)
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Extract form data
        description = request.form.get('description')
        lat, lon = request.form.get('latitude'), request.form.get('longitude')
        file = request.files.get('image')

        image_path = None  # Default to None in case no file is uploaded

        # Handle file upload
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(image_path)

            # Extract GPS coordinates from image
            gps = extract_gps(image_path)
            if gps:
                lat, lon = gps  # Use extracted GPS data if available

        # Create the report dictionary
        report = {"description": description, "image": image_path, "latitude": lat, "longitude": lon}

        # Load existing data and append new report
        try:
            with open(JSON_FILE, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []  # Initialize empty list if the file doesn't exist or is corrupt

        data.append(report)

        # Save updated data
        with open(JSON_FILE, 'w') as f:
            json.dump(data, f, indent=4)

        return redirect(url_for('success'))

    return render_template('index.html')


@app.route('/success')
def success():
    return "Report submitted successfully!"

@app.route('/reports')
def reports():
    try:
        with open(JSON_FILE, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
