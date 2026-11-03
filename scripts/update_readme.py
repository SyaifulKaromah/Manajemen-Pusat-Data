#!/usr/bin/env python3
"""Membuat ulang README.md berisi daftar semua file .md di repo."""
from pathlib import Path
from urllib.parse import quote

TITLE = "Manajemen-Pusat-Data"
ROOT = Path(__file__).resolve().parent.parent

files = []
for p in ROOT.rglob("*.md"):
    rel = p.relative_to(ROOT)
    if rel.name.lower() == "readme.md":
        continue
    if any(part.startswith(".") for part in rel.parts):
        continue
    files.append(rel)

files.sort(key=lambda r: str(r).lower())

lines = [f"# {TITLE}", ""]
for rel in files:
    name = rel.with_suffix("").as_posix()
    lines.append(f"- [**{name}**]({quote(rel.as_posix())})")

(ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"README.md diperbarui: {len(files)} file")
