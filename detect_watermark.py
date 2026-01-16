#!/usr/bin/env python3
"""
Watermark Detection Script - Geometric Angle Filtering Method
Detects sensitive watermarks (e.g., Feishu/DingTalk) in images
"""
import sys
import os
import cv2
import numpy as np
import math
import re
from paddleocr import PaddleOCR

# ================= Configuration =================
# Angle threshold: text tilted beyond this degree is considered watermark
# Feishu/DingTalk watermarks are typically tilted 30-45 degrees, 10 degrees is very safe
MIN_ANGLE_THRESHOLD = 10.0
# =======================================

def calculate_text_angle(box):
    """
    Calculate the tilt angle of text box (relative to horizontal line)
    box format: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    Take the top two points (p0, p1) to calculate slope
    """
    p0, p1 = box[0], box[1]
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    # Use atan2 to calculate radians, then convert to degrees
    angle_rad = math.atan2(dy, dx)
    angle_deg = math.degrees(angle_rad)
    return abs(angle_deg)

def preprocess_image(image_path):
    """
    Preprocessing: Only basic [font thickening], no line removal to avoid false positives
    """
    if not os.path.exists(image_path):
        return None
    img = cv2.imread(image_path)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 1. Strong contrast (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    # 2. Adaptive binarization
    binary = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 35, 10
    )
    # 3. Font thickening (fix dashed line breaks)
    kernel = np.ones((2, 2), np.uint8)
    thickened = cv2.erode(binary, kernel, iterations=1)
    return thickened

def detect_watermark_in_image(image_path, ocr):
    """
    Detect watermark in a single image
    Returns: (has_watermark, watermark_info)
    """
    print(f"[*] Checking image: {image_path}")
    
    processed_img = preprocess_image(image_path)
    if processed_img is None:
        print(f"[Warning] Unable to read or process image: {image_path}")
        return False, None
    
    print(f"[*] Recognizing text...")
    result = ocr.ocr(processed_img, cls=True)
    
    watermark_candidates = []
    if result and result[0]:
        for line in result[0]:
            box = line[0]        # Coordinates
            text = line[1][0]    # Text
            # 1. Calculate angle
            angle = calculate_text_angle(box)
            # 2. Core judgment logic
            if angle > MIN_ANGLE_THRESHOLD:
                # === Is watermark (tilted) ===
                print(f"  [Suspicious watermark] Angle: {angle:.1f}° | Content: {text}")
                watermark_candidates.append(text)
    
    if not watermark_candidates:
        print(f"✅ {image_path}: No tilted text found, image is safe.")
        return False, None
    
    # Concatenate all fragments into a long string for regex search
    full_text = " ".join(watermark_candidates)
    
    # === Core logic: Strict regex matching ===
    # For "Jianjun Li 6719" or "Wang Zhang 1234"
    # Logic: [English words] + [possible spaces and more words] + [space] + [4 digits]
    pattern = re.compile(r'([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+(\d{4})\b')
    matches = pattern.findall(full_text)
    
    if matches:
        print(f"🚨 {image_path}: DETECTED SENSITIVE WATERMARK 🚨")
        watermark_info = []
        for m in matches:
            name = m[0].strip()
            num = m[1]
            # Filter out false positives that are too short
            if len(name) > 3:
                info = f"Name: {name} | Number: {num}"
                print(f"   {info}")
                watermark_info.append(info)
        return True, watermark_info
    else:
        print(f"⚠️ {image_path}: Found tilted text, but no [Name+4-digit number] pattern matched")
        print(f"   Original recognized content: {full_text}")
        return False, None

def main():
    if len(sys.argv) < 2:
        print("Usage: python detect_watermark.py <image_file_or_directory>")
        sys.exit(1)
    
    target = sys.argv[1]
    
    print(f"[*] Starting watermark detection analysis")
    print(f"[*] Filtering logic: Only keep tilted text > {MIN_ANGLE_THRESHOLD}°")
    print(f"="*60)
    
    # Initialize OCR (disable logs)
    ocr = PaddleOCR(
        use_angle_cls=True,
        lang="en",
        det_db_thresh=0.05,
        det_db_unclip_ratio=2.5,
        show_log=False
    )
    
    # Collect images to detect
    image_files = []
    if os.path.isfile(target):
        image_files.append(target)
    elif os.path.isdir(target):
        for root, dirs, files in os.walk(target):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    image_files.append(os.path.join(root, file))
    else:
        print(f"[Error] Path does not exist: {target}")
        sys.exit(1)
    
    if not image_files:
        print("[*] No image files found")
        sys.exit(0)
    
    print(f"[*] Found {len(image_files)} image file(s)")
    print(f"="*60)
    
    # Detect all images
    detected_watermarks = []
    for img_path in image_files:
        has_watermark, info = detect_watermark_in_image(img_path, ocr)
        if has_watermark:
            detected_watermarks.append((img_path, info))
        print()
    
    # Final result
    print(f"="*60)
    print("【Detection Result Summary】")
    if detected_watermarks:
        print(f"🚨 Found {len(detected_watermarks)} file(s) containing sensitive watermarks 🚨")
        for img_path, info in detected_watermarks:
            print(f"\nFile: {img_path}")
            for line in info:
                print(f"  - {line}")
        sys.exit(1)  # Found leak, return error code 1 (block CI)
    else:
        print("✅ All images passed, no sensitive watermarks found")
        sys.exit(0)

if __name__ == "__main__":
    main()
