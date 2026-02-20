from flask import Flask, render_template, request, jsonify
import os
import time
import shutil
from detector_logic import process_video

app = Flask(__name__)

# Optimization: Ensure paths are relative to the script location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def setup_folders():
    """Initializes the upload directory, clearing previous session files."""
    if os.path.exists(UPLOAD_FOLDER):
        try:
            shutil.rmtree(UPLOAD_FOLDER)
        except Exception as e:
            print(f"Warning: Could not clear directory: {e}")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Run folder setup on startup
setup_folders()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # 1. Validation: Ensure file exists in request
    if 'video' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # 2. Path Management: Create unique filenames using timestamps
    ts = int(time.time())
    input_filename = f"in_{ts}.mp4"
    output_filename = f"out_{ts}.mp4"
    
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    
    try:
        # 3. Save input and process
        file.save(input_path)

        # process_video returns (results list, fps float)
        results, fps = process_video(input_path, output_path)
        
        # 4. Data Validation: Ensure frames were actually processed
        if not results:
            return jsonify({"error": "Video processing failed: No frames detected"}), 500

        # 5. Summary Calculation
        anomalies = [r for r in results if r['status'] != "Normal"]
        avg_gap = sum(r['gap'] for r in results) / len(results)
        
        summary = {
            "total_frames": len(results),
            "issues_found": len(anomalies),
            "avg_gap": round(avg_gap, 2),
            "fps": round(fps, 2)
        }
        
        return jsonify({
            "results": results,
            "summary": summary,
            "video_url": f"/static/uploads/{output_filename}"
        })
        
    except Exception as e:
        # Log the specific error to the console for debugging
        print(f"Server Error: {str(e)}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    # Debug mode is helpful for development, but remove in production
    app.run(debug=True, port=5000)