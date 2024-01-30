import datetime
from flask import Flask, request, send_file
from flask_cors import CORS
from PIL import Image, UnidentifiedImageError
import zipfile
import io

app = Flask(__name__)
CORS(app, resources={r"/api/resizeimage": {"origins": ["https://resizer.sn1316.com"]}})

@app.route('/api/resizeimage', methods=['POST'])
def resize_image():

    files = request.files.getlist('files')
    if not files:
        return "No files selected"
        
    if len(request.files) == 0:
        return "No file selected"
    
    max_size_str = request.form.get('max_size')  
    quality_str = request.form.get('quality')

    logmessage(f"Max Size: {max_size_str}")
    logmessage(f"Image Quality: {quality_str}")
    logmessage(f"Number of Images: {len(files)}")
    logmessage(f"Test")

    if not validate_input(max_size_str, quality_str):
        return "Input validation failed"
    
    max_size = int(max_size_str)
    quality = int(quality_str)
    
    zip_data = io.BytesIO()
    with zipfile.ZipFile(zip_data, 'w') as zipf:
        for file in files:
            if file.filename == '':
                continue
            
            if not allowed_file(file.filename):
                return "You can only upload images"
        
            try:
                logmessage(f"File: {file.filename}")
                image = Image.open(file)
            
                resized_image = resize(image, max_size)
                
                img_data = io.BytesIO()
                resized_image.save(img_data, format=image.format, quality=quality)
                
                zipf.writestr(file.filename, img_data.getvalue())
            except Exception as e:
                if isinstance(e, UnidentifiedImageError):
                    print(f"Skipping {file.filename}: Unable to identify image file")
                else:
                    print(f"Skipping {file.filename}: {e}")
    # Move the BytesIO cursor to the beginning
    zip_data.seek(0)
    
    # Return the zip file for download
    response = send_file(zip_data, mimetype='application/zip', as_attachment=True, download_name="resized_images.zip")
    response.headers["x-filename"] = "resized_images.zip"
    response.headers["Access-Control-Expose-Headers"] = 'x-filename'    
    return response    

# Function to check allowed file extensions
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to resize the image
def resize(image, max_size):
    
    width, height = image.size
    
    if width > max_size or height > max_size:
        # Resize the image to fit within the maximum size
        if width > height:
            logmessage("Resizing (Height)")
            ratio = max_size / width
            new_width = max_size
            new_height = int(height * ratio)
            if new_height < 1:
                new_height = 1
            return image.resize((new_width, new_height), Image.LANCZOS)
        else:
            logmessage("Resizing (Width)")
            ratio = max_size / height
            new_height = max_size
            new_width = int(width * ratio)
            if new_width < 1:
                new_width = 1
            return image.resize((new_width, new_height), Image.LANCZOS)
    
    return image


# Function to validate the inputs
def validate_input(max_size_str, quality_str):
    if not max_size_str:
        logmessage("Max size not provided. Please specify a value.")
        return False
    try:
        max_size = int(max_size_str) 
    except ValueError:
        logmessage("Invalid max_size value. Please provide a valid number.")
        return False
    if max_size > 2048:
        logmessage("Max size cannot be greater than 2048")
        return False
    if max_size < 1:
        logmessage("Max size cannot be less than 1")
        return False
    if not quality_str:
        logmessage("Quality not provided. Please specify a value.")
        return False
    try:
        quality = int(quality_str) 
    except ValueError:
        logmessage("Invalid quality value. Please provide a valid number.")
        return False
    if quality > 100:
        logmessage("Quality cannot be greater than 100")
        return False
    if quality < 1:
        logmessage("Quality cannot be less than 1")
        return False
    return True

def logmessage(message):
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S +0000")
    print("[{}] [L] [LOG ] {}".format(timestamp, message))

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)