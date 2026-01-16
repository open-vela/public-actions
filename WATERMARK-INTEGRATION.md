# 水印检测集成说明

## 集成概述

已成功将基于几何角度过滤的水印识别功能集成到 checkpatch workflow 中。

## 新增文件

1. **detect_watermark.py** - 核心水印检测脚本
   - 使用 PaddleOCR 进行文字识别
   - 基于几何角度过滤法识别倾斜水印
   - 支持单文件和目录批量检测

2. **README-WATERMARK.md** - 功能详细说明文档
   - 核心原理说明
   - 使用方法
   - 常见问题解答

3. **test-watermark.sh** - 本地测试脚本
   - 快速验证环境配置
   - 安装依赖并测试功能

## 修改文件

**`.github/workflows/checkpatch.yml`**
- 新增 "Check Watermark in Images" 步骤
- 在 PR 检查前自动检测图片水印
- 仅对 PR 中变更的图片进行检测

## 工作流程

```
PR 提交
  ↓
检测是否包含图片文件
  ↓
是 → 安装依赖 → 运行水印检测 → 发现水印？
                                  ↓
                            是 → CI 失败 ❌
                            否 → 继续 checkpatch ✅
  ↓
否 → 跳过水印检测 → 继续 checkpatch
```

## 检测逻辑

1. **角度计算**：提取文本框坐标，计算倾斜角度
2. **阈值过滤**：倾斜角度 > 10° 的文本被标记为疑似水印
3. **正则匹配**：匹配 "姓名 + 4位数字" 格式（如 "Jianjun Li 6719"）
4. **结果判定**：
   - 匹配成功 → 敏感水印，CI 失败
   - 未匹配 → 安全，CI 通过

## 本地测试

```bash
# 1. 运行测试脚本（验证环境）
./test-watermark.sh

# 2. 检测单个图片
python detect_watermark.py path/to/image.jpg

# 3. 检测整个目录
python detect_watermark.py path/to/images/
```

## CI 集成效果

- ✅ **自动化**：PR 提交时自动触发
- ✅ **高效**：仅检测变更的图片文件
- ✅ **准确**：基于几何角度的稳定识别
- ✅ **阻断**：发现敏感水印时自动失败

## 配置调整

如需调整检测灵敏度，编辑 `detect_watermark.py`：

```python
# 角度阈值（默认 10 度）
MIN_ANGLE_THRESHOLD = 10.0

# 正则表达式（匹配姓名+数字格式）
pattern = re.compile(r'([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+(\d{4})\b')
```

## 依赖项

- opencv-python - 图像处理
- numpy - 数值计算
- paddlepaddle - 深度学习框架
- paddleocr - OCR 引擎

## 注意事项

1. 首次运行会下载 PaddleOCR 模型（约 10MB）
2. 检测时间取决于图片数量和大小
3. 建议在提交前本地测试，避免 CI 失败
4. 如遇误报，可调整角度阈值或正则表达式

## 技术优势

相比传统方法（颜色分割、线条去除），几何角度过滤法具有：
- **稳定性**：基于物理几何特征，不受颜色、亮度影响
- **准确性**：架构图横平竖直 vs 水印倾斜，特征明显
- **鲁棒性**：不会误伤架构图内容
