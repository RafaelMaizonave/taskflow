# Interface CLI para Windows PowerShell (Docker Desktop).
# Espelha scripts/dev.sh / scripts/lib/common.sh sem exigir Make ou Bash.
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Command = "help",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Rest
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

function Write-Info([string]$Message) { Write-Host "==> $Message" -ForegroundColor Cyan }
function Write-Ok([string]$Message) { Write-Host "OK $Message" -ForegroundColor Green }
function Write-Warn([string]$Message) { Write-Host "Atenção: $Message" -ForegroundColor Yellow }
function Fail([string]$Message) {
    Write-Host "Erro: $Message" -ForegroundColor Red
    exit 1
}

function Invoke-Step([string]$Name, [scriptblock]$Action) {
    Write-Info $Name
    try {
        & $Action
        if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) {
            Fail "Falha em: $Name"
        }
    }
    catch {
        Fail "Falha em: $Name — $_"
    }
}

function Require-Docker {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Fail "Docker não encontrado. Instale Docker Desktop: https://docs.docker.com/desktop/setup/install/windows-install/"
    }
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Fail "Docker está instalado, mas o daemon não está acessível. Inicie o Docker Desktop e tente novamente."
    }
    docker compose version 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Fail "Docker Compose V2 não encontrado. Atualize o Docker Desktop."
    }
    docker network inspect web-edge 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        docker network create web-edge | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Fail "Não foi possível criar a rede Docker web-edge."
        }
    }
}

function Get-EnvValue([string]$Key, [string]$Default = "") {
    $path = Join-Path $Root ".env"
    if (-not (Test-Path $path)) { return $Default }
    $line = Get-Content $path | Where-Object { $_ -match "^$Key=" } | Select-Object -Last 1
    if (-not $line) { return $Default }
    return $line.Substring($Key.Length + 1)
}

function Get-BackendPort {
    if ($env:BACKEND_PORT) { return $env:BACKEND_PORT }
    $v = Get-EnvValue "BACKEND_PORT" "8000"
    if ([string]::IsNullOrWhiteSpace($v)) { return "8000" }
    return $v
}

function Get-FrontendPort {
    if ($env:FRONTEND_PORT) { return $env:FRONTEND_PORT }
    $v = Get-EnvValue "FRONTEND_PORT" "5173"
    if ([string]::IsNullOrWhiteSpace($v)) { return "5173" }
    return $v
}

