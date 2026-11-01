"""Verifica links locais em Markdown sem acessar fontes externas."""

import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
documents = [ROOT / "README.md", ROOT / "AGENTS.md", *ROOT.joinpath("docs").rglob("*.md")]
failures = []
checked = 0
for document in documents:
    content = document.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)]+)\)", content):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        relative = unquote(target.split("#", 1)[0]).strip("<>")
        if not (document.parent / relative).resolve().is_file():
            failures.append(f"{document.relative_to(ROOT)}: {target}")
        checked += 1
if failures:
    raise SystemExit("Links locais inválidos:\n" + "\n".join(failures))
print(f"Documentação: {len(documents)} arquivos e {checked} links locais verificados.")
