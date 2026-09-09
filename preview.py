"""Local preview server. Run:  python preview.py

Renders pages on every request straight from source, so editing any file and
refreshing shows the change. The browser also auto-reloads on its own.
Stand-in for `jekyll serve` so no Ruby install is needed. GitHub Pages still
runs real Jekyll; this only has to be close enough to eyeball.
"""
import datetime
import html
import http.server
import pathlib
import re
import socketserver
import webbrowser

ROOT = pathlib.Path(__file__).parent
PORT = 4000
WATCH = ["index.html", "devlogs", "_layouts", "_includes", "_posts", "assets", "_config.yml"]

RELOAD_JS = """
<script>
(function(){let s=null;setInterval(async()=>{try{
const r=await fetch('/__changed');const t=await r.text();
if(s===null){s=t;}else if(s!==t){location.reload();}
}catch(e){}},1000);})();
</script>
"""


# ── front matter ───────────────────────────────────────────────────────────
def parse_front_matter(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw, body = text[4:end], text[end + 4:].lstrip("\n")
    data, lines, i = {}, raw.split("\n"), 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in (">-", ">", "|", "|-"):
            i += 1
            chunk = []
            while i < len(lines) and (not lines[i].strip() or lines[i].startswith("  ")):
                chunk.append(lines[i].strip())
                i += 1
            data[key] = " ".join(c for c in chunk if c)
            continue
        if val.startswith("[") and val.endswith("]"):
            data[key] = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
        elif val:
            data[key] = val.strip("\"'")
        i += 1
    return data, body


# ── markdown ───────────────────────────────────────────────────────────────
def inline_md(s):
    s = re.sub(r"`([^`]+)`", lambda m: "<code>" + html.escape(m.group(1)) + "</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def markdown(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    out, buf, lines, i = [], [], text.split("\n"), 0

    def flush():
        if buf:
            out.append("<p>" + inline_md(" ".join(buf).strip()) + "</p>")
            buf.clear()

    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            flush()
            i += 1
            continue
        h = re.match(r"^(#{2,4})\s+(.*)$", line)
        if h:
            flush()
            n = len(h.group(1))
            out.append(f"<h{n}>{inline_md(h.group(2))}</h{n}>")
            i += 1
            continue
        for pat, tag in ((r"^\s*[-*]\s+", "ul"), (r"^\s*\d+\.\s+", "ol")):
            if re.match(pat, line):
                flush()
                items = []
                while i < len(lines) and re.match(pat, lines[i]):
                    items.append(inline_md(re.sub(pat, "", lines[i]).strip()))
                    i += 1
                out.append(f"<{tag}>" + "".join(f"<li>{x}</li>" for x in items) + f"</{tag}>")
                break
        else:
            buf.append(line.strip())
            i += 1
    flush()
    return "\n".join(out)


# ── liquid subset ──────────────────────────────────────────────────────────
def split_top(s, sep):
    out, buf, q = [], "", None
    for ch in s:
        if q:
            buf += ch
            q = None if ch == q else q
        elif ch in "'\"":
            q, buf = ch, buf + ch
        elif ch == sep:
            out.append(buf)
            buf = ""
        else:
            buf += ch
    out.append(buf)
    return out


def resolve(expr, ctx):
    expr = expr.strip()
    if expr[:1] in "'\"" and expr[-1:] == expr[:1]:
        return expr[1:-1]
    if re.fullmatch(r"-?\d+", expr):
        return int(expr)
    cur = ctx
    for part in expr.split("."):
        if part == "size":
            cur = len(cur) if cur else 0
            continue
        cur = cur.get(part) if isinstance(cur, dict) else None
        if cur is None:
            return None
    return cur


def fmt_date(val, fmt):
    if isinstance(val, str):
        try:
            val = datetime.date.fromisoformat(val)
        except ValueError:
            return val
    out, strip = fmt, []
    for k, v in (("%-d", "%d"), ("%-m", "%m")):
        if k in out:
            out, _ = out.replace(k, v), strip.append(v)
    s = val.strftime(out)
    for _ in strip:
        s = re.sub(r"\b0(\d)", r"\1", s)
    return s


def apply_filter(val, name, args):
    if name == "default":
        return val if val not in (None, "", []) else args[0]
    if name in ("relative_url",):
        return "/" + str(val).lstrip("/")
    if name == "absolute_url":
        return "https://frkncx.github.io/" + str(val).lstrip("/")
    if name == "append":
        return (val or "") + args[0]
    if name == "strip_newlines":
        return re.sub(r"\s*\n\s*", " ", val or "")
    if name == "strip":
        return (val or "").strip()
    if name == "strip_html":
        return re.sub(r"<[^>]+>", "", val or "")
    if name == "truncate":
        n, v = int(args[0]), val or ""
        return v if len(v) <= n else v[: n - 1].rstrip() + "…"
    if name == "slugify":
        return re.sub(r"[^a-z0-9]+", "-", (val or "").lower()).strip("-")
    if name == "date":
        return fmt_date(val, args[0])
    if name == "date_to_xmlschema":
        return (val if isinstance(val, str) else val.isoformat()) + "T00:00:00+00:00"
    return val


def filter_args(argstr, ctx):
    args = []
    for a in split_top(argstr, ","):
        a = a.strip()
        if not a:
            continue
        if a[:1] in "'\"" and a[-1:] == a[:1]:
            args.append(a[1:-1])
        elif re.fullmatch(r"[\w.]+", a) and not re.fullmatch(r"-?\d+", a):
            r = resolve(a, ctx)
            args.append("" if r is None else r)
        else:
            args.append(a.strip("\"'"))
    return args


def evaluate(expr, ctx):
    parts = split_top(expr, "|")
    val = resolve(parts[0], ctx)
    for f in parts[1:]:
        m = re.match(r"^\s*(\w+)\s*:?\s*(.*)$", f)
        val = apply_filter(val, m.group(1), filter_args(m.group(2), ctx))
    return val


def truthy(v):
    return v not in (None, False, "", [], 0)


def eval_cond(expr, ctx):
    m = re.match(r"^(.*?)\s+(==|!=|>|<|>=|<=|contains)\s+(.*)$", expr.strip())
    if not m:
        return truthy(resolve(expr, ctx))
    a, op, b = resolve(m.group(1), ctx), m.group(2), resolve(m.group(3), ctx)
    if op == "==":
        return a == b
    if op == "!=":
        return a != b
    if op == "contains":
        return bool(a) and b in a
    try:
        return {">": a > b, "<": a < b, ">=": a >= b, "<=": a <= b}[op]
    except TypeError:
        return False


TOKEN = re.compile(r"\{\{-?(.*?)-?\}\}|\{%-?(.*?)-?%\}", re.S)


def tokenize(t):
    toks, pos = [], 0
    for m in TOKEN.finditer(t):
        if m.start() > pos:
            toks.append(("text", t[pos:m.start()]))
        toks.append(("out", m.group(1).strip()) if m.group(1) is not None
                    else ("tag", m.group(2).strip()))
        pos = m.end()
    toks.append(("text", t[pos:]))
    return toks


def untokenize(toks):
    return "".join(v if k == "text" else ("{{" + v + "}}" if k == "out" else "{%" + v + "%}")
                   for k, v in toks)


def render(tpl, ctx, includes):
    toks, out, i = tokenize(tpl), [], 0

    def close(start, enders):
        depth, j = 0, start
        while j < len(toks):
            k, v = toks[j]
            if k == "tag":
                w = v.split()[0] if v.split() else ""
                if w in ("if", "for", "comment"):
                    depth += 1
                elif w in ("endif", "endfor", "endcomment"):
                    if depth == 0 and w in enders:
                        return j
                    depth -= 1
                elif depth == 0 and w in enders:
                    return j
            j += 1
        return len(toks) - 1

    while i < len(toks):
        kind, val = toks[i]
        if kind == "text":
            out.append(val)
            i += 1
        elif kind == "out":
            v = evaluate(val, ctx)
            out.append("" if v is None else str(v))
            i += 1
        else:
            word = val.split()[0] if val.split() else ""
            if word == "include":
                out.append(render(includes[val.split()[1]], ctx, includes))
                i += 1
            elif word == "comment":
                i = close(i + 1, {"endcomment"}) + 1
            elif word == "assign":
                m = re.match(r"assign\s+(\w+)\s*=\s*(.*)$", val)
                ctx[m.group(1)] = evaluate(m.group(2), ctx)
                i += 1
            elif word == "if":
                cond, start, branches = val[2:].strip(), i + 1, []
                while True:
                    j = close(start, {"elsif", "else", "endif"})
                    branches.append((cond, toks[start:j]))
                    w = toks[j][1].split()[0]
                    if w == "endif":
                        break
                    cond = "true" if w == "else" else toks[j][1][5:].strip()
                    start = j + 1
                for c, body in branches:
                    if c == "true" or eval_cond(c, ctx):
                        out.append(render(untokenize(body), ctx, includes))
                        break
                i = j + 1
            elif word == "for":
                m = re.match(r"for\s+(\w+)\s+in\s+([\w.]+)(?:\s+limit:\s*(\d+))?", val)
                items = resolve(m.group(2), ctx) or []
                if m.group(3):
                    items = items[: int(m.group(3))]
                j = close(i + 1, {"endfor"})
                body = untokenize(toks[i + 1:j])
                for it in items:
                    ctx[m.group(1)] = it
                    out.append(render(body, ctx, includes))
                i = j + 1
            else:
                i += 1
    return "".join(out)


# ── site model ─────────────────────────────────────────────────────────────
def load():
    cfg, _ = parse_front_matter("---\n" + (ROOT / "_config.yml").read_text(encoding="utf-8") + "\n---\n")
    includes = {p.name: p.read_text(encoding="utf-8") for p in (ROOT / "_includes").glob("*.html")}
    layouts = {p.stem: p.read_text(encoding="utf-8") for p in (ROOT / "_layouts").glob("*.html")}
    posts = []
    for p in sorted((ROOT / "_posts").glob("*.md")):
        fm, body = parse_front_matter(p.read_text(encoding="utf-8"))
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", p.stem)
        fm.update(url=f"/devlogs/{slug}/", content=markdown(body), layout="post")
        fm.setdefault("date", p.stem[:10])
        posts.append(fm)
    posts.sort(key=lambda x: str(x["date"]), reverse=True)
    site = dict(cfg)
    site["posts"] = posts
    return site, includes, layouts


def wrap(page, content, site, includes, layouts):
    name = page.get("layout", "default")
    while name:
        fm, body = parse_front_matter(layouts[name])
        content = render(body, {"site": site, "page": page, "content": content}, includes)
        name = fm.get("layout")
    return content


def build(path):
    site, includes, layouts = load()
    if path in ("/", "/index.html"):
        src, url = ROOT / "index.html", "/"
    elif path == "/devlogs/":
        src, url = ROOT / "devlogs" / "index.html", "/devlogs/"
    else:
        slug = path.strip("/").split("/")[-1]
        for p in site["posts"]:
            if p["url"] == path:
                return wrap(p, p["content"], site, includes, layouts) + RELOAD_JS
        return None
    fm, body = parse_front_matter(src.read_text(encoding="utf-8"))
    fm["url"] = url
    inner = render(body, {"site": site, "page": fm, "content": ""}, includes)
    return wrap(fm, inner, site, includes, layouts) + RELOAD_JS


def stamp():
    newest = 0
    for w in WATCH:
        p = ROOT / w
        if p.is_file():
            newest = max(newest, p.stat().st_mtime)
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    newest = max(newest, f.stat().st_mtime)
    return str(newest)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")  # always serve fresh CSS/JS
        super().end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/__changed":
            return self._send(stamp(), "text/plain")
        if path.endswith("/") or path == "":
            try:
                page = build(path or "/")
            except Exception as e:
                return self._send(f"<pre style='color:#c00;font:14px monospace'>"
                                  f"{html.escape(type(e).__name__)}: {html.escape(str(e))}</pre>"
                                  + RELOAD_JS, "text/html")
            if page is not None:
                return self._send(page, "text/html")
        try:
            return super().do_GET()
        except (ConnectionError, BrokenPipeError):
            pass  # browser cancelled the request

    def _send(self, text, ctype):
        data = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, request, client_address):
        pass  # browsers cancel image requests constantly


if __name__ == "__main__":
    url = f"http://localhost:{PORT}/"
    print(f"Preview running at {url}")
    print("Edit any file and the browser reloads by itself. Ctrl+C to stop.")
    webbrowser.open(url)
    Server(("", PORT), Handler).serve_forever()
