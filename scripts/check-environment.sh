#!/usr/bin/env sh
# Confere se o ambiente serve para instalar o ryx. Só lê; nunca altera nada.
# Saída 0 = pode instalar; 1 = falta algo essencial (Python 3.11+).
set -eu

PYTHON=${PYTHON:-python3}
status=0

ok() { printf '[ok]    %s\n' "$*"; }
warn() { printf '[aviso] %s\n' "$*"; }
fail() { printf '[FALHA] %s\n' "$*"; status=1; }

is_termux() {
  [ -n "${TERMUX_VERSION:-}" ] && return 0
  case "${PREFIX:-}" in *com.termux*) return 0 ;; esac
  return 1
}

if command -v "$PYTHON" >/dev/null 2>&1; then
  version=$("$PYTHON" -c 'import sys; print("%d.%d" % sys.version_info[:2])')
  if "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
    ok "python $version"
  else
    fail "python $version é antigo; preciso do 3.11 ou mais novo (pkg install python)"
  fi
  if "$PYTHON" -P -m pip --version >/dev/null 2>&1; then
    ok "pip disponível"
  else
    warn "pip ausente; o install.sh só consegue usar --no-pip"
  fi
else
  fail "$PYTHON não encontrado (no Termux: pkg install python)"
fi

if is_termux; then
  ok "ambiente Termux"
else
  warn "fora do Termux: o ryx roda, mas packages/server só fazem sentido no aparelho"
fi

for cmd in git curl; do
  if command -v "$cmd" >/dev/null 2>&1; then ok "$cmd"; else warn "$cmd ausente (pkg install $cmd)"; fi
done

exit "$status"
