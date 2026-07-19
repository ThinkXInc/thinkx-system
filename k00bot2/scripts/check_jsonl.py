import json, glob, sys

paths = sorted(glob.glob("data/**/*.jsonl", recursive=True))
for path in paths:
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            s = line.strip()
            if not s:
                continue
            try:
                json.loads(s)
            except json.JSONDecodeError as e:
                print("BAD:", path, "line", i, "col", e.colno, e.msg)
                print("snippet:", s[:400])
                sys.exit(1)
print("OK: all jsonl valid")
PY
