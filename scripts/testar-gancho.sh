#!/usr/bin/env sh
# Prova que o gancho de pré-commit funciona: num repositório temporário, um .py com erro de propósito é recusado
# e um .py limpo passa. Não toca neste repositório. Saída 0 = o gancho barra e libera como deveria.
set -eu
raiz=$(cd "$(dirname "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

mkdir -p "$tmp/scripts" "$tmp/.githooks" "$tmp/src"
cp "$raiz/pyproject.toml" "$tmp/"
cp "$raiz/scripts/lint.sh" "$tmp/scripts/"
cp "$raiz/.githooks/pre-commit" "$tmp/.githooks/"
cd "$tmp"
git init -q
git config user.name teste
git config user.email teste@exemplo.invalid
git config core.hooksPath .githooks
git config commit.gpgsign false

fail() { echo "[FALHA] $*"; exit 1; }

# 0a) só o `ruff check` reprova (import sem uso, formato certo)
printf 'import os\n\nx = 1\n' > src/ruim.py
git add src/ruim.py
if git commit -q -m "deve ser recusado" >/dev/null 2>&1; then fail "o gancho deixou passar um .py com erro de lint"; fi
git rm -q --cached -f src/ruim.py
echo "[ok] erro de lint sozinho foi recusado"

# 0b) só o `ruff format --check` reprova (código correto, formato torto)
printf 'x=1\n' > src/ruim.py
git add src/ruim.py
if git commit -q -m "deve ser recusado" >/dev/null 2>&1; then fail "o gancho deixou passar um .py fora do formato"; fi
git rm -q --cached -f src/ruim.py
echo "[ok] formato torto sozinho foi recusado"

# 1) arquivo com erro de propósito (import sem uso e formato torto): o commit TEM de ser recusado
printf 'import os\nx=1\n' > src/ruim.py
git add src/ruim.py
if git commit -q -m "deve ser recusado" >/dev/null 2>&1; then fail "o gancho deixou passar um .py com erro"; fi
git rev-parse -q --verify HEAD >/dev/null 2>&1 && fail "o commit recusado mesmo assim foi criado"
echo "[ok] .py com erro foi recusado"

# 2) o erro está só no índice: corrigir na pasta sem dar git add continua recusado (o gancho olha o que vai no commit)
printf 'x = 1\n' > src/ruim.py
if git commit -q -m "ainda recusado" >/dev/null 2>&1; then fail "o gancho olhou a pasta em vez do índice"; fi
echo "[ok] correção fora do índice não libera o commit"

# 3) arquivo limpo, corrigido e adicionado: passa
git add src/ruim.py
git commit -q -m "limpo" >/dev/null 2>&1 || fail "o gancho recusou um .py limpo"
echo "[ok] .py limpo foi aceito"

# 4) commit sem nenhum .py não depende do ruff
printf 'oi\n' > nota.txt
git add nota.txt
git commit -q -m "so texto" >/dev/null 2>&1 || fail "o gancho recusou um commit sem .py"
echo "[ok] commit sem .py passa"
