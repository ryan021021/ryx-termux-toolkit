#!/usr/bin/env sh
# Baixa o ryx de um repositório git e roda o install.sh. Não há URL padrão: informe a sua.
#   RYX_REPO_URL=<url> RYX_COMMIT=<sha completo> [RYX_REF=main] sh bootstrap.sh [opções do install.sh]
# O commit baixado precisa ser exatamente RYX_COMMIT (senão aborta). Sem RYX_COMMIT o script recusa,
# a menos que você aceite o risco com RYX_INSECURE=1 (instala sem conferir o que foi baixado).
set -eu

say() { printf '%s\n' "$*"; }
die() { printf 'erro: %s\n' "$*" >&2; exit 1; }

[ -n "${RYX_REPO_URL:-}" ] || die "defina RYX_REPO_URL (ex.: RYX_REPO_URL=git@exemplo:ryx-termux-toolkit.git)"
if [ -z "${RYX_COMMIT:-}" ] && [ "${RYX_INSECURE:-}" != 1 ]; then
  die "defina RYX_COMMIT=<sha completo do commit> para conferir o que será instalado (ou, por sua conta e risco, RYX_INSECURE=1)"
fi
RYX_REF=${RYX_REF:-main}
command -v git >/dev/null 2>&1 || die "git não encontrado (no Termux: pkg install git)"

WORK=$(mktemp -d)
# Ctrl-C/kill: sai com 130 (e o trap de EXIT limpa); só o trap de EXIT apaga a pasta.
trap 'rm -rf -- "$WORK"' EXIT
trap 'exit 130' INT TERM

say "baixando $RYX_REPO_URL ($RYX_REF)"
git clone --quiet --depth 1 --branch "$RYX_REF" -- "$RYX_REPO_URL" "$WORK/ryx"

if [ -n "${RYX_COMMIT:-}" ]; then
  got=$(git -C "$WORK/ryx" rev-parse HEAD)
  [ "$got" = "$RYX_COMMIT" ] || die "commit baixado ($got) difere do esperado ($RYX_COMMIT)"
  say "commit conferido: $got"
else
  say "aviso: RYX_INSECURE=1 e RYX_COMMIT não definido; o commit baixado não foi conferido"
fi

sh "$WORK/ryx/install.sh" "$@"
