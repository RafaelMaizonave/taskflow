#!/usr/bin/env bash
# Funções compartilhadas pela interface de desenvolvimento TaskFlow.
# shellcheck shell=bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE=(docker compose --project-directory "$ROOT")
DEFAULT_BACKEND_PORT=8000
DEFAULT_FRONTEND_PORT=5173

# Cores apenas em terminal interativo.
if [[ -t 1 ]]; then
  C_RESET=$'\033[0m'
  C_BOLD=$'\033[1m'
  C_RED=$'\033[31m'
  C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'
  C_CYAN=$'\033[36m'
else
  C_RESET= C_BOLD= C_RED= C_GREEN= C_YELLOW= C_CYAN=
fi

log() { printf '%s\n' "$*"; }
info() { printf '%s==>%s %s\n' "$C_CYAN" "$C_RESET" "$*"; }
ok() { printf '%sOK%s %s\n' "$C_GREEN" "$C_RESET" "$*"; }
warn() { printf '%sAtenção:%s %s\n' "$C_YELLOW" "$C_RESET" "$*" >&2; }
fail() { printf '%sErro:%s %s\n' "$C_RED" "$C_RESET" "$*" >&2; exit 1; }

step() {
  local name=$1
  shift
  info "$name"
  if ! "$@"; then
    fail "Falha em: $name"
  fi
}

require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    fail "Docker não encontrado. Instale Docker Desktop (Windows/macOS) ou Docker Engine (Linux): https://docs.docker.com/get-docker/"
  fi
  if ! docker info >/dev/null 2>&1; then
    fail "Docker está instalado, mas o daemon não está acessível. Inicie o Docker Desktop ou o serviço docker e tente novamente."
  fi
  if ! docker compose version >/dev/null 2>&1; then
    fail "Docker Compose V2 não encontrado. Atualize o Docker para uma versão com o plugin 'docker compose'."
  fi
  if ! docker network inspect web-edge >/dev/null 2>&1; then
    docker network create web-edge >/dev/null
  fi
}

read_env_value() {
  local key=$1
  local default=${2:-}
  local file=$3
  local line=""
  if [[ -f "$file" ]]; then
    line="$(grep -E "^${key}=" "$file" 2>/dev/null | tail -n 1 || true)"
    if [[ -n "$line" ]]; then
      printf '%s' "${line#*=}"
      return 0
    fi
  fi
  printf '%s' "$default"
}

backend_port() {
  local from_env from_file
  from_env="${BACKEND_PORT:-}"
  if [[ -n "$from_env" ]]; then
    printf '%s' "$from_env"
    return
  fi
  from_file="$(read_env_value BACKEND_PORT "$DEFAULT_BACKEND_PORT" "$ROOT/.env")"
  printf '%s' "${from_file:-$DEFAULT_BACKEND_PORT}"
}

frontend_port() {
  local from_env from_file
  from_env="${FRONTEND_PORT:-}"
  if [[ -n "$from_env" ]]; then
    printf '%s' "$from_env"
    return
  fi
  from_file="$(read_env_value FRONTEND_PORT "$DEFAULT_FRONTEND_PORT" "$ROOT/.env")"
  printf '%s' "${from_file:-$DEFAULT_FRONTEND_PORT}"
}

# Gera .env na raiz sem exibir o segredo e sem sobrescrever arquivo existente.
ensure_root_env() {
  local env_file="$ROOT/.env"
  local tmp secret_len

  if [[ -f "$env_file" ]]; then
    secret_len="$(read_env_value JWT_SECRET "" "$env_file" | tr -d '\r\n' | wc -c | tr -d ' ')"
    if [[ -z "$(read_env_value JWT_SECRET "" "$env_file")" ]]; then
      fail "Arquivo .env existe, mas JWT_SECRET está vazio. Defina um segredo com pelo menos 32 caracteres (veja .env.example)."
    fi
    if [[ "$secret_len" -lt 32 ]]; then
      fail "JWT_SECRET em .env tem menos de 32 caracteres. Ajuste o valor sem versionar o arquivo."
    fi
    ok ".env na raiz já configurado"
    return 0
  fi

  info "Criando .env na raiz com JWT_SECRET seguro (o valor não será exibido)"
  require_docker
  tmp="$(mktemp "$ROOT/.env.tmp.XXXXXX")"
  chmod 600 "$tmp"

  # Escrita do segredo dentro do contêiner; o host só move o arquivo.
  if ! docker run --rm \
    -v "$tmp:/out/.env" \
    python:3.12-slim-bookworm \
    python -c 'from pathlib import Path; import secrets; Path("/out/.env").write_text("JWT_SECRET=" + secrets.token_urlsafe(48) + "\n", encoding="utf-8")'; then
    rm -f "$tmp"
    fail "Não foi possível gerar JWT_SECRET via imagem Python. Verifique a rede/daemon Docker."
  fi

  # mv -n: se outra execução criou .env primeiro, preserva o existente.
  if [[ -f "$env_file" ]]; then
    rm -f "$tmp"
    ok ".env criado por outro processo; mantendo o existente"
    return 0
  fi
  mv -n "$tmp" "$env_file" 2>/dev/null || true
  if [[ -f "$tmp" ]]; then
    # Destino já existia (corrida) ou a movimentação falhou.
    rm -f "$tmp"
    if [[ -f "$env_file" ]]; then
      ok ".env criado por outro processo; mantendo o existente"
      return 0
    fi
    fail "Falha ao gravar .env"
  fi
  chmod 600 "$env_file" 2>/dev/null || true
  ok ".env criado (JWT_SECRET não exibido)"
}

