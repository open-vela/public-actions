#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import subprocess
import re
import argparse

# 中文字符的 Unicode 范围
# 这个范围包含了大部分常见的中日韩（CJK）统一表意文字。
CHINESE_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fff]')

def contains_chinese(text):
    """
    检查给定文本中是否包含中文字符。
    """
    if text and CHINESE_CHAR_PATTERN.search(text):
        return True
    return False

def get_commit_messages(commit_range):
    """
    使用 git log 获取指定范围内的所有 commit 信息。
    返回一个包含 (commit_hash, commit_message) 元组的列表。
    """
    # 使用 %H 获取完整的 commit hash
    # 使用 %B 获取完整的 commit message (包括 subject 和 body)
    # 使用 %x00 作为分隔符，这是最稳妥的方式，可以避免 message 中的特殊字符干扰
    command = ["git", "log", "--pretty=format:%H%x00%B", commit_range]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True  # 如果 git 命令失败，则抛出异常
        )
    except FileNotFoundError:
        print("错误: 'git' 命令未找到。请确保 Git 已经安装并且在系统的 PATH 中。", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"错误: 'git log' 执行失败。\n{e.stderr}", file=sys.stderr)
        sys.exit(1)

    output = result.stdout.strip()
    if not output:
        return []

    commits = []
    # 按换行符分割每个 commit 条目
    for entry in output.split('\n'):
        # 按 null 字节分割 hash 和 message
        parts = entry.split('\x00', 1)
        if len(parts) == 2:
            commit_hash, commit_message = parts
            commits.append((commit_hash, commit_message))

    return commits

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description="检查 Git commit messages 中是否包含中文字符。"
    )
    parser.add_argument(
        "commit_range",
        help="要检查的 Git commit 范围 (例如: 'main..HEAD' 或 'commit1..commit2')。"
    )

    args = parser.parse_args()

    print(f"--- 正在检查 commit 范围: {args.commit_range} ---")

    commits_to_check = get_commit_messages(args.commit_range)

    if not commits_to_check:
        print("没有找到需要检查的 commits。")
        sys.exit(0)

    found_error = False
    for commit_hash, message in commits_to_check:
        if contains_chinese(message):
            found_error = True
            print("\n❌ 检查失败: Commit 中包含中文字符！")
            print(f"   Commit Hash: {commit_hash}")
            # 只显示 message 的前 100 个字符以保持简洁
            print(f"   Message (部分): {message.strip()[:100]}...")

    if found_error:
        print("\n--- 检查未通过 ---")
        sys.exit(1)
    else:
        print("\n✅ 所有 Commit Message 均符合规范，未检测到中文字符。")
        print("--- 检查通过 ---")
        sys.exit(0)

if __name__ == "__main__":
    main()
