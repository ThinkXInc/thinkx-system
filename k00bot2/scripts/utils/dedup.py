from __future__ import annotations
import difflib
from typing import Iterable

from .text import normalize_text, sha1_hex


def similarity(a: str, b: str) -> float:
    a_n = normalize_text(a)
    b_n = normalize_text(b)
    if not a_n or not b_n:
        return 0.0
    return difflib.SequenceMatcher(None, a_n, b_n).ratio()


def is_duplicate(
    text: str,
    existing_texts: Iterable[str],
    threshold: float = 0.5,
) -> bool:
    """
    仕様：「50%以上の文字列が一致するなら重複」
    を difflib の近似一致率で実装。
    """
    for ex in existing_texts:
        if similarity(text, ex) >= threshold:
            return True
    return False


def text_hash(text: str) -> str:
    return sha1_hex(normalize_text(text))