cmd_help() {
  cat <<'EOF'
TaskFlow — interface de desenvolvimento

Uso:
  make <comando>
  ./scripts/dev.sh <comando>
  .\scripts\dev.ps1 <comando>

Comandos:
  help            Exibe esta ajuda
  setup           Valida Docker e prepara .env
  run             Prepara, constrói (se preciso) e inicia a aplicação
  stop            Para os serviços (preserva o banco)
  restart         Reinicia os serviços (preserva o banco)
  logs            Acompanha logs (use SERVICE=backend|frontend)
  ps              Estado dos contêineres
  test            Pytest + Vitest + Playwright
  test-backend    Qualidade e testes do backend
  test-frontend   Lint, tipos e Vitest
  test-e2e        Playwright (imagem isolada)
  test-infra      Validação isolada do Compose
  lint            Ruff + ESLint + typecheck
  format          Formata backend (Ruff) e frontend (ESLint --fix)
  build           Constrói imagens
  check           Lint + testes + build do frontend
  clean           Remove contêineres/órfãos sem apagar o volume
  reset           Apaga contêineres e o volume do banco (pede confirmação)

Variáveis opcionais:
  BACKEND_PORT    Porta publicada do backend (padrão 8000)
  FRONTEND_PORT   Porta publicada do frontend (padrão 5173)
  SERVICE         Serviço para logs (padrão: todos)
EOF
}

cmd_setup() {
  require_docker
  ensure_root_env
  step "Validando docker-compose.yml" "${COMPOSE[@]}" config --quiet
  ok "Ambiente pronto"
}

cmd_build() {
  require_docker
  ensure_root_env
  step "Construindo imagens" "${COMPOSE[@]}" build
  ok "Imagens construídas"
}

cmd_run() {
  local bp fp
  require_docker
  ensure_root_env
  step "Validando configuração" "${COMPOSE[@]}" config --quiet
  step "Construindo imagens (cache reutilizado quando possível)" "${COMPOSE[@]}" build
  step "Iniciando serviços" "${COMPOSE[@]}" up -d --wait --remove-orphans
  bp="$(backend_port)"
  fp="$(frontend_port)"
  ok "Aplicação em execução"
  log ""
  log "${C_BOLD}Acesse:${C_RESET}"
  log "  Frontend:  http://localhost:${fp}"
  log "  API docs:  http://localhost:${bp}/docs"
  log "  Health:    http://localhost:${bp}/health"
  log ""
  log "Logs: make logs   |   Parar: make stop"
}

cmd_stop() {
  require_docker
  step "Parando serviços (volume do banco preservado)" "${COMPOSE[@]}" down --remove-orphans
  ok "Serviços parados"
}

cmd_restart() {
  require_docker
  ensure_root_env
  step "Reiniciando serviços" "${COMPOSE[@]}" up -d --wait --force-recreate --remove-orphans
  ok "Serviços reiniciados"
  log "  Frontend: http://localhost:$(frontend_port)"
  log "  API docs: http://localhost:$(backend_port)/docs"
}

cmd_logs() {
  require_docker
  local service="${SERVICE:-}"
  if [[ -n "$service" ]]; then
    "${COMPOSE[@]}" logs -f "$service"
  else
    "${COMPOSE[@]}" logs -f
  fi
}

cmd_ps() {
  require_docker
  "${COMPOSE[@]}" ps
}

cmd_test_backend() {
  require_docker
  ensure_root_env
  step "Ruff check (backend)" "${COMPOSE[@]}" run --rm --no-deps backend-quality
  step "Ruff format --check (backend)" "${COMPOSE[@]}" run --rm --no-deps backend-quality uv run ruff format --check .
  step "Pytest (backend)" "${COMPOSE[@]}" run --rm --no-deps backend-quality uv run pytest -q
  ok "Testes backend concluídos"
}

cmd_test_frontend() {
  require_docker
  ensure_root_env
  step "ESLint (frontend)" "${COMPOSE[@]}" run --rm --no-deps frontend npm run lint
  step "Typecheck (frontend)" "${COMPOSE[@]}" run --rm --no-deps frontend npm run typecheck
  step "Vitest (frontend)" "${COMPOSE[@]}" run --rm --no-deps frontend npm run test:unit
  ok "Testes frontend concluídos"
}

