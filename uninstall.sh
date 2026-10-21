#!/usr/bin/env sh
# Desfaz a instalação do ryx. Config, estado e backups ficam; só --purge --yes apaga os recursos copiados
# (templates/ e config/ dentro da pasta de dados; o resto da pasta, como backups/, nunca é tocado).
#   sh uninstall.sh [--dry-run] [--no-pip] [--purge] [--yes]
# O python roda com -P (3.11+): a pasta atual não entra no sys.path, então um ryx/ plantado
# ali não vira o "ryx" importado; PYTHONPATH continua valendo.
set -eu

PYTHON=${PYTHON:-python3}
DRY_RUN=0
USE_PIP=1
PURGE=0
YES=0

usage() {
  cat <<'EOF'
Uso: sh uninstall.sh [opções]
  --dry-run   só mostra o que faria
  --no-pip    não desinstala o pacote Python
  --purge     apaga templates/ e config/ que o install.sh copiou para a pasta de dados (exige --yes)
  --yes       confirma o --purge
  -h, --help  esta ajuda
Sempre: remove o bloco do ryx do ~/.bashrc e ~/.zshrc (com backup, via 'ryx shell uninstall').
Nunca apaga: config do usuário, estado nem backups.
EOF
}

say() { printf '%s\n' "$*"; }
die() { printf 'erro: %s\n' "$*" >&2; exit 1; }

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --no-pip) USE_PIP=0 ;;
    --purge) PURGE=1 ;;
    --yes) YES=1 ;;
    -h | --help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done

if [ "$PURGE" = 1 ] && [ "$YES" = 0 ] && [ "$DRY_RUN" = 0 ]; then
  die "--purge apaga arquivos; confirme com --yes (ou veja antes com --dry-run)"
fi

# Caminho físico (sem symlink nem barra final); se a pasta não existe, devolve como veio.
real_path() {
  (CDPATH='' cd -P -- "$1" 2>/dev/null && pwd -P) || printf '%s\n' "$1"
}

run() {
  if [ "$DRY_RUN" = 1 ]; then
    say "[simulação] $*"
  else
    "$@"
  fi
}

if [ -n "${RYX_HOME:-}" ]; then
  DATA="$RYX_HOME/data"
else
  DATA="${XDG_DATA_HOME:-$HOME/.local/share}/ryx"
fi

if command -v "$PYTHON" >/dev/null 2>&1 && "$PYTHON" -P -c 'import ryx' >/dev/null 2>&1; then
  if [ "$DRY_RUN" = 1 ]; then
    "$PYTHON" -P -m ryx shell uninstall
  else
    "$PYTHON" -P -m ryx shell uninstall --apply
  fi
else
  say "ryx não está importável; pulando a remoção do bloco do shell (remova à mão o trecho entre '# >>> ryx >>>' e '# <<< ryx <<<')"
fi

if [ "$USE_PIP" = 1 ]; then
  run "$PYTHON" -P -m pip uninstall -y ryx-termux-toolkit
fi

if [ "$PURGE" = 1 ]; then
  # Trava de segurança: só mexe na pasta de dados do ryx (…/ryx, ou RYX_HOME/data), nunca em algo genérico.
  case "$DATA" in
    "" | / | "$HOME" | "$HOME"/) die "caminho de dados suspeito, não vou apagar: '$DATA'" ;;
  esac
  if [ -n "${RYX_HOME:-}" ]; then
    real_ryx_home=$(real_path "$RYX_HOME")
    real_home=$(real_path "$HOME")
    case "$real_ryx_home" in
      / | "$real_home") die "RYX_HOME suspeito, não vou apagar nada: '$RYX_HOME'" ;;
    esac
  else
    case "$DATA" in
      */ryx) ;;
      *) die "caminho de dados suspeito, não vou apagar: $DATA" ;;
    esac
  fi
  # Fora do RYX_HOME a pasta de dados também guarda backups/: apaga só o que o install.sh copiou.
  run rm -rf -- "$DATA/templates" "$DATA/config"
  if [ "$DRY_RUN" = 1 ]; then
    say "[simulação] rmdir $DATA (só se ficar vazia)"
  else
    rmdir -- "$DATA" 2>/dev/null || true
  fi
else
  say "recursos mantidos em: $DATA (use --purge --yes para apagar)"
fi
say "config, estado e backups não foram tocados."
