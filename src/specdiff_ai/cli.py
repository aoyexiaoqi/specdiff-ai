"""Command line interface.

Usage::

    specdiff OLD NEW [--out diff.xlsx] [--md diff.md]
    specdiff --demo [--demo-dir specdiff-demo]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .diff import compare, count_by_status
from .extract import load_document
from .llm import maybe_enhance
from .report import write_excel, write_markdown


def _print_counts(counts: dict, total: int) -> None:
    print("条款总数：%d" % total)
    for status, count in counts.items():
        if count:
            print("  %s：%d" % (status, count))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="specdiff",
        description="工艺技术协议差异分析：对比两版技术协议，生成可溯源的差异矩阵与报告。",
    )
    parser.add_argument("old", nargs="?", help="旧版文档（.docx / .pdf / .txt / .md）")
    parser.add_argument("new", nargs="?", help="新版文档（.docx / .pdf / .txt / .md）")
    parser.add_argument("--out", default="diff.xlsx", help="Excel 差异矩阵输出路径（默认 diff.xlsx）")
    parser.add_argument("--md", default=None, help="Markdown 报告输出路径（默认与 --out 同名 .md）")
    parser.add_argument("--demo", action="store_true", help="生成示例文档并跑通全流程")
    parser.add_argument("--demo-dir", default="specdiff-demo", help="--demo 输出目录")
    args = parser.parse_args(argv)

    if args.demo:
        from .demo import run_demo

        xlsx_path, md_path, counts = run_demo(args.demo_dir)
        total = sum(counts.values())
        print("演示完成，示例文档与报告位于 %s/" % args.demo_dir)
        _print_counts(counts, total)
        print("Excel 差异矩阵：%s" % xlsx_path)
        print("Markdown 报告：%s" % md_path)
        return 0

    if not args.old or not args.new:
        parser.print_usage(sys.stderr)
        print("specdiff: 需要提供 OLD 与 NEW 两个文档路径（或使用 --demo）", file=sys.stderr)
        return 2

    for label, name in (("旧版", args.old), ("新版", args.new)):
        if not Path(name).is_file():
            print("specdiff: %s文档不存在：%s" % (label, name), file=sys.stderr)
            return 2

    try:
        old_clauses = maybe_enhance(load_document(args.old))
        new_clauses = maybe_enhance(load_document(args.new))
    except Exception as exc:  # unreadable input is a usage-level failure
        print("specdiff: 文档解析失败：%s" % exc, file=sys.stderr)
        return 2

    items = compare(old_clauses, new_clauses)
    xlsx_path = write_excel(items, args.out, Path(args.old).name, Path(args.new).name)
    md_path = args.md or str(Path(args.out).with_suffix(".md"))
    write_markdown(items, md_path, Path(args.old).name, Path(args.new).name)

    _print_counts(count_by_status(items), len(items))
    print("Excel 差异矩阵：%s" % xlsx_path)
    print("Markdown 报告：%s" % md_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
