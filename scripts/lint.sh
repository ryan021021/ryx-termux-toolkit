#!/usr/bin/env sh
# Lint do ryx, o mesmo que o CI faz: `ruff check` + `ruff format --check`. Só lê; nunca altera arquivo.
#   scripts/lint.sh            -> o repositório inteiro
#   scripts/lint.sh --indice   -> só os .py que entram no commit (conteúdo do índice do git); é o que o gancho usa
# Saída: 0 limpo · 1 achou problema · 2 ruff não instalado (o ryx em si segue só stdlib; o ruff é ferramenta de desenvolvimento).
set -eu

cd "$(git rev-parse --show-toplevel)"

if [ -n "${RUFF:-}" ]; then
  ruff() { $RUFF "$@"; }
elif python3 -m ruff --version >/dev/null 2>&1; then
  ruff() { python3 -m ruff "$@"; }
elif python -m ruff --version >/dev/null 2>&1; then
  ruff() { python -m ruff "$@"; }
elif command -v ruff >/dev/null 2>&1; then
  ruff() { command ruff "$@"; }
else
  echo "lint: ruff nao esta instalado. Instale com: python -m pip install --user 'ruff>=0.5'" >&2
  exit 2
fi

if [ "${1:-}" != "--indice" ]; then
  status=0
  ruff check . || status=1
  ruff format --check . || status=1
  exit "$status"
fi

# Modo --indice: confere o que vai no commit, não o que está solto na pasta
arquivos=$(git diff --cached --name-only --diff-filter=ACM -- '*.py')
[ -n "$arquivos" ] || exit 0
status=0
IFS='
'
for f in $arquivos; do
  git show ":$f" | ruff check --quiet --stdin-filename "$f" - || status=1
  git show ":$f" | ruff format --check --quiet --stdin-filename "$f" - || {
    echo "lint: $f fora do formato (corrija com: ruff format $f)" >&2
    status=1
  }
done
[ "$status" -eq 0 ] || echo "lint: commit recusado. Corrija os arquivos acima e adicione de novo (git add)." >&2
exit "$status"
