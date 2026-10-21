#!/usr/bin/env sh
# Confere se a instalação do ryx está inteira. Só lê; nunca altera nada.
# Saída 0 = tudo certo; 1 = algo faltando ou quebrado.
# O python roda com -P (3.11+): um ryx/ plantado na pasta atual não vira o "ryx" importado.
set -eu

PYTHON=${PYTHON:-python3}
status=0

ok() { printf '[ok]    %s\n' "$*"; }
fail() { printf '[FALHA] %s\n' "$*"; status=1; }

if [ -n "${RYX_HOME:-}" ]; then
  DATA="$RYX_HOME/data"
else
  DATA="${XDG_DATA_HOME:-$HOME/.local/share}/ryx"
fi

if version=$("$PYTHON" -P -m ryx --version 2>/dev/null); then
  ok "$version"
else
  fail "'$PYTHON -m ryx' não roda (pacote não instalado ou fora do PYTHONPATH)"
fi

for item in config/default.toml config/modules.toml templates/bash/ryx.sh templates/zsh/ryx.zsh; do
  if [ -f "$DATA/$item" ]; then ok "$DATA/$item"; else fail "faltando $DATA/$item (rode install.sh)"; fi
done

if "$PYTHON" -P -m ryx doctor --json >/dev/null 2>&1; then
  ok "doctor sem falhas"
else
  fail "doctor apontou falhas (rode: $PYTHON -m ryx doctor)"
fi

if "$PYTHON" -P -m ryx shell status 2>/dev/null | grep -q 'não instalado'; then
  printf '[aviso] bloco do shell ainda não instalado (opcional: ryx shell install --apply)\n'
fi

exit "$status"
