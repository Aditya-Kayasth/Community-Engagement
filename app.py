import os
import json
import exifread
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
JSON_FILE = 'data.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

categories = [
    "Environmental Issues",
    "Deforestation",
    "Illegal Wildlife Trade",
    "Air Pollution",
    "Water Pollution",
    "Plastic Waste Management",
    "Climate Change",
    "Industrial Waste Dumping",
    "Ocean Conservation",
    "E-Waste Management",
    "Land Degradation",
    "Animal Welfare",
    "Animal Cruelty & Abuse",
    "Wildlife Conservation",
    "Stray Animal Rescue",
    "Illegal Poaching",
    "Animal Testing in Labs",
    "Marine Life Protection",
    "Zoo and Captivity Exploitation"
]

def allowed_file(filename):
    """Check if the file extension is allowed."""
    if "." not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def extract_gps(image_path):
    """Extract GPS coordinates from image metadata."""
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
        category = request.form.get('category')
        description = request.form.get('description')
        lat = request.form.get('latitude')
        lon = request.form.get('longitude')
        file = request.files.get('image')

        image_path = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(image_path)
            gps = extract_gps(image_path)
            if gps:
                lat, lon = gps

        report = {
            "category": category,
            "description": description,
            "image": image_path,
            "latitude": lat,
            "longitude": lon
        }

        try:
            with open(JSON_FILE, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        data.append(report)

        with open(JSON_FILE, 'w') as f:
            json.dump(data, f, indent=4)

        return redirect(url_for('success'))

    return render_template('index.html', categories=categories)

@app.route('/success')
def success():
    return "<h2>Report submitted successfully!</h2><a href='/'>Submit another report</a>"

@app.route('/reports')
def reports():
    """View stored reports"""
    try:
        with open(JSON_FILE, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)




