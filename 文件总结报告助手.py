#!/usr/bin/env python3

import os
import sys
import argparse
from datetime import datetime
from collections import defaultdict

DEFAULT_EXCLUDES = {
    ".git", ".svn", ".hg", ".idea", ".vscode", "__pycache__",
    ".DS_Store", "Thumbs.db", ".dir_snapshot.json", "rename_log.log",
}

EXT_ICONS = {
    "pdf": "📄", "doc": "📝", "docx": "📝",
    "xls": "📊", "xlsx": "📊", "csv": "📊",
    "ppt": "📊", "pptx": "📊",
    "png": "🖼️", "jpg": "🖼️", "jpeg": "🖼️", "gif": "🖼️",
    "heic": "🖼️", "bmp": "🖼️", "tiff": "🖼️", "webp": "🖼️",
    "mp3": "🎵", "wav": "🎵", "flac": "🎵", "m4a": "🎵",
    "mp4": "🎬", "mov": "🎬", "avi": "🎬", "mkv": "🎬",
    "zip": "📦", "rar": "📦", "7z": "📦", "tar": "📦", "gz": "📦",
    "dmg": "💾", "iso": "💾", "pkg": "💾",
    "py": "🐍", "sh": "🔧", "js": "🔧", "ts": "🔧",
    "json": "📋", "xml": "📋", "yaml": "📋", "yml": "📋",
    "html": "🌐", "css": "🌐",
    "md": "📖", "txt": "📖",
    "log": "📋", "tmp": "📋", "bak": "📋",
}


def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_icon(filename):
    if "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        return EXT_ICONS.get(ext, "📎")
    return "📄"


def collect_tree(base_dir, max_depth, excludes):
    root = {"name": os.path.basename(os.path.abspath(base_dir)) or base_dir,
            "type": "dir", "children": [], "file_count": 0, "total_size": 0}

    def _walk(current_path, node, depth):
        if depth > max_depth:
            return
        try:
            entries = sorted(os.listdir(current_path))
        except PermissionError:
            return
        for entry in entries:
            if entry in excludes or entry.startswith("."):
                continue
            full_path = os.path.join(current_path, entry)
            if os.path.isdir(full_path):
                child = {"name": entry, "type": "dir", "children": [],
                         "file_count": 0, "total_size": 0}
                _walk(full_path, child, depth + 1)
                node["children"].append(child)
                node["file_count"] += child["file_count"]
                node["total_size"] += child["total_size"]
            elif os.path.isfile(full_path):
                try:
                    size = os.path.getsize(full_path)
                except OSError:
                    size = 0
                node["children"].append({
                    "name": entry, "type": "file", "size": size
                })
                node["file_count"] += 1
                node["total_size"] += size

    _walk(base_dir, root, 1)
    return root


def build_tree_lines(nodes, prefix="", show_files=True):
    lines = []
    for i, node in enumerate(nodes):
        is_last = i == len(nodes) - 1
        connector = "└── " if is_last else "├── "
        if node["type"] == "dir":
            child_dirs = [c for c in node["children"] if c["type"] == "dir"]
            child_files = [c for c in node["children"] if c["type"] == "file"]
            has_child = node["file_count"] > 0
            if has_child:
                count_info = f" ({node['file_count']} 文件)"
                size_info = f" · {format_size(node['total_size'])}" if node["total_size"] > 0 else ""
            else:
                count_info = " (空)"
                size_info = ""
            lines.append(f"{prefix}{connector}📁 {node['name']}/{count_info}{size_info}")
            child_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(build_tree_lines(child_dirs, child_prefix, show_files))
            if show_files:
                for j, fchild in enumerate(child_files):
                    file_icon = get_icon(fchild["name"])
                    size_str = f"  ({format_size(fchild['size'])})" if fchild.get("size", 0) > 0 else ""
                    last_file = j == len(child_files) - 1 and len(child_dirs) == 0
                    fconn = "└── " if last_file else "├── "
                    lines.append(f"{child_prefix}{fconn}{file_icon} {fchild['name']}{size_str}")
    return lines


def compute_stats(base_dir, excludes):
    ext_counts = defaultdict(int)
    ext_sizes = defaultdict(int)
    total_files = 0
    total_size = 0
    dir_count = 0
    root_files = []

    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in excludes and not d.startswith(".")]
        rel_root = os.path.relpath(root, base_dir)
        if rel_root != ".":
            dir_count += 1
        for fn in files:
            if fn in excludes or fn.startswith("."):
                continue
            total_files += 1
            ext = fn.rsplit(".", 1)[-1].lower() if "." in fn else "(无扩展名)"
            ext_counts[ext] += 1
            try:
                sz = os.path.getsize(os.path.join(root, fn))
            except OSError:
                sz = 0
            ext_sizes[ext] += sz
            total_size += sz
            if rel_root == ".":
                root_files.append(fn)

    return {
        "total_files": total_files,
        "total_size": total_size,
        "dir_count": dir_count,
        "ext_counts": dict(ext_counts),
        "ext_sizes": dict(ext_sizes),
        "root_files": root_files,
    }


