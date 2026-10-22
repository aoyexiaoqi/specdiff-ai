"""Clause alignment between the old and the new document version.

Alignment runs in three passes, most reliable first:

1. **Clause number** -- the same ``clause_no`` in both documents.
2. **Fuzzy, same section** -- normalised-text similarity (difflib) inside
   the same section path.
3. **Fuzzy, cross section** -- a stricter similarity threshold, to catch
   clauses that moved to another section.

Anything left unpaired is reported as deleted (old only) or added
(new only) by the diff stage.
"""

from __future__ import annotations

import difflib
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Set

from .extract import Clause

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[，。；：、！？·,.;:!?'\"“”‘’（）()\[\]<>《》\-—_~～]")


def normalize_text(text: str) -> str:
    """Normalise text for comparison: no whitespace, unified punctuation."""
    text = _PUNCT_RE.sub("", text)
    text = _WS_RE.sub("", text)
    return text.lower()


def text_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


def _section_similarity(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


@dataclass
class Alignment:
    pairs: Dict[int, int] = field(default_factory=dict)  # old index -> new index
    similarity: Dict[int, float] = field(default_factory=dict)
    added: List[int] = field(default_factory=list)  # new indices without a match
    removed: List[int] = field(default_factory=list)  # old indices without a match


def align(old: Sequence[Clause], new: Sequence[Clause]) -> Alignment:
    pairs: Dict[int, int] = {}
    similarity: Dict[int, float] = {}
    used_new: Set[int] = set()

    def take(old_idx: int, new_idx: int, score: float) -> None:
        pairs[old_idx] = new_idx
        similarity[old_idx] = score
        used_new.add(new_idx)

    # Pass 1 -- identical clause numbers.
    old_by_no: Dict[str, List[int]] = defaultdict(list)
    new_by_no: Dict[str, List[int]] = defaultdict(list)
    for i, clause in enumerate(old):
        if clause.clause_no:
            old_by_no[clause.clause_no].append(i)
    for j, clause in enumerate(new):
        if clause.clause_no:
            new_by_no[clause.clause_no].append(j)

    for number, old_idxs in old_by_no.items():
        new_idxs = [j for j in new_by_no.get(number, []) if j not in used_new]
        candidates = []
        for i in old_idxs:
            for j in new_idxs:
                score = 0.7 * _section_similarity(
                    old[i].section_path, new[j].section_path
                ) + 0.3 * text_similarity(old[i].text, new[j].text)
                candidates.append((score, i, j))
        for score, i, j in sorted(candidates, reverse=True):
            if i not in pairs and j not in used_new:
                take(i, j, text_similarity(old[i].text, new[j].text))

    # Passes 2 and 3 -- fuzzy text similarity.
    def fuzzy_pass(same_section: bool, threshold: float) -> None:
        candidates = []
        for i, old_clause in enumerate(old):
            if i in pairs:
                continue
            for j, new_clause in enumerate(new):
                if j in used_new:
                    continue
                if same_section and old_clause.section_path != new_clause.section_path:
                    continue
                if not same_section and old_clause.section_path == new_clause.section_path:
                    continue
                score = text_similarity(old_clause.text, new_clause.text)
                if score >= threshold:
                    candidates.append((score, i, j))
        for score, i, j in sorted(candidates, reverse=True):
            if i not in pairs and j not in used_new:
                take(i, j, score)

    fuzzy_pass(same_section=True, threshold=0.5)
    fuzzy_pass(same_section=False, threshold=0.8)

    added = [j for j in range(len(new)) if j not in used_new]
    removed = [i for i in range(len(old)) if i not in pairs]
    return Alignment(pairs=pairs, similarity=similarity, added=added, removed=removed)
