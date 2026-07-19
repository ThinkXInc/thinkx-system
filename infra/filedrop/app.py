#!/usr/bin/env python3
"""filedrop — ブラウザのドラッグ&ドロップで素材を /src/thinkx-system/Downloads に受け取る内部ツール。

staging LB の basic auth 配下(https://staging.thinkxinc.com/filedrop/)で公開する。
バインドは 0.0.0.0:8008 だが SG により LB からしか到達できない。
依存なし(Python 標準ライブラリのみ)。systemd(filedrop.service)が kaz で常駐させる。
"""
import html
import os
import pathlib
import re
from email.parser import BytesParser
from email.policy import default as email_default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

INBOX = pathlib.Path("/src/thinkx-system/Downloads")
PORT = 8008
MAX_BYTES = 200 * 1024 * 1024

PAGE = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>File to Staging</title>
<style>
body{font-family:sans-serif;max-width:640px;margin:40px auto;padding:0 16px;color:#333}
#drop{border:3px dashed #aaa;border-radius:12px;padding:60px 20px;text-align:center;color:#777;font-size:18px;cursor:pointer}
#drop.over{border-color:#39c;background:#eef7fb}
li{margin:4px 0}
</style>
<h2>File to Staging</h2>
<p>ここにファイルをドラッグ&ドロップ(またはクリックして選択)すると staging サーバーに転送されます。</p>
<div id="drop">ここにドロップ</div>
<input type="file" id="pick" multiple style="display:none">
<h3>受信済み</h3>
<ul>__LIST__</ul>
<script>
const d=document.getElementById('drop'),p=document.getElementById('pick');
d.onclick=()=>p.click();
d.ondragover=e=>{e.preventDefault();d.classList.add('over')};
d.ondragleave=()=>d.classList.remove('over');
d.ondrop=e=>{e.preventDefault();d.classList.remove('over');send(e.dataTransfer.files)};
p.onchange=()=>send(p.files);
async function send(files){
  const f=new FormData();
  for(const x of files)f.append('file',x,x.name);
  await fetch('./',{method:'POST',body:f});
  location.reload();
}
</script>
"""


def safe_name(filename):
    name = os.path.basename(filename)
    name = re.sub(r"[/\\\x00-\x1f]", "_", name).strip()
    return name or "unnamed"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        items = sorted((p for p in INBOX.iterdir() if p.is_file()),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        listing = "".join(
            f"<li>{html.escape(p.name)} ({max(1, p.stat().st_size // 1024)} KB)</li>"
            for p in items) or "<li>(まだありません)</li>"
        body = PAGE.replace("__LIST__", listing).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > MAX_BYTES:
            self.send_error(413, "file too large")
            return
        raw = (b"Content-Type: " + self.headers["Content-Type"].encode() + b"\r\n\r\n"
               + self.rfile.read(length))
        msg = BytesParser(policy=email_default).parsebytes(raw)
        saved = 0
        for part in msg.iter_parts():
            filename = part.get_filename()
            if not filename:
                continue
            (INBOX / safe_name(filename)).write_bytes(part.get_payload(decode=True))
            saved += 1
        self.send_response(303)
        self.send_header("Location", "./")
        self.send_header("Content-Length", "0")
        self.end_headers()
        self.log_message("saved %d file(s)", saved)


def main():
    INBOX.mkdir(parents=True, exist_ok=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