cmd_test_e2e() {
  require_docker
  ensure_root_env
  step "Playwright E2E" "${COMPOSE[@]}" run --build --rm e2e
  ok "Testes E2E concluídos"
}

cmd_test() {
  cmd_test_backend
  cmd_test_frontend
  cmd_test_e2e
  ok "Todos os testes concluídos"
}

cmd_test_infra() {
  require_docker
  info "Validação isolada do Compose (projeto e volume temporários)"
  # Preferir Python do host quando disponível (mesmo fluxo do CI).
  if command -v python3 >/dev/null 2>&1; then
    if ! (cd "$ROOT" && python3 scripts/validate_compose.py); then
      fail "Falha em: validação de infraestrutura Compose"
    fi
    ok "Validação de infraestrutura concluída"
    return 0
  fi
  # Sem Python no host: CLI Docker + Python na imagem.
  # Monta o repo no mesmo caminho absoluto para bind mounts do Compose
  # resolvidos pelo daemon no host (ex.: ./backend/app).
  if ! docker run --rm \
    -v "$ROOT:$ROOT" \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -w "$ROOT" \
    docker:27-cli \
    sh -c 'apk add --no-cache python3 >/dev/null && python3 scripts/validate_compose.py'; then
    fail "Falha em: validação de infraestrutura Compose"
  fi
  ok "Validação de infraestrutura concluída"
}

cmd_lint() {
  require_docker
  ensure_root_env
  step "Ruff check" "${COMPOSE[@]}" run --rm --no-deps backend-quality
  step "Ruff format --check" "${COMPOSE[@]}" run --rm --no-deps backend-quality uv run ruff format --check .
  step "ESLint" "${COMPOSE[@]}" run --rm --no-deps frontend npm run lint
  step "TypeScript typecheck" "${COMPOSE[@]}" run --rm --no-deps frontend npm run typecheck
  ok "Lint concluído"
}

cmd_format() {
  require_docker
  ensure_root_env
  step "Ruff format" "${COMPOSE[@]}" run --rm --no-deps backend-quality uv run ruff format .
  step "ESLint --fix" "${COMPOSE[@]}" run --rm --no-deps frontend npx eslint . --fix
  ok "Formatação concluída"
}

cmd_check() {
  cmd_lint
  step "Pytest" "${COMPOSE[@]}" run --rm --no-deps backend-quality uv run pytest -q
  step "Vitest" "${COMPOSE[@]}" run --rm --no-deps frontend npm run test:unit
  step "Build frontend" "${COMPOSE[@]}" run --rm --no-deps frontend npm run build
  step "Playwright E2E" "${COMPOSE[@]}" run --build --rm e2e
  ok "check concluído: qualidade, testes e build aprovados"
}

cmd_clean() {
  require_docker
  info "Removendo contêineres e órfãos (volume taskflow-data preservado)"
  "${COMPOSE[@]}" --profile tools --profile tests down --remove-orphans || true
  "${COMPOSE[@]}" down --remove-orphans || true
  ok "Limpeza concluída (banco persistente intacto)"
}

cmd_reset() {
  require_docker
  {
    log ""
    log "${C_YELLOW}Atenção:${C_RESET} isto irá:"
    log "  - parar e remover contêineres do projeto"
    log "  - APAGAR o volume Docker 'taskflow-data' (banco SQLite)"
    log "  - preservar o arquivo .env"
    log ""
  } >&2
  if [[ "${RESET_CONFIRM:-}" == "yes" ]]; then
    info "Confirmação via RESET_CONFIRM=yes"
  elif [[ -t 0 ]]; then
    printf 'Digite %sreset%s para confirmar: ' "$C_BOLD" "$C_RESET" >&2
    local answer
    read -r answer
    if [[ "$answer" != "reset" ]]; then
      fail "Reset cancelado"
    fi
  else
    fail "Reset exige confirmação. Execute interativamente ou use RESET_CONFIRM=yes"
  fi
  step "Removendo contêineres e volume do banco" "${COMPOSE[@]}" --profile tools --profile tests down --volumes --remove-orphans
  ok "Ambiente reinicializado (dados do volume apagados; .env preservado)"
}

dispatch() {
  local cmd=${1:-help}
  shift || true
  case "$cmd" in
    help|-h|--help) cmd_help ;;
    setup) cmd_setup ;;
    run) cmd_run ;;
    stop) cmd_stop ;;
    restart) cmd_restart ;;
    logs) cmd_logs ;;
    ps) cmd_ps ;;
    test) cmd_test ;;
    test-backend) cmd_test_backend ;;
    test-frontend) cmd_test_frontend ;;
    test-e2e) cmd_test_e2e ;;
    test-infra) cmd_test_infra ;;
    lint) cmd_lint ;;
    format) cmd_format ;;
    build) cmd_build ;;
    check) cmd_check ;;
    clean) cmd_clean ;;
    reset) cmd_reset ;;
    *) fail "Comando desconhecido: $cmd (use: help)" ;;
  esac
}
