from __future__ import annotations
import re
import hashlib
from typing import List

URL_RE = re.compile(r"https?://\S+")


def normalize_text(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", "", s)
    return s


def sha1_hex(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def count_x_chars(s: str) -> int:
    """
    安全側のカウント（URLはt.co換算で1本=23文字扱い）
    """
    urls = URL_RE.findall(s)
    base = len(URL_RE.sub("", s))
    return base + 23 * len(urls)


def trim_plaintext(s: str, max_len: int) -> str:
    s = s.strip()
    if max_len <= 0:
        return ""
    if len(s) <= max_len:
        return s
    if max_len <= 1:
        return s[:max_len]
    return s[: max_len - 1].rstrip() + "…"


def split_batches(items: List[str], batch_size: int) -> List[List[str]]:
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]