EXT_LABELS = {
    "pdf": "PDF 文档", "doc": "Word 文档", "docx": "Word 文档",
    "xls": "Excel 表格", "xlsx": "Excel 表格", "csv": "CSV 数据",
    "ppt": "PPT 演示", "pptx": "PPT 演示",
    "png": "PNG 图片", "jpg": "JPEG 图片", "jpeg": "JPEG 图片",
    "gif": "GIF 动图", "heic": "HEIC 图片", "bmp": "BMP 图片",
    "tiff": "TIFF 图片", "webp": "WebP 图片",
    "mp3": "MP3 音频", "wav": "WAV 音频", "flac": "FLAC 音频",
    "m4a": "M4A 音频",
    "mp4": "MP4 视频", "mov": "MOV 视频", "avi": "AVI 视频",
    "mkv": "MKV 视频",
    "zip": "ZIP 压缩包", "rar": "RAR 压缩包", "7z": "7Z 压缩包",
    "tar": "TAR 压缩包", "gz": "GZ 压缩包",
    "dmg": "DMG 安装包", "iso": "ISO 镜像", "pkg": "PKG 安装包",
    "py": "Python 脚本", "sh": "Shell 脚本", "js": "JS 脚本",
    "ts": "TS 脚本",
    "json": "JSON 数据", "xml": "XML 数据", "yaml": "YAML 数据",
    "yml": "YAML 数据",
    "html": "HTML 页面", "css": "CSS 样式",
    "md": "Markdown 文件", "txt": "文本文件",
    "log": "日志文件", "tmp": "临时文件", "bak": "备份文件",
    "(无扩展名)": "无扩展名文件",
}


def generate_report(base_dir, output_path, max_depth, show_files):
    base_dir = os.path.abspath(base_dir)
    dir_name = os.path.basename(base_dir) or base_dir
    now = datetime.now()

    excludes = DEFAULT_EXCLUDES.copy()

    stats = compute_stats(base_dir, excludes)
    tree = collect_tree(base_dir, max_depth, excludes)
    tree_lines = build_tree_lines(tree["children"], show_files=show_files)

    sorted_exts = sorted(stats["ext_counts"].items(),
                         key=lambda x: stats["ext_counts"][x[0]], reverse=True)

    lines = []
    lines.append(f"# {dir_name} 文件总结报告")
    lines.append("")
    lines.append(f"> 生成时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"> 目标目录：`{base_dir}`")
    lines.append(f"> 递归深度：{'完整' if max_depth >= 99 else f'{max_depth} 层'}")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 一、统计概览")
    lines.append("")
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 文件夹数 | {stats['dir_count']} |")
    lines.append(f"| 文件总数 | {stats['total_files']} |")
    lines.append(f"| 总大小 | {format_size(stats['total_size'])} |")
    lines.append(f"| 文件类型数 | {len(stats['ext_counts'])} |")
    lines.append("")
    lines.append("### 按扩展名分类")
    lines.append("")
    lines.append("| 类型 | 数量 | 大小 |")
    lines.append("|------|------|------|")
    for ext, count in sorted_exts:
        label = EXT_LABELS.get(ext, f".{ext} 文件")
        size = stats["ext_sizes"][ext]
        lines.append(f"| {label}（`.{ext}`） | {count} | {format_size(size)} |")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 二、目录结构")
    lines.append("")
    lines.append("```")
    lines.append(f"📁 {dir_name}/")
    lines.extend(tree_lines)
    lines.append("```")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 三、根目录文件清单")
    lines.append("")
    if stats["root_files"]:
        for fn in sorted(stats["root_files"]):
            icon = get_icon(fn)
            fpath = os.path.join(base_dir, fn)
            try:
                sz = os.path.getsize(fpath)
            except OSError:
                sz = 0
            lines.append(f"- {icon} `{fn}` — {format_size(sz)}")
    else:
        lines.append("_根目录下无直接文件，所有文件都在子文件夹中。_")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 四、说明")
    lines.append("")
    lines.append("本报告由 **文件总结报告助手** 自动生成，扫描时已跳过以下内容：")
    lines.append("")
    lines.append("- 以 `.` 开头的隐藏文件和目录（如 `.git/`、`.DS_Store`）")
    lines.append("- 常见缓存目录（如 `__pycache__/`）")
    lines.append("- 工具运行时产生的日志/快照文件（如 `rename_log.log`、`.dir_snapshot.json`）")
    lines.append("")
    lines.append(f"_报告生成工具版本：v1.0_")
    lines.append("")

    report_content = "\n".join(lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    return report_content


def main():
    parser = argparse.ArgumentParser(
        description="扫描指定目录，自动生成 Markdown 格式的文件总结报告"
    )
    parser.add_argument(
        "target_dir", nargs="?", default=".",
        help="要扫描的目标目录（默认: 当前目录）"
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="输出文件路径（默认: 本脚本所在目录下的 `文件总结报告.md`）"
    )
    parser.add_argument(
        "-d", "--depth", type=int, default=99,
        help="目录树递归深度（默认: 不限）"
    )
    parser.add_argument(
        "--no-files", action="store_true",
        help="目录树中不列出具体文件（只显示文件夹结构）"
    )

    args = parser.parse_args()

    target_dir = os.path.abspath(args.target_dir)
    if not os.path.isdir(target_dir):
        print(f"❌ 目录不存在: {target_dir}", file=sys.stderr)
        sys.exit(1)

    tool_dir = os.path.dirname(os.path.abspath(__file__))
    output = args.output or os.path.join(tool_dir, "文件总结报告.md")
    max_depth = args.depth if args.depth > 0 else 99

    print(f"🔍 正在扫描: {target_dir}")
    print(f"📝 输出文件: {output}")

    content = generate_report(target_dir, output, max_depth, not args.no_files)

    stats_line = f"✅ 报告已生成 — 路径: {output}"
    print(stats_line)
    print()

    head = "\n".join(content.split("\n")[:20])
    print("--- 报告预览（前 20 行）---")
    print(head)
    print("...")


if __name__ == "__main__":
    main()
