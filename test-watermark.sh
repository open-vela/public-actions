#!/bin/bash
# 水印检测功能测试脚本

echo "=========================================="
echo "水印检测功能测试"
echo "=========================================="

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到 Python3"
    exit 1
fi

echo "✓ Python3 已安装"

# 检查脚本是否存在
if [ ! -f "detect_watermark.py" ]; then
    echo "❌ 错误：未找到 detect_watermark.py"
    exit 1
fi

echo "✓ detect_watermark.py 存在"

# 创建测试虚拟环境
echo ""
echo "正在创建测试环境..."
python3 -m venv .test_watermark_venv
source .test_watermark_venv/bin/activate

# 安装依赖
echo "正在安装依赖..."
pip install -q opencv-python numpy paddlepaddle paddleocr

echo ""
echo "=========================================="
echo "环境准备完成"
echo "=========================================="
echo ""
echo "使用方法："
echo "  python detect_watermark.py <图片路径>"
echo "  python detect_watermark.py <目录路径>"
echo ""
echo "示例："
echo "  python detect_watermark.py test.jpg"
echo "  python detect_watermark.py ./images/"
echo ""

# 清理
deactivate
rm -rf .test_watermark_venv

echo "测试环境已清理"
