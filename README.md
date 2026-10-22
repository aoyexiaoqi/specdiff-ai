# SpecDiff AI — 工艺技术协议差异分析

把两个版本的技术协议（技术协议 / 工艺规范 / 供货技术条件）逐条对齐，自动生成
**可溯源的差异矩阵**：每一条结论都标注状态、参数变化和原文出处，评审时能直接
回到源文档核对。

## 功能

- **多格式输入**：`.docx`（python-docx，含标题层级与表格）、`.pdf`（pypdf 文本层）、
  `.txt` / `.md`（标准库），全程离线运行
- **结构化提取**：按章节路径 + 条款号切分条款；条款内用正则提取关键参数——
  带单位数值（`8.5 kA`、`6.0 mm`）、公差（`±0.2 kN`）、范围（`180~200 ℃`）、百分比（`5%`）
- **三级对齐**：条款号精确匹配 → 同章节模糊匹配 → 跨章节高阈值模糊匹配（捕捉条款迁移）
- **五态分类**：
  - `冲突` 同一条款、关键参数值不同（评审优先级最高）
  - `新增` / `删除` 仅在新版 / 旧版出现
  - `修改` 措辞变化但参数不变
  - `未变`
- **双格式输出**：Excel 差异矩阵（汇总 + 明细，状态着色、参数变化列、双向出处）
  与 Markdown 报告
- **确定性优先**：核心流程不依赖任何大模型；仅预留一个可选的 LLM 文本规整钩子
  （环境变量 `SPECDIFF_LLM_ENDPOINT`），不可用时自动降级，离线结果不受影响

## 安装

```bash
pip install -e .          # 或 pip install specdiff-ai（发布后）
pip install -e .[dev]     # 开发/测试依赖
```

要求 Python ≥ 3.9。

## 使用

```bash
# 对比两版协议
specdiff old_spec.docx new_spec.docx --out diff.xlsx --md diff.md

# 一键演示：生成两份带预埋差异的示例协议并跑通全流程
specdiff --demo
```

演示的两份示例（电阻点焊工艺协议）预埋了 5 处差异：焊接电流 8.5→9.2 kA（冲突）、
抽检比例 5%→10%（冲突）、电极压力条款改写（修改）、端面直径条款删除、位置度公差条款新增。

## 输出示例（差异矩阵列）

| 状态 | 章节 | 条款号 | 参数变化 | 旧版出处 |
| --- | --- | --- | --- | --- |
| 冲突 | 2 焊接参数 | 2.1 | 8.5 kA → 9.2 kA | old_spec.txt 第6行 |
| 新增 | 3 质量要求 | 3.4 | 新增参数 ±0.5 mm | — |

## 设计说明

- 参数提取刻意保守：无单位的裸数字、年份、条款号不会被当作参数，避免误报
- 「冲突」只由参数签名（类型 + 单位 + 数值）差异触发；纯措辞调整归为「修改」
- 每条 DiffItem 保留新旧原文与定位（页 / 行 / 段），报告末尾也注明需人工复核

## 局限

- PDF 仅支持文本层，扫描件需先 OCR
- 章节识别基于标题样式 / 编号启发式，格式极不规范的文档对齐质量会下降
- 参数按（类型、单位）分组配对生成变化说明；同组内参数大幅增删时，
  变化说明可能不精确（状态判定本身基于参数多重集比较，不受影响）

## 开发

```bash
pip install -e .[dev]
pytest --cov=specdiff_ai
```

## License

MIT

---

# SpecDiff AI — Technical Agreement Diff Analysis (English)

Compare two versions of a technical agreement / process specification,
align their clauses, and produce a **traceable difference matrix**: every
conclusion carries a status, the parameter delta, and a pointer back to
the original wording.

**Pipeline** — parse (`.docx` / `.pdf` / `.txt` / `.md`) → extract clauses
(section path + clause number) and key parameters (values with units,
±tolerances, ranges, percentages) → align (clause number, then fuzzy
same-section, then fuzzy cross-section) → classify each clause as
**conflict / added / deleted / modified / unchanged** → export an Excel
difference matrix and a Markdown report.

Deterministic by design and fully offline; an optional LLM hook
(`SPECDIFF_LLM_ENDPOINT`) can normalise wording but is never required.

```bash
pip install -e .
specdiff old.docx new.docx --out diff.xlsx --md diff.md
specdiff --demo   # sample specs with planted differences
```

MIT License.
