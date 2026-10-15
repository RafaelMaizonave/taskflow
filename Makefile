# Interface principal do ambiente de desenvolvimento TaskFlow.
# A lógica operacional vive em scripts/lib/common.sh (via scripts/dev.sh).

.PHONY: help setup run stop restart logs ps test test-backend test-frontend \
	test-e2e test-infra lint format build check clean reset

ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
DEV := $(ROOT)scripts/dev.sh

help:
	@$(DEV) help

setup:
	@$(DEV) setup

run:
	@$(DEV) run

stop:
	@$(DEV) stop

restart:
	@$(DEV) restart

logs:
	@$(DEV) logs

ps:
	@$(DEV) ps

test:
	@$(DEV) test

test-backend:
	@$(DEV) test-backend

test-frontend:
	@$(DEV) test-frontend

test-e2e:
	@$(DEV) test-e2e

test-infra:
	@$(DEV) test-infra

lint:
	@$(DEV) lint

format:
	@$(DEV) format

build:
	@$(DEV) build

check:
	@$(DEV) check

clean:
	@$(DEV) clean

reset:
	@$(DEV) reset
