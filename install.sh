#!/usr/bin/env sh
# Instala o ryx para o usuário atual (sem root). Pode rodar de novo: o resultado é o mesmo.
#   sh install.sh [--dry-run] [--no-pip] [--skip-doctor] [--strict]
# Variáveis: PYTHON (padrão python3), RYX_HOME (isola tudo numa pasta), RYX_PIP_ARGS.
# O python roda com -P (3.11+): a pasta atual não entra no sys.path, então um ryx/ plantado
# ali não vira o "ryx" importado; PYTHONPATH continua valendo (modo --no-pip com PYTHONPATH=src).
set -eu

REPO_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
PYTHON=${PYTHON:-python3}
DRY_RUN=0
USE_PIP=1
RUN_DOCTOR=1
STRICT=0

usage() {
  cat <<'EOF'
Uso: sh install.sh [opções]
  --dry-run       só mostra o que faria (não grava nada)
  --no-pip        não instala o pacote; só copia templates/config e roda o doctor
                  (para desenvolvimento: use com PYTHONPATH=src)
  --skip-doctor   não roda o diagnóstico no fim
  --strict        sai com 1 se o diagnóstico (doctor) reportar FALHA
  -h, --help      esta ajuda
EOF
}

say() { printf '%s\n' "$*"; }
die() { printf 'erro: %s\n' "$*" >&2; exit 1; }

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --no-pip) USE_PIP=0 ;;
    --skip-doctor) RUN_DOCTOR=0 ;;
    --strict) STRICT=1 ;;
    -h | --help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done

run() {
  if [ "$DRY_RUN" = 1 ]; then
    say "[simulação] $*"
  else
    "$@"
  fi
}

data_dir() {
  if [ -n "${RYX_HOME:-}" ]; then
    printf '%s\n' "$RYX_HOME/data"
  else
    printf '%s\n' "${XDG_DATA_HOME:-$HOME/.local/share}/ryx"
  fi
}

in_termux() {
  [ -n "${TERMUX_VERSION:-}" ] || case "${PREFIX:-}" in *com.termux*) return 0 ;; esac
  return 1
}

command -v "$PYTHON" >/dev/null 2>&1 || die "$PYTHON não encontrado (no Termux: pkg install python)"
"$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' ||
  die "é preciso Python 3.11 ou mais novo"

[ -f "$REPO_DIR/pyproject.toml" ] || die "rode o install.sh de dentro do repositório do ryx"

DATA=$(data_dir)
say "ryx: instalando a partir de $REPO_DIR"

if [ "$USE_PIP" = 1 ]; then
  if in_termux; then
    # shellcheck disable=SC2086
    run "$PYTHON" -P -m pip install --upgrade ${RYX_PIP_ARGS:-} "$REPO_DIR"
  else
    # shellcheck disable=SC2086
    run "$PYTHON" -P -m pip install --user --upgrade ${RYX_PIP_ARGS:-} "$REPO_DIR"
  fi
else
  say "pulando o pip (--no-pip)"
fi

run mkdir -p "$DATA"
run cp -R "$REPO_DIR/templates" "$DATA/"
run cp -R "$REPO_DIR/config" "$DATA/"
say "templates e config em: $DATA"

DOCTOR_FAILED=0
if [ "$RUN_DOCTOR" = 1 ] && [ "$DRY_RUN" = 0 ]; then
  say "diagnóstico:"
  "$PYTHON" -P -m ryx doctor || DOCTOR_FAILED=1
fi

say "pronto. Próximo passo: ryx shell install   (simula; use --apply para gravar)"
say "se 'ryx' não for achado, acrescente \$HOME/.local/bin ao PATH ou use: $PYTHON -m ryx"

if [ "$DOCTOR_FAILED" = 1 ]; then
  say "doctor reportou FALHA: corrija o que está marcado acima (docs/TROUBLESHOOTING.md)"
  if [ "$STRICT" = 1 ]; then
    exit 1
  fi
fi
