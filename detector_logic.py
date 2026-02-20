import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import subprocess
import os

def format_timestamp(ms):
    minutes = int(ms // 60000)
    seconds = int((ms % 60000) // 1000)
    millis = int(ms % 1000)
    return f"{minutes:02}:{seconds:02}.{millis:03}"

def reencode_for_web(path):
    """
    Forces the video into H.264 format with 'faststart' 
    so it plays immediately in web browsers.
    """
    temp_path = path.replace(".mp4", "_temp.mp4")
    cmd = [
        'ffmpeg', '-y', '-i', path,
        '-c:v', 'libx264', # Browser standard codec
        '-pix_fmt', 'yuv420p', # Ensures compatibility with Windows/Quicktime
        '-movflags', 'faststart', # Moves metadata to the start for web streaming
        temp_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        os.replace(temp_path, path)
        print("FFmpeg: Video successfully optimized for web.")
    except Exception as e:
        print(f"FFmpeg Error: {e}")

def process_video(input_path, output_path):
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    expected_delta = (1000.0 / fps) if fps > 0 else 0.0
    jitter_threshold = expected_delta * 1.3 
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # We save a temporary raw file first
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    results = []
    prev_gray, prev_ts, idx = None, 0, 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        curr_ts = cap.get(cv2.CAP_PROP_POS_MSEC)
        small_frame = cv2.resize(frame, (320, 240))
        curr_gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        
        status, color = "Normal", (0, 255, 0)
        time_gap = 0
        motion_score = 1.0

        if idx > 0:
            time_gap = curr_ts - prev_ts
            motion_score = ssim(prev_gray, curr_gray)
            
            if time_gap > jitter_threshold:
                status, color = "Frame Drop/Lag", (0, 0, 255)
            elif motion_score > 0.985:
                status, color = "Frozen/Merge", (0, 165, 255)

        # Draw Overlay
        cv2.rectangle(frame, (10, 10), (460, 65), (0, 0, 0), -1)
        cv2.putText(frame, f"{format_timestamp(curr_ts)} | {status}", (20, 45), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        out.write(frame)
        results.append({
            "frame": idx,
            "timestamp": round(curr_ts, 2),
            "gap": round(time_gap, 2),
            "status": status
        })

        prev_gray, prev_ts = curr_gray, curr_ts
        idx += 1

    cap.release()
    out.release()

    # CRITICAL: Re-encode the video so the browser can actually display it
    reencode_for_web(output_path)

    return results, fps