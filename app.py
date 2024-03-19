import json
import os
import uuid
from http.client import HTTPException

from flask import Flask, request, send_from_directory, after_this_request
from werkzeug.utils import secure_filename

# Assuming your backend.db and backend.main modules are compatible with Flask or don't need specific adaptations.
from backend.db import db_api
import backend.main

app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "*"}})  # 仅用于示例，实际部署时应限制为真实的前端地址

UPLOAD_FOLDER = db_api.get_temp_dir()
ALLOWED_EXTENSIONS = {'mp4', 'mov'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/remove-watermark', methods=['POST'])
def remove_watermark():
    """
    :param file 视频
    :param area 区域 (startY, endY, startX, endX)
    """
    print("start inference")
    if 'file' not in request.files:
        raise HTTPException(400, 'No selected file')
    file = request.files['file']
    area = request.form['area']
    print(area)
    remove_type = request.form['remove_type'] #water_mask | subtitle
    if remove_type is None:
        remove_type = 'water_mask'
    if remove_type == 'water_mask':
        sttn_skip_detection = True
    else:
        sttn_skip_detection = False

    if file.filename == '':
        raise HTTPException(400, 'No selected file')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"temp_{uuid.uuid4()}.{filename.rsplit('.', 1)[1].lower()}"
        temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        file.save(temp_filepath)
        area_list = json.loads(area)
        subtitle_area = (area_list[0], area_list[1], area_list[2], area_list[3])

        try:
            print(subtitle_area)
            output_file = backend.main.SubtitleRemover(temp_filepath, subtitle_area, sttn_skip_detection=sttn_skip_detection).run()

            @after_this_request
            def remove_file(response):
                os.remove(temp_filepath)
                return response

            return send_from_directory(directory=os.path.dirname(output_file),
                                       path=os.path.basename(output_file),
                                       as_attachment=True)
        except Exception as e:
            print(e)
            raise HTTPException(500, str(e))
    else:
        raise HTTPException(500, "Invalid file type.")

@app.route('/')
def main():
    return {"message": "Welcome to the watermark removal API!"}

if __name__ == "__main__":
    print(f"run in prot 8000 start")
    app.run(host='0.0.0.0', port=8000, debug=True)
    print(f"run in prot 8000 success")