function Ensure-RootEnv {
    $envFile = Join-Path $Root ".env"
    if (Test-Path $envFile) {
        $secret = Get-EnvValue "JWT_SECRET" ""
        if ([string]::IsNullOrWhiteSpace($secret)) {
            Fail "Arquivo .env existe, mas JWT_SECRET está vazio. Defina um segredo com pelo menos 32 caracteres."
        }
        if ($secret.Trim().Length -lt 32) {
            Fail "JWT_SECRET em .env tem menos de 32 caracteres."
        }
        Write-Ok ".env na raiz já configurado"
        return
    }

    Write-Info "Criando .env na raiz com JWT_SECRET seguro (o valor não será exibido)"
    Require-Docker
    $tmp = Join-Path $Root (".env.tmp." + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType File -Path $tmp -Force | Out-Null

    docker run --rm -v "${tmp}:/out/.env" python:3.12-slim-bookworm `
        python -c "from pathlib import Path; import secrets; Path('/out/.env').write_text('JWT_SECRET=' + secrets.token_urlsafe(48) + chr(10), encoding='utf-8')"
    if ($LASTEXITCODE -ne 0) {
        Remove-Item -Force $tmp -ErrorAction SilentlyContinue
        Fail "Não foi possível gerar JWT_SECRET via imagem Python."
    }

    if (Test-Path $envFile) {
        Remove-Item -Force $tmp -ErrorAction SilentlyContinue
        Write-Ok ".env criado por outro processo; mantendo o existente"
        return
    }

    try {
        Move-Item -Path $tmp -Destination $envFile -ErrorAction Stop
    }
    catch {
        if (Test-Path $envFile) {
            Remove-Item -Force $tmp -ErrorAction SilentlyContinue
            Write-Ok ".env criado por outro processo; mantendo o existente"
            return
        }
        Remove-Item -Force $tmp -ErrorAction SilentlyContinue
        Fail "Falha ao gravar .env"
    }
    Write-Ok ".env criado (JWT_SECRET não exibido)"
}

function Invoke-Compose {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    & docker compose --project-directory $Root @Args
    return $LASTEXITCODE
}

function Show-Help {
    @"
TaskFlow — interface de desenvolvimento

Uso:
  make <comando>
  ./scripts/dev.sh <comando>
  .\scripts\dev.ps1 <comando>

Comandos:
  help, setup, run, stop, restart, logs, ps
  test, test-backend, test-frontend, test-e2e, test-infra
  lint, format, build, check, clean, reset

Variáveis opcionais: BACKEND_PORT, FRONTEND_PORT, SERVICE, RESET_CONFIRM=yes
"@ | Write-Host
}

switch ($Command.ToLowerInvariant()) {
    { $_ -in @("help", "-h", "--help") } { Show-Help }

    "setup" {
        Require-Docker
        Ensure-RootEnv
        Invoke-Step "Validando docker-compose.yml" { Invoke-Compose config --quiet | Out-Null }
        Write-Ok "Ambiente pronto"
    }

    "build" {
        Require-Docker
        Ensure-RootEnv
        Invoke-Step "Construindo imagens" { Invoke-Compose build | Out-Null; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Write-Ok "Imagens construídas"
    }

    "run" {
        Require-Docker
        Ensure-RootEnv
        Invoke-Step "Validando configuração" { Invoke-Compose config --quiet | Out-Null }
        Invoke-Step "Construindo imagens (cache reutilizado quando possível)" { Invoke-Compose build; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Invoke-Step "Iniciando serviços" { Invoke-Compose up -d --wait --remove-orphans; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        $bp = Get-BackendPort
        $fp = Get-FrontendPort
        Write-Ok "Aplicação em execução"
        Write-Host ""
        Write-Host "Acesse:"
        Write-Host "  Frontend:  http://localhost:$fp"
        Write-Host "  API docs:  http://localhost:${bp}/docs"
        Write-Host "  Health:    http://localhost:${bp}/health"
    }

    "stop" {
        Require-Docker
        Invoke-Step "Parando serviços (volume do banco preservado)" { Invoke-Compose down --remove-orphans; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Write-Ok "Serviços parados"
    }

    "restart" {
        Require-Docker
        Ensure-RootEnv
        Invoke-Step "Reiniciando serviços" { Invoke-Compose up -d --wait --force-recreate --remove-orphans; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Write-Ok "Serviços reiniciados"
        Write-Host "  Frontend: http://localhost:$(Get-FrontendPort)"
        Write-Host "  API docs: http://localhost:$(Get-BackendPort)/docs"
    }

    "logs" {
        Require-Docker
        if ($env:SERVICE) {
            Invoke-Compose logs -f $env:SERVICE
        }
        else {
            Invoke-Compose logs -f
        }
    }

    "ps" {
        Require-Docker
        Invoke-Compose ps
    }

    "test-backend" {
        Require-Docker
        Ensure-RootEnv
        Invoke-Step "Ruff check (backend)" { Invoke-Compose run --rm --no-deps backend-quality; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Invoke-Step "Ruff format --check (backend)" { Invoke-Compose run --rm --no-deps backend-quality uv run ruff format --check .; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Invoke-Step "Pytest (backend)" { Invoke-Compose run --rm --no-deps backend-quality uv run pytest -q; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Write-Ok "Testes backend concluídos"
    }

    "test-frontend" {
        Require-Docker
        Ensure-RootEnv
        Invoke-Step "ESLint (frontend)" { Invoke-Compose run --rm --no-deps frontend npm run lint; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Invoke-Step "Typecheck (frontend)" { Invoke-Compose run --rm --no-deps frontend npm run typecheck; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Invoke-Step "Vitest (frontend)" { Invoke-Compose run --rm --no-deps frontend npm run test:unit; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Write-Ok "Testes frontend concluídos"
    }

    "test-e2e" {
        Require-Docker
        Ensure-RootEnv
        Invoke-Step "Playwright E2E" { Invoke-Compose run --build --rm e2e; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Write-Ok "Testes E2E concluídos"
    }

    "test" {
        & $PSCommandPath test-backend
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & $PSCommandPath test-frontend
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & $PSCommandPath test-e2e
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        Write-Ok "Todos os testes concluídos"
    }

    "test-infra" {
        Require-Docker
        Write-Info "Validação isolada do Compose (projeto e volume temporários)"
        $python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
        if ($python) {
            Push-Location $Root
            try {
                & $python.Source scripts/validate_compose.py
                if ($LASTEXITCODE -ne 0) { Fail "Falha em: validação de infraestrutura Compose" }
            }
            finally { Pop-Location }
        }
        else {
            # Mesmo caminho absoluto: bind mounts do Compose devem existir no host.
            docker run --rm `
                -v "${Root}:${Root}" `
                -v "/var/run/docker.sock:/var/run/docker.sock" `
                -w $Root `
                docker:27-cli `
                sh -c "apk add --no-cache python3 >/dev/null && python3 scripts/validate_compose.py"
            if ($LASTEXITCODE -ne 0) { Fail "Falha em: validação de infraestrutura Compose" }
        }
        Write-Ok "Validação de infraestrutura concluída"
    }

    "lint" {
        Require-Docker
        Ensure-RootEnv
        Invoke-Step "Ruff check" { Invoke-Compose run --rm --no-deps backend-quality; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Invoke-Step "Ruff format --check" { Invoke-Compose run --rm --no-deps backend-quality uv run ruff format --check .; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Invoke-Step "ESLint" { Invoke-Compose run --rm --no-deps frontend npm run lint; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Invoke-Step "TypeScript typecheck" { Invoke-Compose run --rm --no-deps frontend npm run typecheck; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Write-Ok "Lint concluído"
    }

    "format" {
        Require-Docker
        Ensure-RootEnv
        Invoke-Step "Ruff format" { Invoke-Compose run --rm --no-deps backend-quality uv run ruff format .; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Invoke-Step "ESLint --fix" { Invoke-Compose run --rm --no-deps frontend npx eslint . --fix; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Write-Ok "Formatação concluída"
    }

    "check" {
        & $PSCommandPath lint
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        Require-Docker
        Invoke-Step "Pytest" { Invoke-Compose run --rm --no-deps backend-quality uv run pytest -q; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Invoke-Step "Vitest" { Invoke-Compose run --rm --no-deps frontend npm run test:unit; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Invoke-Step "Build frontend" { Invoke-Compose run --rm --no-deps frontend npm run build; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Invoke-Step "Playwright E2E" { Invoke-Compose run --build --rm e2e; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }
        Write-Ok "check concluído: qualidade, testes e build aprovados"
    }

    "clean" {
        Require-Docker
        Write-Info "Removendo contêineres e órfãos (volume taskflow-data preservado)"
        Invoke-Compose --profile tools --profile tests down --remove-orphans | Out-Null
        Invoke-Compose down --remove-orphans | Out-Null
        Write-Ok "Limpeza concluída (banco persistente intacto)"
    }

    "reset" {
        Require-Docker
        Write-Host ""
        Write-Warn "Isto irá:"
        Write-Host "  - parar e remover contêineres do projeto"
        Write-Host "  - APAGAR o volume Docker 'taskflow-data' (banco SQLite)"
        Write-Host "  - preservar o arquivo .env"
        Write-Host ""
        if ($env:RESET_CONFIRM -eq "yes") {
            Write-Info "Confirmação via RESET_CONFIRM=yes"
        }
        else {
            $answer = Read-Host "Digite reset para confirmar"
            if ($answer -ne "reset") { Fail "Reset cancelado" }
        }
        Invoke-Step "Removendo contêineres e volume do banco" {
            Invoke-Compose --profile tools --profile tests down --volumes --remove-orphans
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        }
        Write-Ok "Ambiente reinicializado (dados do volume apagados; .env preservado)"
    }

    default { Fail "Comando desconhecido: $Command (use: help)" }
}
