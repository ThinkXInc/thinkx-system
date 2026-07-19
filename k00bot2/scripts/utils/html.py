from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

try:
    import trafilatura
    from trafilatura.metadata import extract_metadata
except Exception:  # trafilatura optional fallback
    trafilatura = None
    extract_metadata = None


@dataclass
class PageExtract:
    url: str
    final_url: str
    title: str
    published_at: str  # ISO date or empty
    text: str


DEFAULT_HEADERS = {
    "User-Agent": "k00bot2/1.0 (+https://example.com) requests",
    "Accept-Language": "ja,en;q=0.8",
}


# ---- Title cleanup ----
_TITLE_SUFFIX_PATTERNS = [
    r"\s*[-–—]\s*大塚一輝\s*$",
    r"\s*[|｜]\s*大塚一輝\s*$",
]


def clean_title(title: str) -> str:
    t = (title or "").strip()
    t = re.sub(r"\s+", " ", t).strip()
    for pat in _TITLE_SUFFIX_PATTERNS:
        t = re.sub(pat, "", t).strip()
    return t


def normalize_extracted_text_keep_newlines(text: str) -> str:
    """
    改行を保持しつつ、見た目を整える:
    - CRLF -> LF
    - 行内の連続空白を1つに
    - 行頭/行末の余分な空白を除去
    - 3つ以上の連続改行を2つに
    """
    t = (text or "").replace("\r\n", "\n").replace("\r", "\n")

    # 行内の空白だけを詰める（\nは保持）
    t = re.sub(r"[ \t]+", " ", t)

    # 改行周辺の空白を除去
    t = re.sub(r" *\n *", "\n", t)

    # 空行が多すぎるのを抑制
    t = re.sub(r"\n{3,}", "\n\n", t)

    return t.strip()


def fetch_html(url: str, timeout: int = 30) -> Tuple[str, str]:
    r = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    return r.text, r.url


def _parse_date_from_html(soup: BeautifulSoup) -> str:
    candidates = []
    for key in [
        ("property", "article:published_time"),
        ("name", "pubdate"),
        ("name", "publishdate"),
        ("name", "timestamp"),
        ("name", "date"),
        ("name", "DC.date.issued"),
        ("property", "og:published_time"),
    ]:
        tag = soup.find("meta", attrs={key[0]: key[1]})
        if tag and tag.get("content"):
            candidates.append(tag["content"])

    time_tag = soup.find("time")
    if time_tag and time_tag.get("datetime"):
        candidates.append(time_tag["datetime"])

    for c in candidates:
        try:
            dt = dateparser.parse(c)
            if dt:
                return dt.date().isoformat()
        except Exception:
            continue
    return ""


def _extract_text_fallback(html: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    container = soup.find("article") or soup.find("main") or soup.body
    if not container:
        return title, ""

    for s in container.find_all(["script", "style", "noscript"]):
        s.decompose()

    # ★ 改行を残すため、セパレータは "\n"
    text = container.get_text("\n", strip=True)
    text = normalize_extracted_text_keep_newlines(text)
    return title, text


def extract_page(html: str, url: str, final_url: Optional[str] = None) -> PageExtract:
    final_url = final_url or url

    if trafilatura:
        try:
            extracted = trafilatura.extract(
                html, url=final_url, include_comments=False, include_tables=False
            )
            meta = extract_metadata(html, url=final_url) if extract_metadata else None
            title = (meta.title if meta and meta.title else "") or ""
            date = ""
            if meta and meta.date:
                try:
                    date = dateparser.parse(str(meta.date)).date().isoformat()
                except Exception:
                    date = ""
            if extracted:
                # ★ 改行保持の正規化
                text = normalize_extracted_text_keep_newlines(extracted)
                return PageExtract(url=url, final_url=final_url, title=title, published_at=date, text=text)
        except Exception:
            pass

    soup = BeautifulSoup(html, "lxml")
    title, text = _extract_text_fallback(html)
    published_at = _parse_date_from_html(soup)
    return PageExtract(url=url, final_url=final_url, title=title, published_at=published_at, text=text)


def domain_of(url: str) -> str:
    p = urlparse(url)
    return p.netloc.replace(":", "_")
