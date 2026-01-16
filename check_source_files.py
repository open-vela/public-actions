#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import subprocess
import re
import argparse
from pathlib import Path

# 中文字符的 Unicode 范围
CHINESE_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fff]')

def get_changed_files(commit_range):
    """
    使用 git diff 获取指定范围内的所有已变更（添加/修改）的文件列表。
    """
    # --name-only: 只显示文件名
    # --diff-filter=AM: 只关心被添加(A)或修改(M)的文件，忽略删除(D)等
    command = ["git", "diff", "--name-only", "--diff-filter=AM", commit_range]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True
        )
    except FileNotFoundError:
        print("错误: 'git' 命令未找到。请确保 Git 已经安装并且在系统的 PATH 中。", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"错误: 'git diff' 执行失败。\n{e.stderr}", file=sys.stderr)
        sys.exit(1)

    files = result.stdout.strip().split('\n')
    # 过滤掉空字符串，以防万一
    return [f for f in files if f]

def is_file_excluded(filepath, exclusion_patterns):
    """
    检查文件路径是否匹配任何排除模式。
    模式可以是：
    - 具体文件名 (e.g., 'README.md')
    - 文件扩展名 (e.g., '.md')
    - 目录 (e.g., 'docs/')
    """
    if not exclusion_patterns:
        return False

    path_obj = Path(filepath)
    for pattern in exclusion_patterns:
        if pattern.startswith('.'):  # 检查扩展名
            if path_obj.suffix == pattern:
                return True
        elif pattern.endswith('/'):  # 检查目录
            if filepath.startswith(pattern):
                return True
        else:  # 检查具体文件名
            if path_obj.name == pattern:
                return True

    return False

def check_file_for_chinese(filepath):
    """
    逐行检查文件内容，如果发现中文字符，返回包含中文的行号列表。
    """
    lines_with_chinese = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if CHINESE_CHAR_PATTERN.search(line):
                    lines_with_chinese.append(i)
    except UnicodeDecodeError:
        # 很可能是二进制文件，直接跳过检查
        print(f"  [警告] 文件 '{filepath}' 无法以 UTF-8 解码，已跳过检查（可能为二进制文件）。")
        return []
    except FileNotFoundError:
        # 文件可能在 diff 中列出，但后续被删除了
        print(f"  [警告] 文件 '{filepath}' 未找到，已跳过。")
        return []
    except Exception as e:
        print(f"  [错误] 读取文件 '{filepath}' 时发生未知错误: {e}")
        return []

    return lines_with_chinese

def main():
    parser = argparse.ArgumentParser(
        description="检查 Git 变更的文件中是否包含中文字符（注释或字符串）。"
    )
    parser.add_argument(
        "commit_range",
        help="要检查的 Git commit 范围 (例如: 'main..HEAD')。"
    )
    parser.add_argument(
        '--exclude',
        nargs='*',  # 允许多个 --exclude 参数
        default=['README.md', '.md', 'docs/'], # 默认的排除列表
        help="要排除检查的文件或目录。例如: 'README.md' '.md' 'docs/'"
    )

    args = parser.parse_args()

    print(f"--- 正在检查文件内容，commit 范围: {args.commit_range} ---")
    print(f"--- 排除规则: {args.exclude} ---")

    changed_files = get_changed_files(args.commit_range)

    if not changed_files:
        print("没有找到需要检查的文件。")
        sys.exit(0)

    found_error = False
    for filepath in changed_files:
        if is_file_excluded(filepath, args.exclude):
            print(f"  [跳过] 文件 '{filepath}' 在排除列表中。")
            continue

        print(f"  [检查] 文件 '{filepath}'...")
        lines_with_chinese = check_file_for_chinese(filepath)

        if lines_with_chinese:
            found_error = True
            print(f"  ❌ 失败: 在文件 '{filepath}' 中发现中文字符，行号: {lines_with_chinese}")

    if found_error:
        print("\n--- 检查未通过：代码文件中包含中文字符。 ---")
        sys.exit(1)
    else:
        print("\n✅ 所有已检查的文件均符合规范。")
        print("--- 检查通过 ---")
        sys.exit(0)

if __name__ == "__main__":
    main()
