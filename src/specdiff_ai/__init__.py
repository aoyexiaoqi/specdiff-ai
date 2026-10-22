"""SpecDiff AI -- 工艺技术协议差异分析.

Compare two versions of a technical agreement, align clauses, classify
the differences （新增 / 删除 / 修改 / 冲突 / 未变） and produce a
traceable Excel difference matrix plus a Markdown report.
"""

from .diff import DiffItem, compare, count_by_status
from .extract import Clause, load_document
from .params import Param, extract_params

__version__ = "0.1.0"

__all__ = [
    "Clause",
    "DiffItem",
    "Param",
    "__version__",
    "compare",
    "count_by_status",
    "extract_params",
    "load_document",
]
