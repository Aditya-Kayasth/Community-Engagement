import os
import json
import exifread  # To extract GPS data from images
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from fractions import Fraction

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
JSON_FILE = 'data.json'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Check if the file type is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_gps_from_image(image_path):
    """Extract GPS coordinates from image metadata"""
    with open(image_path, 'rb') as img_file:
        tags = exifread.process_file(img_file)
        
        if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
            lat_values = tags['GPS GPSLatitude'].values
            lon_values = tags['GPS GPSLongitude'].values

            # Convert Fraction to float
            lat = float(lat_values[0]) + float(lat_values[1]) / 60 + float(lat_values[2]) / 3600
            lon = float(lon_values[0]) + float(lon_values[1]) / 60 + float(lon_values[2]) / 3600
            
            print(f"Extracted GPS: Latitude={lat}, Longitude={lon}")  # Debugging line
            
            return round(lat, 6), round(lon, 6)

    print("No GPS data found in image")  # Debugging line
    return None


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        description = request.form.get('description')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        file = request.files.get('image')

        image_path = None
        extracted_location = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(image_path)

            # Try extracting GPS data from image
            extracted_location = extract_gps_from_image(image_path)

        # If no GPS data, ask for browser location
        if not extracted_location:
            if not latitude or not longitude:
                return render_template('location.html', image=image_path, description=description)

        # Final location selection
            # Final location selection
        final_lat = extracted_location[0] if extracted_location else latitude
        final_lon = extracted_location[1] if extracted_location else longitude

        print(f"Final selected location: Latitude={final_lat}, Longitude={final_lon}")  # Debugging line


        report_data = {
            "description": description,
            "image": image_path,
            "latitude": final_lat,
            "longitude": final_lon
        }

        # Save data to JSON
        try:
            with open(JSON_FILE, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        data.append(report_data)

        with open(JSON_FILE, 'w') as f:
            json.dump(data, f, indent=4)

        return redirect(url_for('success'))

    return render_template('index.html')

@app.route('/location', methods=['POST'])
def location():
    """Handles location input after checking image metadata"""
    description = request.form.get('description')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    image = request.form.get('image')

    report_data = {
        "description": description,
        "image": image,
        "latitude": latitude,
        "longitude": longitude
    }

    print(f"Saving report: {report_data}")  # Debugging line


    # Save data to JSON
    try:
        with open(JSON_FILE, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append(report_data)

    with open(JSON_FILE, 'w') as f:
        json.dump(data, f, indent=4)

    return redirect(url_for('success'))

@app.route('/success')
def success():
    return render_template('success.html')

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
