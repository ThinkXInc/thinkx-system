from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Set, Union


PathLike = Union[str, Path]


def ensure_dir(path: PathLike) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_lines(path: PathLike) -> List[str]:
    """
    テキストを行のリストで読む(strip 済み・空行は捨てる)。
    ファイルが無ければ空リスト(iter_jsonl と同じ流儀)。
    """
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        return [s for s in (line.strip() for line in f) if s]


def write_lines(path: PathLike, lines: List[str]) -> None:
    """1行=1要素でテキストに書く(上書き・末尾改行あり)。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for s in lines:
            f.write(f"{s}\n")


def iter_jsonl(path: PathLike) -> Iterator[Dict[str, Any]]:
    """
    1行=1JSON の jsonl を読む。
    壊れた行があれば、ファイル名/行番号/抜粋付きで落とす。
    """
    p = Path(path)
    if not p.exists():
        return
    with p.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError as e:
                snippet = s[:500]
                raise RuntimeError(
                    f"Invalid JSONL: {p} line={lineno} col={e.colno} msg={e.msg}\n"
                    f"snippet: {snippet}\n"
                    f"Hint: 末尾改行なしのjsonlに追記すると '}}{{' のように連結して壊れます。"
                ) from None
            if isinstance(obj, dict):
                yield obj
            else:
                # 念のためdict以外も許容（必要ならここで弾く）
                yield obj  # type: ignore[misc]


def append_jsonl(path: PathLike, obj: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(obj, ensure_ascii=False) + "\n"
    data = line.encode("utf-8")

    with open(p, "ab+") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        if size > 0:
            f.seek(-1, os.SEEK_END)
            last = f.read(1)
            if last != b"\n":
                f.write(b"\n")
        f.write(data)

def load_jsonl_set(path: PathLike, key: str) -> Set[str]:
    s: Set[str] = set()
    for obj in iter_jsonl(path):
        if not isinstance(obj, dict):
            continue
        v = obj.get(key)
        if v is None:
            continue
        vs = str(v).strip()
        if vs:
            s.add(vs)
    return s
