from __future__ import annotations
import argparse
import gzip
import re
import xml.etree.ElementTree as ET
from typing import List, Set, Optional
import requests

from ..config import load_config
from ..utils.io import ensure_dir, write_lines
from ..utils.html import domain_of


def fetch_bytes(url: str) -> bytes:
    r = requests.get(url, timeout=30, allow_redirects=True, headers={"User-Agent": "k00bot2/1.0"})
    r.raise_for_status()
    content = r.content
    if url.endswith(".gz"):
        return gzip.decompress(content)
    return content


def parse_sitemap(xml_bytes: bytes) -> ET.Element:
    return ET.fromstring(xml_bytes)


def _localname(tag: str) -> str:
    # "{namespace}urlset" -> "urlset"
    if tag.startswith("{") and "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _ns_uri(tag: str) -> str:
    # "{namespace}urlset" -> "namespace"
    if tag.startswith("{") and "}" in tag:
        return tag[1:].split("}", 1)[0]
    return ""


def is_sitemap_index(root: ET.Element) -> bool:
    return _localname(root.tag) == "sitemapindex"


def is_urlset(root: ET.Element) -> bool:
    return _localname(root.tag) == "urlset"


def extract_locs(root: ET.Element) -> List[str]:
    """
    WordPress.com の sitemap では <image:loc> が大量に出るため、
    sitemap 標準名前空間の <url>/<loc>（または <sitemap>/<loc>）のみを抽出する。
    """
    ns = _ns_uri(root.tag)

    def q(name: str) -> str:
        return f"{{{ns}}}{name}" if ns else name

    locs: List[str] = []

    if is_sitemap_index(root):
        # <sitemapindex><sitemap><loc> ... </loc></sitemap>...</sitemapindex>
        for loc in root.findall(f".//{q('sitemap')}/{q('loc')}"):
            if loc.text:
                locs.append(loc.text.strip())
        return locs

    if is_urlset(root):
        # <urlset><url><loc> ... </loc></url>...</urlset>
        for loc in root.findall(f".//{q('url')}/{q('loc')}"):
            if loc.text:
                locs.append(loc.text.strip())
        return locs

    # 想定外のルート形式でも「標準NSのloc」だけを拾う（image:loc等は除外）
    for elem in root.iter():
        if _localname(elem.tag) != "loc":
            continue
        if ns and _ns_uri(elem.tag) != ns:
            continue
        if elem.text:
            locs.append(elem.text.strip())
    return locs


def crawl_sitemap(sitemap_url: str, seen: Optional[Set[str]] = None, limit: int = 50000) -> List[str]:
    if seen is None:
        seen = set()
    if sitemap_url in seen:
        return []
    seen.add(sitemap_url)

    xml_bytes = fetch_bytes(sitemap_url)
    root = parse_sitemap(xml_bytes)

    if is_sitemap_index(root):
        urls: List[str] = []
        for loc in extract_locs(root):
            urls.extend(crawl_sitemap(loc, seen=seen, limit=limit))
            if len(urls) >= limit:
                break
        return urls[:limit]

    if is_urlset(root):
        urls = extract_locs(root)
        return urls[:limit]

    return []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", default="settings.yaml")
    ap.add_argument("--all", action="store_true", help="settings.yaml の blogs 全てを処理")
    ap.add_argument("--sitemap-url", default="", help="直接sitemap URLを指定して処理")
    ap.add_argument("--blog-name", default="", help="settings.yaml の blogs[].name を指定して処理")
    ap.add_argument("--limit", type=int, default=50000)
    args = ap.parse_args()

    cfg = load_config(settings_path=args.settings)
    data_dir = cfg.data_dir
    out_dir = data_dir / "urls" / "sitemap"
    ensure_dir(out_dir)

    blogs = cfg.settings.get("blogs", []) or []

    targets = []
    if args.sitemap_url:
        targets = [{"name": "manual", "sitemap_url": args.sitemap_url}]
    elif args.blog_name:
        targets = [b for b in blogs if b.get("name") == args.blog_name]
    elif args.all:
        targets = blogs
    else:
        raise SystemExit("Specify one of --all / --sitemap-url / --blog-name")

    for b in targets:
        sitemap_url = b["sitemap_url"]
        urls = crawl_sitemap(sitemap_url, limit=args.limit)

        inc = b.get("url_include_regex", "") or ""
        exc = b.get("url_exclude_regex", "") or ""
        if inc:
            urls = [u for u in urls if re.search(inc, u)]
        if exc:
            urls = [u for u in urls if not re.search(exc, u)]

        urls = sorted(set(urls))

        dom = domain_of(sitemap_url)
        out_path = out_dir / f"page_urls_{dom}.txt"
        write_lines(out_path, urls)
        print(f"[ok] {sitemap_url} -> {out_path} ({len(urls)} urls)")


if __name__ == "__main__":
    main()