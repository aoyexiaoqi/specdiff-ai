from specdiff_ai.diff import (
    STATUS_ADDED,
    STATUS_CONFLICT,
    STATUS_DELETED,
    STATUS_MODIFIED,
    STATUS_UNCHANGED,
    compare,
    count_by_status,
    summarize_param_changes,
)
from specdiff_ai.extract import parse_lines
from specdiff_ai.params import extract_params

OLD = [
    "2 焊接参数",
    "2.1 焊接电流应为 8.5 kA。",
    "2.2 电极压力为 3.2 kN。",
    "2.3 电极端面直径为 6.0 mm。",
]
NEW = [
    "2 焊接参数",
    "2.1 焊接电流应为 9.2 kA。",
    "2.2 电极压力为 3.2 kN，需每日点检。",
    "2.4 焊点位置度公差为 ±0.5 mm。",
]


def _by_no(items):
    return {item.clause_no: item for item in items if item.clause_no}


def test_conflict_when_parameter_changes():
    items = _by_no(compare(parse_lines(OLD, "o"), parse_lines(NEW, "n")))
    assert items["2.1"].status == STATUS_CONFLICT
    assert items["2.1"].param_changes == "8.5 kA → 9.2 kA"


def test_modified_when_only_wording_changes():
    items = _by_no(compare(parse_lines(OLD, "o"), parse_lines(NEW, "n")))
    assert items["2.2"].status == STATUS_MODIFIED
    assert items["2.2"].param_changes == ""


def test_added_and_deleted():
    items = compare(parse_lines(OLD, "o"), parse_lines(NEW, "n"))
    by_no = _by_no(items)
    assert by_no["2.4"].status == STATUS_ADDED
    assert by_no["2.4"].old_text == ""
    assert by_no["2.3"].status == STATUS_DELETED
    assert by_no["2.3"].new_text == ""


def test_unchanged():
    same = parse_lines(OLD, "o")
    items = compare(same, parse_lines(OLD, "n"))
    assert all(item.status == STATUS_UNCHANGED for item in items)


def test_fuzzy_alignment_for_unnumbered_clause():
    old = parse_lines(["3 质量", "焊点表面不得有飞溅和裂纹。"], "o")
    new = parse_lines(["3 质量", "焊点表面不得有飞溅、裂纹和烧穿。"], "n")
    items = compare(old, new)
    assert len(items) == 1
    assert items[0].status == STATUS_MODIFIED


def test_clause_moved_to_other_section_still_matched():
    old = parse_lines(["2 参数", "2.1 焊接电流应为 8.5 kA，焊接时间 12 周波。"], "o")
    new = parse_lines(["5 附则", "焊接电流应为 8.5 kA，焊接时间 12 周波，详见记录表。"], "n")
    items = compare(old, new)
    assert len(items) == 1
    assert items[0].status == STATUS_MODIFIED


def test_count_by_status_includes_all_keys():
    counts = count_by_status(compare(parse_lines(OLD, "o"), parse_lines(NEW, "n")))
    assert counts[STATUS_CONFLICT] == 1
    assert counts[STATUS_ADDED] == 1
    assert counts[STATUS_DELETED] == 1
    assert counts[STATUS_MODIFIED] == 1
    assert counts[STATUS_UNCHANGED] == 0


def test_summarize_param_changes_add_remove():
    old_params = extract_params("电流 8.5 kA，压力 3.2 kN。")
    new_params = extract_params("电流 8.5 kA，公差 ±0.5 mm。")
    summary = summarize_param_changes(old_params, new_params)
    assert "删除参数 3.2 kN" in summary
    assert "新增参数 ±0.5 mm" in summary
