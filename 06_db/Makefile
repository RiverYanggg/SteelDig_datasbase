# ---------------------------------------------------------------------------
# SteelDig 材料知识库 —— 常用操作入口
#   make up        起数据库
#   make bootstrap 一次性：建库 + 迁移 + 入库 + 质检 + 报告
#   make ingest    全量入库（幂等）
#   make test      完整性 + API 测试
#   make ui        起浏览界面 + API（http://127.0.0.1:8011/）
# ---------------------------------------------------------------------------
SHELL := /bin/bash
PY    := .venv/bin/python
PIP   := .venv/bin/pip
PORT  := 8011

.PHONY: help up down logs psql venv install migrate reset ingest qa report embed \
        docs test api verify stats bootstrap clean

help:
	@grep -E '^#   ' Makefile | sed 's/^#   //'

up:                ## 启动 PostgreSQL 16 + pgvector
	docker compose up -d db
	@echo "等待健康检查…" && sleep 3 && docker compose ps

down:              ## 停止容器（保留数据卷）
	docker compose down

logs:
	docker compose logs -f --tail=50 db

psql:              ## 进入 psql
	docker exec -it steeldig-db psql -U steeldig -d steeldig

venv:              ## 创建虚拟环境并安装依赖
	test -d .venv || python3 -m venv .venv
	$(PIP) install -q -U pip
	$(PIP) install -q -e etl -e api
	@echo "已安装 steeldig-db / steeldig-api"

install: venv

migrate:           ## 执行迁移（幂等）
	$(PY) -m steeldig_db migrate

reset:             ## [开发] 清空并重建 schema
	$(PY) -m steeldig_db reset --yes

ingest:            ## 全量入库
	$(PY) -m steeldig_db ingest --all

qa:                ## 质量门禁
	$(PY) -m steeldig_db qa

report:            ## 覆盖率报告 → 04_reports/
	$(PY) -m steeldig_db report

embed:             ## 计算语义向量（可选，需可访问 HF 或镜像）
	HF_ENDPOINT=$${HF_ENDPOINT:-https://hf-mirror.com} $(PY) -m steeldig_db embed

docs:              ## 从系统目录重建数据字典与 ER 图
	$(PY) ops/gen_docs.py

verify:            ## 校验资产湖与溯源链
	$(PY) -m steeldig_db verify

stats:             ## 控制台概览
	$(PY) -m steeldig_db stats

test:              ## 跑测试
	$(PY) -m pytest tests -q

ui:                ## 启动浏览界面 + API（同源）
	.venv/bin/uvicorn steeldig_api.main:app --host 127.0.0.1 --port $(PORT) --reload

api: ui            ## 兼容别名

bootstrap: up migrate ingest qa report docs ## 从零到可用
	@echo "完成：make api 启动服务，http://127.0.0.1:$(PORT)/docs"

clean:
	rm -rf .pytest_cache etl/*.egg-info api/*.egg-info
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
