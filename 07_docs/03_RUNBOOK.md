# 运维手册（Runbook）

> 面向：首次搭建、日常重跑、故障排查、备份恢复、版本升级。
> 所有命令均假设工作目录为 `database/06_db`。

---

## 1. 首次搭建

```bash
cd database/06_db

# 1) 起数据库（PostgreSQL 16 + pgvector），监听 127.0.0.1:5435
cp .env.example .env
docker compose up -d db

# 2) Python 环境（Python ≥ 3.11）
python3 -m venv .venv
.venv/bin/pip install -e etl -e api

# 3) 建 schema + 受控词表
.venv/bin/python -m steeldig_db migrate

# 4) 全量入库（68 篇，约 30 秒）
.venv/bin/python -m steeldig_db ingest --all

# 5) 质量门禁 + 报告
.venv/bin/python -m steeldig_db qa
.venv/bin/python -m steeldig_db report

# 6) （可选）语义检索向量；未做则自动降级为全文+模糊
.venv/bin/python -m steeldig_db embed

# 7) 起服务（浏览界面 + REST API 同源）
.venv/bin/uvicorn steeldig_api.main:app --host 127.0.0.1 --port 8011
#    界面: http://127.0.0.1:8011/
#    API : http://127.0.0.1:8011/docs   （REST 统一在 /api 前缀下）
```

### 用 Conda 的等价环境

```bash
conda env create -f environment.yml     # 见本目录 environment.yml
conda activate steeldig
python -m steeldig_db migrate && python -m steeldig_db ingest --all
```

---

## 2. 日常操作

| 操作 | 命令 |
|---|---|
| 新增/更新若干篇 | `python -m steeldig_db ingest --papers 10.xxx 10.yyy` |
| 全量重跑（幂等） | `python -m steeldig_db ingest --all` |
| 只灌一批新批次 | 先写 `03_manifests/paper_runs.json` 增加 run，再 `ingest --papers …` |
| 跑质量门禁 | `python -m steeldig_db qa` |
| 生成报告 | `python -m steeldig_db report` |
| 校验湖完整性 | `python -m steeldig_db verify` |
| 控制台概览 | `python -m steeldig_db stats` |
| 重算向量 | `python -m steeldig_db embed` |
| 重建文档 | `python ops/gen_docs.py` |

**幂等性**：每篇论文在单事务内 `DELETE → COPY`，重复执行结果一致；
`lake.object` 按 sha256 去重，重跑只会"复用"，不会重复占空间。

---

## 3. 故障排查

| 现象 | 排查 |
|---|---|
| `ingest` 某篇 failed | `SELECT * FROM ops.ingest_log WHERE status='failed';` 看 `error`；加 `--debug` 单独重跑该篇 |
| API 500 / 连接失败 | `docker compose ps` 看容器健康；`SELECT 1` 验证 DSN |
| 语义检索 `vector_used=false` | 模型未下载或 `STEELDIG_EMBED_MODEL` 为空；`embed` 命令会打印真实原因 |
| 中文搜不到 | 检查 `content_seg` 是否已分词：`SELECT left(content_seg,120) FROM search.document LIMIT 3;` |
| 溯源断链 | `python -m steeldig_db verify`；`SELECT rule_code,count(*) FROM ops.qa_issue GROUP BY 1;` |
| 迁移 checksum 冲突 | 说明改动了已执行的迁移文件——**不要改历史迁移**，新增一个 `0NN_*.sql` |

---

## 4. 备份与恢复

```bash
# 逻辑备份（schema + 数据）
docker exec steeldig-db pg_dump -U steeldig -d steeldig -Fc > backup_$(date +%F).dump

# 恢复
docker exec -i steeldig-db pg_restore -U steeldig -d steeldig --clean --if-exists < backup.dump

# 资产湖是纯文件，直接 rsync
rsync -a --delete 05_lake/ /backup/05_lake/
```

**重建策略**：湖不可变 → 只要湖在，`reset` 后 `ingest --all` 即可完全重建 DB（约 30 s）。
这条链路就是架构图里"数据库可随时从湖重建"的具体兑现方式。

---

## 5. 升级

1. 新增 `migrations/0NN_描述.sql`；
2. `python -m steeldig_db migrate`（只执行未执行的迁移，并校验历史 checksum）；
3. 若新增列需要回填：写一次性脚本，从 `core.sample_data.payload` 重算，不要改 ETL 历史逻辑；
4. `python ops/gen_docs.py` 刷新数据字典。

开发期如确需改历史迁移，用 `.venv/bin/python -m steeldig_db reset --yes` 重建
（生产禁用，该命令不设二次确认以外的保护）。

---

## 6. 角色与权限（生产建议）

```sql
CREATE ROLE steeldig_etl LOGIN PASSWORD '...';
GRANT USAGE, CREATE ON SCHEMA core, lake, search, ops, canon TO steeldig_etl;

CREATE ROLE steeldig_api LOGIN PASSWORD '...';
GRANT USAGE ON SCHEMA api, search TO steeldig_api;
GRANT SELECT ON ALL TABLES IN SCHEMA api TO steeldig_api;
GRANT EXECUTE ON FUNCTION search.hybrid(text,text,vector,integer,text[]) TO steeldig_api;
```

API 进程只持有 `steeldig_api`，即使被攻破也无法写事实层。

---

## 7. 改名（显示名 / 包名 / 库名）

改名分三层，按代价从低到高。**只换显示名不需要动代码**。

### A. 只改显示名（1 分钟）

```bash
# 06_db/.env
STEELDIG_APP_NAME=BaoWu
```

重启服务后，界面标题、侧边栏品牌、API 文档标题一起变；数据库名、表名、包名都不动。
这是唯一推荐在"名字还没最终确定"阶段做的改动。

### B. 连包名与命令一起改（约 30 分钟）

```bash
cd database/06_db
git mv etl/steeldig_db etl/baowu_db          # 包目录
git mv api/steeldig_api api/baowu_api
grep -rl "steeldig_db\|steeldig_api" --include="*.py" --include="*.toml" --include="*.md" . \
  | xargs sed -i '' 's/steeldig_db/baowu_db/g; s/steeldig_api/baowu_api/g'
# 同步改 pyproject 的 name 与 [project.scripts] 里的命令名
.venv/bin/pip install -e etl -e api          # 重装，生成新命令
```

数据库连接串（`STEELDIG_DSN`）与库名不受影响，数据不用动。

### C. 连数据库名 / 容器名一起改（约 1 小时）

PostgreSQL 不能在自己被连接时改库名，最省事的做法是新建库 + 从湖重灌：

```bash
# 1) .env：POSTGRES_DB=baowu  STEELDIG_DSN=.../baowu
# 2) compose：container_name: baowu-db，volumes 里的卷名同步改（新卷 = 空库）
docker compose up -d db
.venv/bin/python -m steeldig_db migrate
.venv/bin/python -m steeldig_db ingest --all      # 30 秒，从 05_lake 重放
```

旧库先别删，确认新库数据对得上（`python -m steeldig_db stats` 对比行数）再删旧卷。

> 建议顺序：先把 A 定下来，等名字稳定一个版本周期后再做 B / C。
> B、C 一改，所有外部连接串、脚本、书签、PPT 里的示例都要跟着更新。
