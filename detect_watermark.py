#!/usr/bin/env python3
"""
水印检测脚本 - 基于几何角度过滤法
用于检测图片中的敏感水印（如飞书/钉钉水印）
"""
import sys
import os
import cv2
import numpy as np
import math
import re
from paddleocr import PaddleOCR

# ================= 配置 =================
# 角度阈值：如果文字倾斜超过这个度数，就被认为是水印
# 飞书/钉钉水印通常倾斜 30-45 度，设为 10 度非常安全
MIN_ANGLE_THRESHOLD = 10.0
# =======================================

def calculate_text_angle(box):
    """
    计算文本框的倾斜角度（相对于水平线）
    box 格式: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    取上方两点 (p0, p1) 计算斜率
    """
    p0, p1 = box[0], box[1]
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    # 使用 atan2 计算弧度，然后转角度
    angle_rad = math.atan2(dy, dx)
    angle_deg = math.degrees(angle_rad)
    return abs(angle_deg)

def preprocess_image(image_path):
    """
    预处理：只做最基础的【字体加粗】，不再去线，避免误伤
    """
    if not os.path.exists(image_path):
        return None
    img = cv2.imread(image_path)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 1. 强对比度 (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    # 2. 自适应二值化
    binary = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 35, 10
    )
    # 3. 字体加粗（修复虚线断裂）
    kernel = np.ones((2, 2), np.uint8)
    thickened = cv2.erode(binary, kernel, iterations=1)
    return thickened

def detect_watermark_in_image(image_path, ocr):
    """
    检测单个图片中的水印
    返回: (has_watermark, watermark_info)
    """
    print(f"[*] 检测图片：{image_path}")
    
    processed_img = preprocess_image(image_path)
    if processed_img is None:
        print(f"[Warning] 无法读取或处理图片: {image_path}")
        return False, None
    
    print(f"[*] 正在识别文字...")
    result = ocr.ocr(processed_img, cls=True)
    
    watermark_candidates = []
    if result and result[0]:
        for line in result[0]:
            box = line[0]        # 坐标
            text = line[1][0]    # 文本
            # 1. 计算角度
            angle = calculate_text_angle(box)
            # 2. 核心判断逻辑
            if angle > MIN_ANGLE_THRESHOLD:
                # === 是水印 (倾斜) ===
                print(f"  [发现疑似水印] 角度: {angle:.1f}° | 内容: {text}")
                watermark_candidates.append(text)
    
    if not watermark_candidates:
        print(f"✅ {image_path}: 未发现倾斜文字，图片安全。")
        return False, None
    
    # 把所有碎片拼成一个长字符串，方便正则查找
    full_text = " ".join(watermark_candidates)
    
    # === 核心逻辑：正则严格匹配 ===
    # 针对 "Jianjun Li 6719" 或 "Wang Zhang 1234"
    # 逻辑：[英文单词] + [可能的空格和更多单词] + [空格] + [4位数字]
    pattern = re.compile(r'([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+(\d{4})\b')
    matches = pattern.findall(full_text)
    
    if matches:
        print(f"🚨 {image_path}: DETECTED SENSITIVE WATERMARK 🚨")
        watermark_info = []
        for m in matches:
            name = m[0].strip()
            num = m[1]
            # 再次过滤掉太短的误判
            if len(name) > 3:
                info = f"姓名: {name} | 尾号: {num}"
                print(f"   {info}")
                watermark_info.append(info)
        return True, watermark_info
    else:
        print(f"⚠️ {image_path}: 发现倾斜文字，但未匹配到 [姓名+4位手机号] 格式")
        print(f"   原始识别内容: {full_text}")
        return False, None

def main():
    if len(sys.argv) < 2:
        print("Usage: python detect_watermark.py <image_file_or_directory>")
        sys.exit(1)
    
    target = sys.argv[1]
    
    print(f"[*] 启动水印检测分析")
    print(f"[*] 过滤逻辑：只保留倾斜角度 > {MIN_ANGLE_THRESHOLD}° 的文字")
    print(f"="*60)
    
    # 初始化 OCR (关闭日志)
    ocr = PaddleOCR(
        use_angle_cls=True,
        lang="en",
        det_db_thresh=0.05,
        det_db_unclip_ratio=2.5,
        show_log=False
    )
    
    # 收集要检测的图片
    image_files = []
    if os.path.isfile(target):
        image_files.append(target)
    elif os.path.isdir(target):
        for root, dirs, files in os.walk(target):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    image_files.append(os.path.join(root, file))
    else:
        print(f"[Error] 路径不存在: {target}")
        sys.exit(1)
    
    if not image_files:
        print("[*] 未找到任何图片文件")
        sys.exit(0)
    
    print(f"[*] 找到 {len(image_files)} 个图片文件")
    print(f"="*60)
    
    # 检测所有图片
    detected_watermarks = []
    for img_path in image_files:
        has_watermark, info = detect_watermark_in_image(img_path, ocr)
        if has_watermark:
            detected_watermarks.append((img_path, info))
        print()
    
    # 最终结果
    print(f"="*60)
    print("【检测结果汇总】")
    if detected_watermarks:
        print(f"🚨 发现 {len(detected_watermarks)} 个文件包含敏感水印 🚨")
        for img_path, info in detected_watermarks:
            print(f"\n文件: {img_path}")
            for line in info:
                print(f"  - {line}")
        sys.exit(1)  # 发现泄露，返回错误码 1 (阻断 CI)
    else:
        print("✅ 所有图片均未发现敏感水印")
        sys.exit(0)

if __name__ == "__main__":
    main()
