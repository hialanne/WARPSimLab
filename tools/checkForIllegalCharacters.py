from pathlib import Path

bad = []

for path in Path(".").rglob("*.py"):
    text = path.read_text(encoding="utf-8", errors="replace")
    for line_no, line in enumerate(text.splitlines(), start=1):
        for col_no, ch in enumerate(line, start=1):
            code = ord(ch)
            if code > 127 or (code < 32 and ch not in "\t"):
                bad.append((path, line_no, col_no, ch, code))

if not bad:
    print("No suspicious special characters found.")
else:
    for path, line, col, ch, code in bad:
        print(f"{path}:{line}:{col}: U+{code:04X} {repr(ch)}")
