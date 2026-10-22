# 使用说明 / Usage

## 命令行

```bash
specdiff OLD NEW [--out diff.xlsx] [--md diff.md]
specdiff --demo [--demo-dir DIR]
```

- `OLD` / `NEW`：`.docx`、`.pdf`、`.txt`、`.md` 文件，可混合格式对比
  （如旧版 PDF 对新版 DOCX）。
- `--out`：Excel 差异矩阵路径，默认 `diff.xlsx`。
- `--md`：Markdown 报告路径，默认与 `--out` 同名、后缀改为 `.md`。
- 退出码：`0` 成功；`2` 参数错误或文件不可读。

## Python API

```python
from specdiff_ai import load_document, compare, count_by_status
from specdiff_ai.report import write_excel, write_markdown

old = load_document("old_spec.docx")
new = load_document("new_spec.docx")
items = compare(old, new)
print(count_by_status(items))   # {'冲突': 2, '新增': 1, ...}
write_excel(items, "diff.xlsx", "old_spec.docx", "new_spec.docx")
write_markdown(items, "diff.md", "old_spec.docx", "new_spec.docx")
```

## 状态判定规则

| 状态 | 判定 |
| --- | --- |
| 未变 | 归一化后文本完全一致 |
| 冲突 | 文本不同且关键参数签名集合不同 |
| 修改 | 文本不同但关键参数签名集合相同 |
| 新增 | 仅新版存在（对齐后无匹配） |
| 删除 | 仅旧版存在（对齐后无匹配） |

参数签名 = （类型， 单位， 数值/区间）。参数提取覆盖带单位数值、±公差、
`~`/`-` 区间与百分比；无单位裸数字不计入。

## 可选 AI 钩子

设置环境变量 `SPECDIFF_LLM_ENDPOINT` 指向一个接受 `{"text": ...}` 并返回
`{"text": ...}` 的 HTTP 端点后，条款文本会先经该端点规整再比对。端点不可用
时自动回退原文；不设置时该功能完全不激活，测试与离线使用不受影响。
