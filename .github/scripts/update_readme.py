import json
import pathlib
import re
import sys

EXPECTED_PATH = pathlib.Path(__file__).resolve().parent / "expected_todos.json"
EXPECTED = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
TARGETS = list(EXPECTED.keys())

ROOT = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[2]

TODO_RE = re.compile(r'^\s*#\s*TODO\s*(?:\((?P<who>[^)]*)\))?\s*:?\s*(?P<msg>.*?)\s*$')
ENTRY_RE = re.compile(r'^- \[ \] \*\*(?P<path>.+?):(?P<line>\d+)\*\* - (?P<msg>.*)$')


def extract(rel):
    rows = []
    text = (ROOT / rel).read_text(encoding="utf-8")
    for lineno, raw in enumerate(text.splitlines(), 1):
        if "TODO" not in raw:
            continue
        m = TODO_RE.match(raw)
        if not m:
            continue
        msg = (m.group("msg") or "").strip()
        who = m.group("who")
        if who:
            msg = ("(" + who.strip() + ") " + msg).strip()
        if msg:
            rows.append((lineno, msg))
    rows.sort(key=lambda x: x[0])
    return rows


def main():
    extracted = {}
    for rel in TARGETS:
        rows = extract(rel)
        got_msgs = [m for _, m in rows]
        exp_msgs = [m for _, m in EXPECTED[rel]]
        if got_msgs != exp_msgs:
            print("[FAIL] TODO messages mismatch for " + rel)
            print("GOT " + json.dumps(rows, ensure_ascii=False))
            print("EXP " + json.dumps(EXPECTED[rel], ensure_ascii=False))
            return 2
        extracted[rel] = rows
        print("[OK] " + rel + ": " + str(len(rows)) + " TODO entries")

    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    orig = text
    lines = text.split("\n")
    title = "### 📝 Complete TODO List"
    ti = lines.index(title)
    hi = next(k for k in range(ti + 1, len(lines)) if lines[k].startswith("## "))

    kept = []
    for k in range(ti + 1, hi):
        m = ENTRY_RE.match(lines[k])
        if m and m.group("path") not in TARGETS:
            kept.append((m.group("path"), int(m.group("line")), lines[k]))

    new_entries = []
    for rel in TARGETS:
        for lineno, msg in extracted[rel]:
            new_entries.append((rel, lineno, "- [ ] **" + rel + ":" + str(lineno) + "** - " + msg))

    all_entries = kept + new_entries
    all_entries.sort(key=lambda t: (t[0], t[1]))
    block = [raw for _, _, raw in all_entries]

    new_lines = lines[: ti + 1] + [""] + block + [""] + lines[hi:]
    new_text = "\n".join(new_lines)
    if orig.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"

    if new_text == orig:
        print("[INFO] README unchanged")
    else:
        readme.write_text(new_text, encoding="utf-8")
        print("[OK] README.md updated; total entries: " + str(len(block)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
