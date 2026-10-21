#!/usr/bin/env sh
# Liga os ganchos do repositório (.githooks/) neste clone. Só muda a configuração local do git, não toca em arquivo do projeto.
set -eu
cd "$(git rev-parse --show-toplevel)"
git config core.hooksPath .githooks
echo "ganchos ligados: core.hooksPath = .githooks (pre-commit roda o ruff nos .py do commit)"
