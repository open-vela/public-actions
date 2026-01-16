# Watermark Detection - Complete Guide

## Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Core Principles](#core-principles)
4. [Docker Setup](#docker-setup)
5. [Usage](#usage)
6. [CI/CD Integration](#cicd-integration)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Performance](#performance)

---

## Overview

Automated watermark detection system for CI/CD pipelines that prevents sensitive watermarks (e.g., Feishu/DingTalk personal watermarks) from being committed to repositories.

### Key Features
- ✅ **Geometric Angle Filtering**: Detects tilted watermarks (>10°) using OCR
- ✅ **Docker-based**: Pre-built image with all dependencies (~10x faster)
- ✅ **Automatic**: Runs on every PR with image changes
- ✅ **Accurate**: Pattern matching for "Name + 4-digit number" format
- ✅ **Efficient**: Only scans changed images in PRs

### Architecture
```
PR with Images → Detect Changes → Pull Docker Image → OCR Analysis
                                                           ↓
                                                    Angle Calculation
                                                           ↓
                                                    Pattern Matching
                                                           ↓
                                              Watermark Found? → ❌ Block PR
                                                           ↓
                                                          No → ✅ Pass
```

---

## Quick Start

### For Repository Owners

**Step 1: Add Workflow**

Create `.github/workflows/checkpatch.yml`:

```yaml
name: checkpatch

on:
  pull_request:
    types: [opened, reopened, synchronize]

jobs:
  checkpatch:
    uses: YOUR_USERNAME/public-actions/.github/workflows/checkpatch.yml@dev
    secrets: inherit
```

**Step 2: Make Docker Image Public**

1. Go to `https://github.com/YOUR_USERNAME?tab=packages`
2. Click on `watermark-detector` package
3. Package settings → Change visibility → Public

**Done!** Watermark detection now runs automatically on all PRs.

### For Developers

**Local Testing:**

```bash
# Using Docker (recommended)
docker run --rm -v "$(pwd):/workspace" \
  ghcr.io/YOUR_USERNAME/watermark-detector:latest image.jpg

# Using Python script
python detect_watermark.py image.jpg
```

---

## Core Principles

### The Problem
Office software (Feishu, DingTalk) adds personal watermarks to screenshots:
- Contains employee name + phone number
- Tilted at 30-45° for anti-forgery
- Can leak sensitive information when shared publicly

### The Solution
**Geometric Angle Filtering Method:**

1. **Architecture Content**: Horizontal (0°) or vertical (90°) text
   - Diagrams must be aligned for readability
   
2. **Watermark Text**: Tilted at 30-45°
   - Designed to cover entire image
   - Cannot be easily removed

3. **Detection Logic**:
   ```
   Extract all text → Calculate angles → Filter tilted text (>10°)
   → Pattern match "Name + 4 digits" → Report if found
   ```

### Why This Works
- **Stable**: Based on physical geometry, not colors/brightness
- **Accurate**: Architecture diagrams are always horizontal/vertical
- **Robust**: Watermarks must be tilted to be effective
- **Unavoidable**: This contradiction is fundamental

---

## Docker Setup

### Automatic Build

Docker images are automatically built when:
- `detect_watermark.py` is modified
- `Dockerfile.watermark` is modified
- Pushed to `dev` or `trunk` branch

### Image Details

**Base Image:** `python:3.10-slim`

**Pre-installed:**
- opencv-python-headless 4.8.1.78
- numpy 1.24.3
- paddlepaddle 2.6.2
- paddleocr 2.7.3
- PaddleOCR models (pre-downloaded):
  - en_PP-OCRv3_det_infer (detection)
  - en_PP-OCRv4_rec_infer (recognition - latest)
  - ch_ppocr_mobile_v2.0_cls_infer (angle classification)

**Image Tags:**
- `latest` - Latest stable (dev branch, default)
- `trunk` - Trunk branch version
- `dev-<sha>` - Specific commit from dev branch

**Registry:** `ghcr.io/YOUR_USERNAME/watermark-detector`

### Manual Build

```bash
# Build locally
docker build -f Dockerfile.watermark -t watermark-detector .

# Test
docker run --rm -v "$(pwd):/workspace" watermark-detector test.jpg

# Push to registry
docker tag watermark-detector ghcr.io/YOUR_USERNAME/watermark-detector:latest
docker push ghcr.io/YOUR_USERNAME/watermark-detector:latest
```

---

## Usage

### Command Line

**Single Image:**
```bash
python detect_watermark.py image.jpg
```

**Directory:**
```bash
python detect_watermark.py ./images/
```

**Docker:**
```bash
docker run --rm -v "$(pwd):/workspace" \
  ghcr.io/YOUR_USERNAME/watermark-detector:latest image.jpg
```

### GitHub Actions

**Method 1: Reusable Workflow (Recommended)**
```yaml
jobs:
  checkpatch:
    uses: YOUR_USERNAME/public-actions/.github/workflows/checkpatch.yml@dev
    secrets: inherit
```

**Method 2: Direct Docker**
```yaml
- name: Check Watermark
  run: |
    docker run --rm -v "$(pwd):/workspace" \
      ghcr.io/YOUR_USERNAME/watermark-detector:latest image.jpg
```

**Method 3: GitHub Action**
```yaml
- uses: YOUR_USERNAME/public-actions/.github/actions/watermark-check@dev
  with:
    image-path: 'image.jpg'
```

### Output Examples

**✅ Safe Image:**
```
[*] Starting watermark detection
[*] Filtering logic: Only tilted text > 10°
[*] Detecting image: diagram.png
[*] Recognizing text...
✅ diagram.png: No tilted text found, image is safe.
```

**❌ Watermark Detected:**
```
[*] Starting watermark detection
[*] Detecting image: screenshot.jpg
[*] Recognizing text...
  [Suspicious watermark] Angle: 35.2° | Content: Jianjun Li
  [Suspicious watermark] Angle: 35.1° | Content: 6719
🚨 screenshot.jpg: DETECTED SENSITIVE WATERMARK 🚨
   Name: Jianjun Li | Number: 6719
```

---

## CI/CD Integration

### Workflow Integration

The watermark check is integrated into `checkpatch.yml`:

```yaml
- name: Check Watermark in Images
  run: |
    cd ${{ env.REPO_NAME }}
    commits="${{ github.event.pull_request.base.sha }}..HEAD"
    
    # Get modified images (case-insensitive)
    image_count=$(git diff -z --name-only --diff-filter=ACM $commits | \
                  tr '\0' '\n' | grep -icE '\.(png|jpg|jpeg|bmp|gif)$' || echo 0)
    
    if [ "$image_count" -gt 0 ]; then
      echo "Found $image_count image(s), starting detection..."
      
      # Check each image with Docker
      git diff -z --name-only --diff-filter=ACM $commits | \
        tr '\0' '\n' | grep -iE '\.(png|jpg|jpeg|bmp|gif)$' > /tmp/images.txt
      
      has_error=0
      while IFS= read -r img; do
        if [ -f "$img" ]; then
          docker run --rm -v "$(pwd):/workspace" \
            ghcr.io/${{ github.repository_owner }}/watermark-detector:latest "$img" \
            || has_error=1
        fi
      done < /tmp/images.txt
      
      [ $has_error -eq 1 ] && exit 1
      echo "✅ All images passed"
    fi
```

### Behavior

- **Trigger**: PR opened, updated, or synchronized
- **Scope**: Only images changed in the PR
- **Action**: Blocks PR merge if watermark detected
- **Performance**: ~15-25 seconds (after image cache)

---

## Configuration

### Adjust Detection Sensitivity

Edit `detect_watermark.py`:

```python
# Angle threshold (default: 10 degrees)
MIN_ANGLE_THRESHOLD = 10.0

# Pattern for "Name + 4-digit number"
pattern = re.compile(r'([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+(\d{4})\b')
```

**Lower threshold (5°)**: More sensitive, may have false positives
**Higher threshold (15°)**: Less sensitive, may miss some watermarks

### Supported Image Formats

- PNG (.png)
- JPEG (.jpg, .jpeg)
- BMP (.bmp)
- GIF (.gif)

Case-insensitive matching.

### OCR Parameters

In `detect_watermark.py`:

```python
ocr = PaddleOCR(
    use_angle_cls=True,      # Enable angle classification
    lang="en",               # Language (en/ch)
    det_db_thresh=0.05,      # Detection threshold
    det_db_unclip_ratio=2.5, # Text box expansion
    show_log=False           # Suppress logs
)
```

---

## Troubleshooting

### Issue: Image Pull Failed

**Error:**
```
Error: failed to pull image: unauthorized
```

**Solution:**
1. Ensure Docker image is public
2. Go to GitHub Packages → watermark-detector → Settings
3. Change visibility to Public

### Issue: Image Not Found

**Error:**
```
Error: manifest unknown
```

**Solution:**
1. Check if image exists: `https://github.com/YOUR_USERNAME?tab=packages`
2. Wait for initial build to complete (~5-10 minutes)
3. Verify image name in workflow matches registry

### Issue: False Positives

**Symptom:** Architecture diagram text flagged as watermark

**Solution:**
1. Check if diagram has tilted text (e.g., diamond shapes)
2. Increase `MIN_ANGLE_THRESHOLD` to 15°
3. Adjust regex pattern to be more specific

### Issue: Missed Watermarks

**Symptom:** Watermark not detected

**Solution:**
1. Check image resolution (may be too low)
2. Decrease `MIN_ANGLE_THRESHOLD` to 5°
3. Verify watermark angle is >10° (use test mode)
4. Check if watermark matches pattern (Name + 4 digits)

### Issue: Slow Detection

**Symptom:** CI takes too long

**Solution:**
1. Ensure Docker image is cached (first run is slower)
2. Reduce image resolution before committing
3. Check if multiple large images in PR
4. Consider parallel processing for multiple images

---

## Performance

### Execution Time

**Without Docker (Installing dependencies each time):**
- Install dependencies: ~2-3 minutes
- Detection: ~10-20 seconds per image
- **Total: ~2.5-3.5 minutes**

**With Docker (Pre-built image with models):**
- Pull image (first time): ~30-60 seconds
- Pull image (cached): ~5 seconds
- Detection: ~5-10 seconds per image (no model download!)
- **Total: ~10-15 seconds (after cache)**

**Speed Improvement: ~15x faster** ⚡

### Optimization Tips

1. **Image Size**: Keep images under 2MB
2. **Resolution**: 1920x1080 is usually sufficient
3. **Format**: PNG is faster than JPEG for diagrams
4. **Batch**: Multiple small images faster than one large image

### Resource Usage

**Docker Image:**
- Size: ~1.5 GB (compressed: ~500 MB)
- Memory: ~500 MB during detection
- CPU: 1 core sufficient

**CI Runner:**
- Disk: ~2 GB for image + workspace
- Memory: ~1 GB total
- Network: ~500 MB first pull, ~0 MB cached

---

## Files Overview

### Core Files
- `detect_watermark.py` - Detection script (5.8K)
- `Dockerfile.watermark` - Docker image definition (765B)

### Workflows
- `.github/workflows/checkpatch.yml` - Main CI workflow
- `.github/workflows/build-watermark-docker.yml` - Image builder

### Actions
- `.github/actions/watermark-check/action.yml` - Reusable action

### Documentation
- `WATERMARK-DETECTION.md` - This file (complete guide)

### Testing
- `test-watermark.sh` - Test Python environment
- `test-docker.sh` - Test Docker image

### Configuration
- `.dockerignore` - Docker build optimization

---

## Technical Details

### Detection Algorithm

```python
1. Preprocess image (enhance contrast, binarize)
2. Run OCR to extract all text boxes
3. For each text box:
   a. Calculate angle: atan2(dy, dx)
   b. If angle > threshold: mark as watermark candidate
4. Concatenate all watermark candidates
5. Apply regex: r'([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+(\d{4})\b'
6. If match found: report watermark
```

### Why Angle-Based?

**Alternatives considered:**
- Color filtering: Unreliable (watermarks can be any color)
- Line removal: Damages architecture content
- Template matching: Requires known watermark templates

**Angle-based advantages:**
- Fundamental geometric property
- Independent of color/brightness
- Doesn't damage content
- Works with unknown watermark formats

---

## Support & Contributing

### Getting Help

1. Check this documentation
2. Review GitHub Actions logs
3. Test locally with Docker
4. Open an issue with:
   - Error message
   - Sample image (without sensitive data)
   - Workflow logs

### Contributing

Improvements welcome:
- Better OCR accuracy
- Faster detection
- Support for more watermark types
- Documentation improvements

### License

Part of OpenVela public-actions repository.

---

## Quick Reference

### Commands

```bash
# Local test with Python
python detect_watermark.py image.jpg

# Local test with Docker
docker run --rm -v "$(pwd):/workspace" \
  ghcr.io/YOUR_USERNAME/watermark-detector:latest image.jpg

# Build Docker image
docker build -f Dockerfile.watermark -t watermark-detector .

# Run test suite
./test-docker.sh
```

### Key Thresholds

- **Angle**: 10° (tilted text threshold)
- **Pattern**: `Name + 4 digits`
- **Formats**: png, jpg, jpeg, bmp, gif

### Important URLs

- Packages: `https://github.com/YOUR_USERNAME?tab=packages`
- Actions: `https://github.com/YOUR_USERNAME/REPO/actions`
- Registry: `ghcr.io/YOUR_USERNAME/watermark-detector`

---

**Last Updated:** 2025-01-16
**Version:** 1.0.0
