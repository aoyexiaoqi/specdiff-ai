"""Built-in demo: two sample specs with planted differences.

The demo writes ``old_spec.txt`` / ``new_spec.txt`` (a small resistance
spot-welding technical agreement), runs the full pipeline and produces
``diff.xlsx`` + ``diff.md``.  Planted differences:

* 2.1 welding current 8.5 kA -> 9.2 kA           -> 冲突
* 2.2 reworded, same parameters                   -> 修改
* 2.3 electrode diameter clause removed          -> 删除
* 3.2 inspection ratio 5% -> 10%                  -> 冲突
* 3.4 positional tolerance clause added           -> 新增
* everything else                                 -> 未变
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from .diff import compare, count_by_status
from .extract import load_document
from .report import write_excel, write_markdown

OLD_SPEC = """电阻点焊工艺技术协议
1 总则
1.1 本协议适用于车身电阻点焊工艺。
1.2 焊接设备应满足生产线节拍要求。
2 焊接参数
2.1 焊接电流应为 8.5 kA，焊接时间 12 周波。
2.2 电极压力应为 3.2 kN，允许偏差 ±0.2 kN。
2.3 电极端面直径为 6.0 mm，磨损后不得小于 5.5 mm。
2.4 冷却水流量不低于 6 L/min。
3 质量要求
3.1 焊核直径不小于 4.5 mm。
3.2 焊接强度抽检比例为 5%。
3.3 焊点表面不得有飞溅和裂纹。
"""

NEW_SPEC = """电阻点焊工艺技术协议
1 总则
1.1 本协议适用于车身电阻点焊工艺。
1.2 焊接设备应满足生产线节拍要求。
2 焊接参数
2.1 焊接电流应为 9.2 kA，焊接时间 12 周波。
2.2 电极压力应为 3.2 kN，允许偏差 ±0.2 kN，压力需每日点检确认。
2.4 冷却水流量不低于 6 L/min。
3 质量要求
3.1 焊核直径不小于 4.5 mm。
3.2 焊接强度抽检比例为 10%。
3.3 焊点表面不得有飞溅和裂纹。
3.4 焊点位置度公差为 ±0.5 mm。
"""


def run_demo(out_dir) -> Tuple[Path, Path, dict]:
    """Generate the sample documents, diff them, write both reports."""
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)

    old_path = target / "old_spec.txt"
    new_path = target / "new_spec.txt"
    old_path.write_text(OLD_SPEC, encoding="utf-8")
    new_path.write_text(NEW_SPEC, encoding="utf-8")

    old_clauses = load_document(old_path)
    new_clauses = load_document(new_path)
    items = compare(old_clauses, new_clauses)

    xlsx_path = write_excel(items, target / "diff.xlsx", old_path.name, new_path.name)
    md_path = write_markdown(items, target / "diff.md", old_path.name, new_path.name)
    return xlsx_path, md_path, count_by_status(items)
