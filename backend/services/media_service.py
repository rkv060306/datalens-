import os
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any
from PIL import Image, ImageStat

class MediaService:
    @staticmethod
    def analyze_image(file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            return {"error": "Image file not found"}

        try:
            with Image.open(path) as img:
                width, height = img.size
                format_str = img.format
                mode = img.mode
                aspect_ratio = round(width / height, 2) if height > 0 else 0

                # Brightness & Contrast
                grayscale = img.convert('L')
                stat = ImageStat.Stat(grayscale)
                mean_brightness = round(stat.mean[0], 2)
                contrast = round(stat.stddev[0], 2)

                # Color Histograms using OpenCV
                cv_img = cv2.imread(str(path))
                dominant_colors = []
                if cv_img is not None:
                    # Calculate RGB channel averages
                    b_avg = float(np.mean(cv_img[:, :, 0]))
                    g_avg = float(np.mean(cv_img[:, :, 1]))
                    r_avg = float(np.mean(cv_img[:, :, 2]))

                    dominant_colors = [
                        {"color": "Red", "value": round(r_avg, 1)},
                        {"color": "Green", "value": round(g_avg, 1)},
                        {"color": "Blue", "value": round(b_avg, 1)}
                    ]

                # Basic OCR check using OpenCV / fallback string
                ocr_text = "No text detected"
                try:
                    import pytesseract
                    ocr_text = pytesseract.image_to_string(img).strip() or "No text detected"
                except Exception:
                    pass

                return {
                    "mediaType": "Image",
                    "width": width,
                    "height": height,
                    "aspectRatio": aspect_ratio,
                    "format": format_str,
                    "mode": mode,
                    "brightness": mean_brightness,
                    "contrast": contrast,
                    "dominantColors": dominant_colors,
                    "ocrDetectedText": ocr_text,
                    "qualityScore": 95 if contrast > 30 else 75
                }
        except Exception as e:
            return {"error": f"Error analyzing image: {str(e)}"}

    @staticmethod
    def analyze_video(file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            return {"error": "Video file not found"}

        try:
            cap = cv2.VideoCapture(str(path))
            if not cap.isOpened():
                return {"error": "Could not open video file"}

            fps = float(cap.get(cv2.CAP_PROP_FPS))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration_sec = round(frame_count / fps, 2) if fps > 0 else 0.0

            # Sample brightness / motion intensity across frames
            frame_brightness = []
            sample_step = max(1, frame_count // 10)
            
            for f_idx in range(0, frame_count, sample_step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
                ret, frame = cap.read()
                if ret:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    frame_brightness.append(round(float(np.mean(gray)), 2))

            cap.release()

            return {
                "mediaType": "Video",
                "width": width,
                "height": height,
                "fps": round(fps, 2),
                "totalFrames": frame_count,
                "durationSeconds": duration_sec,
                "sampledBrightnessTimeline": frame_brightness,
                "qualityScore": 90 if fps >= 24 else 70
            }
        except Exception as e:
            return {"error": f"Error analyzing video: {str(e)}"}

media_service = MediaService()
