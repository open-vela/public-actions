# 中文字符检测

本文档说明如何在 CI/CD 流程中检测 PR 中的中文字符。

## 概述

中文检测包含两个主要检查：

1. **Commit Message 检查** - 检查所有 commit 消息中是否包含中文字符
2. **源文件检查** - 检查修改的源代码文件中是否包含中文注释或字符串

## 检查脚本

### 1. check_commit_msg.py

检查 Git commit messages 中是否包含中文字符。

**核心思想：**
- 接收一个 Git 的提交范围（例如，一个 PR 包含的所有 commits）
- 使用 `git log` 命令获取这个范围内所有 commit 的 message
- 使用正则表达式逐一检查每个 message 是否包含中文字符
- 如果发现中文字符，就打印错误信息并以失败状态退出（非零退出码）

**使用方法：**

```bash
# 检查最近 3 个 commit
./check_commit_msg.py HEAD~3..HEAD

# 检查 develop 分支和当前 feature 分支的差异
./check_commit_msg.py develop..my-feature-branch
```

### 2. check_source_files.py

检查 Git 变更的文件中是否包含中文字符（注释或字符串）。

**核心思想：**
- 接收一个 Git 提交范围
- 使用 `git diff` 找出在此范围内所有被修改或添加的文件
- 对每一个文件，检查是否在"豁免列表"中（如 README.md、docs/ 目录下的文件等）
- 如果文件不在豁免列表中，则逐行读取文件内容，检查是否包含中文注释或中文字符串
- 如果发现中文字符，打印出文件名和行号，并以失败状态退出

**使用方法：**

```bash
# 使用默认排除规则（README.md, .md 文件, docs/ 目录）
./check_source_files.py main..HEAD

# 自定义排除规则
./check_source_files.py main..HEAD --exclude README.md .md docs/ LICENSE
```

**排除规则说明：**
- 具体文件名：`README.md`
- 文件扩展名：`.md`（所有 markdown 文件）
- 目录：`docs/`（docs 目录下的所有文件）

## CI/CD 集成

在 GitHub Actions 工作流中，这些检查已经集成到 `checkpatch.yml` 中：

### 检查流程

1. **Check Chinese in Commit Messages** - 检查所有 PR 中的 commit 消息
2. **Check Chinese in Source Files** - 检查所有修改的源文件（排除文档文件）

### Docker 镜像

中文检测使用专用的轻量级 Docker 镜像：
```
ghcr.io/<organization>/chinese-detector:dev
```

该镜像包含：
- Python 3.10
- Git
- 中文检测脚本（check_commit_msg.py, check_source_files.py）

**注意：** 中文检测镜像与水印检测镜像是分离的，这样可以：
- 减小镜像体积（不包含 OpenCV、PaddleOCR 等大型依赖）
- 加快构建和拉取速度
- 独立维护和更新

## 本地测试

### 使用 Docker 测试

```bash
# 测试 commit message
docker run --rm -v "$(pwd):/workspace" -w /workspace \
  ghcr.io/<organization>/chinese-detector:dev \
  bash -c "git config --global --add safe.directory /workspace && python /usr/local/bin/check_commit_msg.py 'main..HEAD'"

# 测试源文件
docker run --rm -v "$(pwd):/workspace" -w /workspace \
  ghcr.io/<organization>/chinese-detector:dev \
  bash -c "git config --global --add safe.directory /workspace && python /usr/local/bin/check_source_files.py 'main..HEAD' --exclude README.md .md docs/"
```

**注意：** Docker 容器中需要先配置 `safe.directory` 以避免 Git 安全检查问题。

### 直接运行脚本

```bash
# 赋予执行权限
chmod +x check_commit_msg.py check_source_files.py

# 运行检查
./check_commit_msg.py HEAD~3..HEAD
./check_source_files.py HEAD~3..HEAD --exclude README.md .md docs/
```

## 自定义配置

### 修改排除规则

如果需要修改源文件检查的排除规则，可以在 `checkpatch.yml` 中修改 `--exclude` 参数：

```yaml
- name: Check Chinese in Source Files
  run: |
      # 添加更多排除规则
      docker run --rm -v "$(pwd):/workspace" -w /workspace \
        ghcr.io/${{ github.repository_owner }}/chinese-detector:dev \
        bash -c "git config --global --add safe.directory /workspace && \
        python /usr/local/bin/check_source_files.py '$commits' \
        --exclude README.md .md docs/ LICENSE CHANGELOG.md"
```

### 禁用某个检查

如果需要临时禁用某个检查，可以在 `checkpatch.yml` 中注释掉相应的步骤：

```yaml
# - name: Check Chinese in Commit Messages
#   run: |
#       ...
```

## 检测原理

### 中文字符范围

脚本使用 Unicode 范围 `\u4e00-\u9fff` 来检测中文字符，这个范围包含了大部分常见的中日韩（CJK）统一表意文字。

### 正则表达式

```python
CHINESE_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fff]')
```

## 常见问题

### Q: 为什么需要检查中文字符？

A: 为了保持代码库的国际化和可维护性，建议使用英文编写 commit 消息和代码注释。

### Q: 如何处理必须包含中文的文件？

A: 将这些文件添加到排除列表中，例如文档文件（.md）、README 等。

### Q: 检查失败了怎么办？

A: 检查失败时，脚本会输出包含中文字符的文件名和行号，根据提示修改相应的内容即可。

## 维护

### 更新 Docker 镜像

当修改检测脚本后，需要重新构建 Docker 镜像。镜像会在以下情况自动构建：
- 修改 `Dockerfile.chinese-detection`
- 修改 `check_commit_msg.py` 或 `check_source_files.py`
- 推送到 `dev` 或 `trunk` 分支

也可以手动构建：

```bash
docker build -f Dockerfile.chinese-detection -t ghcr.io/<organization>/chinese-detector:dev .
docker push ghcr.io/<organization>/chinese-detector:dev
```

### 测试脚本

在提交前，建议在本地测试脚本：

```bash
# 创建测试 commit
git commit -m "测试中文"  # 应该失败

# 创建包含中文的文件
echo "// 这是中文注释" > test.c
git add test.c
git commit -m "test"

# 运行检查
./check_commit_msg.py HEAD~1..HEAD
./check_source_files.py HEAD~1..HEAD
```
