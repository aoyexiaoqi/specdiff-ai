from specdiff_ai.params import extract_params


def sigs(text):
    return [p.signature() for p in extract_params(text)]


def test_plain_value_with_unit():
    params = extract_params("焊接电流应为 8.5 kA。")
    assert len(params) == 1
    assert params[0].kind == "value"
    assert params[0].unit == "kA"
    assert params[0].value == 8.5


def test_multiple_params_in_one_clause():
    params = extract_params("电流 9.2 kA，时间 12 周波，压力 3.2 kN。")
    assert [p.unit for p in params] == ["kA", "周波", "kN"]


def test_tolerance_not_double_counted():
    params = extract_params("允许偏差 ±0.2 kN。")
    assert len(params) == 1
    assert params[0].kind == "tolerance"
    assert params[0].value == 0.2
    assert params[0].unit == "kN"
    assert params[0].raw == "±0.2 kN"


def test_tilde_range():
    params = extract_params("温度控制在 180~200 ℃。")
    assert len(params) == 1
    assert params[0].kind == "range"
    assert (params[0].low, params[0].high) == (180.0, 200.0)
    assert params[0].unit == "℃"


def test_dash_range_with_unit():
    params = extract_params("间隙 0.5-1.0 mm。")
    assert len(params) == 1
    assert params[0].kind == "range"
    assert params[0].unit == "mm"


def test_percent():
    params = extract_params("抽检比例为 5%。")
    assert len(params) == 1
    assert params[0].kind == "percent"
    assert params[0].value == 5.0
    assert params[0].raw == "5%"


def test_bare_numbers_are_not_params():
    assert extract_params("3.2.1 本条款自 2024 年起执行，共 5 项。") == []


def test_season_markers_are_not_ranges():
    assert extract_params("包含 S01-S05 全部剧集。") == []


def test_decimal_and_temperature_units():
    params = extract_params("烘烤温度 120.5 °C，保持 30 min。")
    assert sigs("烘烤温度 120.5 °C，保持 30 min。") == [
        ("value", "°C", 120.5),
        ("value", "min", 30.0),
    ]
    assert len(params) == 2
