"""Diff classification.

Every aligned pair of clauses -- and every unpaired clause -- becomes a
:class:`DiffItem` with one of five statuses:

* ``未变`` unchanged -- normalised text identical
* ``修改`` modified   -- wording changed, key parameters unchanged
* ``冲突`` conflict   -- same clause, but key parameter values differ
* ``新增`` added      -- only present in the new version
* ``删除`` deleted    -- only present in the old version

Each item keeps both original texts and both locators, so a reviewer can
verify every conclusion against the source documents in seconds.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from itertools import zip_longest
from typing import List, Sequence

from .align import align, normalize_text
from .extract import Clause
from .params import Param

STATUS_ADDED = "新增"
STATUS_DELETED = "删除"
STATUS_MODIFIED = "修改"
STATUS_CONFLICT = "冲突"
STATUS_UNCHANGED = "未变"
ALL_STATUSES = [
    STATUS_CONFLICT,
    STATUS_ADDED,
    STATUS_DELETED,
    STATUS_MODIFIED,
    STATUS_UNCHANGED,
]


@dataclass
class DiffItem:
    status: str
    section_path: str
    clause_no: str
    old_text: str = ""
    new_text: str = ""
    old_params: List[Param] = field(default_factory=list)
    new_params: List[Param] = field(default_factory=list)
    old_locator: str = ""
    new_locator: str = ""
    old_doc: str = ""
    new_doc: str = ""
    similarity: float = 0.0

    @property
    def param_changes(self) -> str:
        return summarize_param_changes(self.old_params, self.new_params)


def summarize_param_changes(old_params: Sequence[Param], new_params: Sequence[Param]) -> str:
    """Human-readable parameter delta, e.g. ``8.5 kA → 9.2 kA; 新增参数 ±0.5 mm``.

    Parameters are paired within (kind, unit) groups, so a replaced
    parameter (``3.2 kN`` -> ``±0.5 mm``) is reported as one deletion plus
    one addition, while a value change inside a group is a ``→`` delta.
    """
    from collections import defaultdict

    def group(params: Sequence[Param]) -> dict:
        grouped: dict = defaultdict(list)
        for param in params:
            grouped[(param.kind, param.unit)].append(param)
        return grouped

    old_groups = group(old_params)
    new_groups = group(new_params)
    keys: List = []
    for param in list(old_params) + list(new_params):
        key = (param.kind, param.unit)
        if key not in keys:
            keys.append(key)

    parts: List[str] = []
    for key in keys:
        for old_p, new_p in zip_longest(
            old_groups.get(key, []), new_groups.get(key, [])
        ):
            if old_p is None:
                parts.append("新增参数 %s" % new_p.raw)
            elif new_p is None:
                parts.append("删除参数 %s" % old_p.raw)
            elif old_p.signature() != new_p.signature():
                parts.append("%s → %s" % (old_p.raw, new_p.raw))
    return "; ".join(parts)


def _param_signature_counter(params: Sequence[Param]) -> Counter:
    return Counter(p.signature() for p in params)


def classify_pair(old_clause: Clause, new_clause: Clause, similarity: float) -> DiffItem:
    if normalize_text(old_clause.text) == normalize_text(new_clause.text):
        status = STATUS_UNCHANGED
    elif _param_signature_counter(old_clause.params) != _param_signature_counter(
        new_clause.params
    ):
        status = STATUS_CONFLICT
    else:
        status = STATUS_MODIFIED
    return DiffItem(
        status=status,
        section_path=new_clause.section_path or old_clause.section_path,
        clause_no=new_clause.clause_no or old_clause.clause_no,
        old_text=old_clause.text,
        new_text=new_clause.text,
        old_params=list(old_clause.params),
        new_params=list(new_clause.params),
        old_locator=old_clause.locator,
        new_locator=new_clause.locator,
        old_doc=old_clause.doc,
        new_doc=new_clause.doc,
        similarity=similarity,
    )


def compare(old: Sequence[Clause], new: Sequence[Clause]) -> List[DiffItem]:
    """Compare two extracted documents and return the diff items.

    Order follows the new document (matched and added items), with the
    deleted items appended in old-document order.
    """
    result = align(old, new)
    old_for_new = {new_idx: old_idx for old_idx, new_idx in result.pairs.items()}

    items: List[DiffItem] = []
    for j, new_clause in enumerate(new):
        if j in old_for_new:
            i = old_for_new[j]
            items.append(classify_pair(old[i], new_clause, result.similarity.get(i, 0.0)))
        else:
            items.append(
                DiffItem(
                    status=STATUS_ADDED,
                    section_path=new_clause.section_path,
                    clause_no=new_clause.clause_no,
                    new_text=new_clause.text,
                    new_params=list(new_clause.params),
                    new_locator=new_clause.locator,
                    new_doc=new_clause.doc,
                )
            )
    for i in result.removed:
        old_clause = old[i]
        items.append(
            DiffItem(
                status=STATUS_DELETED,
                section_path=old_clause.section_path,
                clause_no=old_clause.clause_no,
                old_text=old_clause.text,
                old_params=list(old_clause.params),
                old_locator=old_clause.locator,
                old_doc=old_clause.doc,
            )
        )
    return items


def count_by_status(items: Sequence[DiffItem]) -> dict:
    counts = Counter(item.status for item in items)
    return {status: counts.get(status, 0) for status in ALL_STATUSES}
