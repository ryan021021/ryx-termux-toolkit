#!/usr/bin/env python3
"""Imprime as notas de uma versão a partir do CHANGELOG.md.

Uso: python scripts/generate-release-notes.py 0.1.0 [--changelog CHANGELOG.md]
Saída 0 com o texto da seção; 1 se a versão não existe ou a seção está vazia.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^## \[(?P<version>[^\]]+)\](?: - (?P<date>\S+))?\s*$")


def extract(changelog: str, version: str) -> str | None:
    """Corpo da seção `## [version]`; None se a versão não existe."""
    lines = changelog.splitlines()
    start = None
    for index, line in enumerate(lines):
        match = HEADING.match(line)
        if match and match["version"] == version:
            start = index + 1
            break
    if start is None:
        return None
    body = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    return "\n".join(body).strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("version", help="ex.: 0.1.0 (sem o 'v')")
    parser.add_argument("--changelog", default="CHANGELOG.md", type=Path)
    args = parser.parse_args(argv)
    try:
        text = args.changelog.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"erro: não consegui ler {args.changelog}: {exc.strerror}", file=sys.stderr)
        return 1
    notes = extract(text, args.version.removeprefix("v"))
    if not notes:
        print(f"erro: versão {args.version} não encontrada ou vazia em {args.changelog}", file=sys.stderr)
        return 1
    print(notes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
