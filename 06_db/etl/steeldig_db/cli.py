"""SteelDig 知识库命令行。

    python -m steeldig_db migrate                 初始化/升级 schema
    python -m steeldig_db ingest --all            全量入库（幂等，可重跑）
    python -m steeldig_db ingest --papers X Y     指定论文重跑
    python -m steeldig_db qa                      跑质量门禁
    python -m steeldig_db report                  生成覆盖率报告
    python -m steeldig_db embed                   计算语义向量（可选）
    python -m steeldig_db verify                  校验资产湖完整性
    python -m steeldig_db stats                   控制台概览
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

from . import __version__, qa
from . import curate as curation
from .config import REPO_HOME, settings
from .db import connect, migrate
from .ingest import COLS, PaperIngest, load_paper
from .lake import Lake
from .resolve import load_resolvers


# ---------------------------------------------------------------------------
# 运行版本
# ---------------------------------------------------------------------------
def load_run_map() -> dict:
    p = settings.manifests_root / "paper_runs.json"
    if not p.exists():
        return {"runs": {}, "papers": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def ensure_runs(conn, runmap: dict) -> dict[str, str]:
    """把 run 定义写入 ops.run，返回 paper_id → run_id 映射。"""
    papers = runmap.get("papers") or {}
    used = {}
    for pid, meta in papers.items():
        used.setdefault(meta["run_id"], 0)
        used[meta["run_id"]] += 1

    for rid, meta in (runmap.get("runs") or {}).items():
        conn.execute("""
            INSERT INTO ops.run (run_id, label, model, source_batch, dataset_version,
                                 schema_versions, paper_count)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (run_id) DO UPDATE
               SET label = EXCLUDED.label, model = EXCLUDED.model,
                   source_batch = EXCLUDED.source_batch, paper_count = EXCLUDED.paper_count
        """, (rid, meta["label"], meta.get("model"), meta.get("source_batch"),
              settings.dataset_version,
              json.dumps({"preprocess": "preprocess-manifest-v1",
                          "evidence": "evidence-blocks-v1",
                          "discover": "sample-discover-v1",
                          "figure": "figure-evidence-v1"}), used.get(rid, 0)))

    if not used:
        conn.execute("""
            INSERT INTO ops.run (run_id, label, dataset_version, paper_count)
            VALUES ('run_default','default','%s',0) ON CONFLICT DO NOTHING
        """ % settings.dataset_version)
    return {pid: meta["run_id"] for pid, meta in papers.items()}


# ---------------------------------------------------------------------------
# 命令
# ---------------------------------------------------------------------------
def cmd_migrate(args) -> int:
    print("执行迁移：")
    applied = migrate()
    print(f"完成，新执行 {len(applied)} 个迁移" if applied else "已是最新，无需迁移")
    return 0


def cmd_reset(args) -> int:
    """开发用：清空全部 schema 后重建。生产禁止使用。"""
    if not args.yes:
        print("这会删除所有数据。确认请加 --yes")
        return 1
    with connect(autocommit=True) as conn:
        conn.execute("DROP SCHEMA IF EXISTS ops, lake, core, canon, search, api CASCADE")
    print("已清空 schema，重新执行迁移：")
    migrate()
    return 0


def cmd_ingest(args) -> int:
    papers = sorted([p.name for p in settings.extraction_root.iterdir()
                     if p.is_dir() and p.name.startswith("10.")])
    if args.papers:
        wanted = set(args.papers)
        papers = [p for p in papers if p in wanted]
        missing = wanted - set(papers)
        if missing:
            print(f"⚠ 未找到：{sorted(missing)}")
    if args.limit:
        papers = papers[: args.limit]
    if not papers:
        print("没有待入库的论文")
        return 1

    print(f"资产根：{settings.extraction_root}")
    print(f"湖根  ：{settings.lake_root}")
    print(f"论文数：{len(papers)}")

    lake = Lake(settings.lake_root)
    runmap = load_run_map()
    t_start = time.time()
    total_rows: dict[str, int] = {}
    failed: list[str] = []

    with connect() as conn:
        ingest_id = conn.execute(
            "INSERT INTO ops.ingest_run (label, params, tool_version) VALUES (%s,%s,%s)"
            " RETURNING ingest_id",
            (args.label or "ingest", json.dumps({k: str(v) for k, v in vars(args).items() if k != "func"}, ensure_ascii=False), __version__),
        ).fetchone()[0]
        run_by_paper = ensure_runs(conn, runmap)
        families = [dict(family_key=r[0], rule=r[1], parent_key=r[2])
                    for r in conn.execute(
                        "SELECT family_key, rule, parent_key FROM canon.alloy_family").fetchall()]
        conn.commit()

        phase_resolver, technique_resolver = load_resolvers(conn)
        ctx = PaperIngest(settings, lake, families, run_id="", ingest_id=ingest_id,
                          phase_resolver=phase_resolver,
                          technique_resolver=technique_resolver)

        for i, pid in enumerate(papers, 1):
            run_id = run_by_paper.get(pid, "run_default")
            ctx.run_id = run_id
            t0 = time.time()
            try:
                result = ctx.process(pid)
                counts = load_paper(conn, result)
                conn.commit()
                for k, v in counts.items():
                    total_rows[k] = total_rows.get(k, 0) + v
                ms = int((time.time() - t0) * 1000)
                conn.execute(
                    "INSERT INTO ops.ingest_log (ingest_id, paper_id, run_id, status, rows, objects, duration_ms)"
                    " VALUES (%s,%s,%s,'loaded',%s,%s,%s)"
                    " ON CONFLICT (ingest_id, paper_id) DO UPDATE SET status='loaded'",
                    (ingest_id, pid, run_id, json.dumps(counts), len(result.objects), ms))
                conn.commit()
                print(f"[{i:>3}/{len(papers)}] ✓ {pid}  {ms:>5} ms  "
                      f"rows={sum(counts.values()):>5}  obj={len(result.objects):>3}")
            except Exception as exc:  # noqa: BLE001 — 单篇失败不阻断整批
                conn.rollback()
                failed.append(pid)
                conn.execute(
                    "INSERT INTO ops.ingest_log (ingest_id, paper_id, run_id, status, error)"
                    " VALUES (%s,%s,%s,'failed',%s)"
                    " ON CONFLICT (ingest_id, paper_id) DO UPDATE SET status='failed', error=EXCLUDED.error",
                    (ingest_id, pid, run_id, f"{type(exc).__name__}: {exc}"))
                conn.commit()
                print(f"[{i:>3}/{len(papers)}] ✗ {pid}  {type(exc).__name__}: {exc}")
                if args.debug:
                    traceback.print_exc()

        # 重放人工校订：core 刚刚被重建，人的修改必须重新生效
        cured = curation.apply_changes(conn)
        conn.execute("UPDATE ops.ingest_run SET status=%s, finished_at=now(), stats=%s WHERE ingest_id=%s",
                     ("success" if not failed else "partial", json.dumps(total_rows), ingest_id))
        conn.commit()

    dur = time.time() - t_start
    print("\n— 汇总 —")
    for k, v in sorted(total_rows.items()):
        print(f"  {k:<26} {v:>8,}")
    print(f"  耗时 {dur:.1f}s，失败 {len(failed)} 篇")
    if failed:
        print("  失败：", ", ".join(failed))
    print(f"湖：写入 {lake.stats['written']} 个新对象，复用 {lake.stats['reused']} 个已有对象")
    print(f"校订：重放 {cured['applied']} 条生效校订（失败 {cured['failed']}）")
    return 0 if not failed else 2


def cmd_qa(args) -> int:
    with connect() as conn:
        ingest_id = conn.execute(
            "SELECT coalesce(max(ingest_id),0) FROM ops.ingest_run").fetchone()[0]
        # 这三条规则是"全库扫描"型，每次重算前先清空（与 ingest_id 无关）
        conn.execute("""DELETE FROM ops.qa_issue
                        WHERE rule_code IN ('TRACE_PATH_MISSING','BLOCK_ID_DANGLING','DUPLICATE_TITLE')""")
        issues: list[dict] = []
        issues += qa.check_trace_paths(conn, ingest_id)
        issues += qa.check_dangling_blocks(conn)
        issues += qa.check_duplicate_titles(conn)
        n = qa.persist(conn, ingest_id, issues)
        conn.commit()
        print(f"质量门禁：写入 {n} 条问题（ingest_id={ingest_id}）")
        for r in conn.execute("""SELECT rule_code, severity, count(*) FROM ops.qa_issue
                                 GROUP BY 1,2 ORDER BY 3 DESC""").fetchall():
            print(f"  {r[0]:<26} {r[1]:<6} {r[2]:>6}")
    return 0


def cmd_report(args) -> int:
    out_dir = args.out or (REPO_HOME / "04_reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        ingest_id = conn.execute("SELECT coalesce(max(ingest_id),0) FROM ops.ingest_run").fetchone()[0]
        rep = qa.report(conn)
    (out_dir / "qa_report.md").write_text(qa.markdown_report(rep, ingest_id), encoding="utf-8")
    (out_dir / "qa_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"报告已写入 {out_dir}/qa_report.md")
    for r in rep["key_metrics"]:
        print(f"  {r['metric']:<26} n={r['rows']:<5} numeric={r['numeric']:<5} "
              f"{r['min']}–{r['max']} {r['unit']}")
    return 0


def cmd_embed(args) -> int:
    from fastembed import TextEmbedding

    model_name = args.model or settings.embed_model
    if not model_name:
        print("未配置 STEELDIG_EMBED_MODEL，跳过")
        return 1
    prefix = "passage: " if "e5" in model_name.lower() else ""
    print(f"加载嵌入模型 {model_name}（前缀 {prefix!r}）…")
    model = TextEmbedding(model_name=model_name, cache_dir=str(settings.model_cache))
    dim = len(next(iter(model.embed(["dimension probe"]))))
    print(f"向量维度 {dim}")

    with connect() as conn:
        rows = conn.execute("""
            SELECT doc_id, title, body FROM search.document
            WHERE embed IS NULL ORDER BY doc_id
        """).fetchall()
        print(f"待向量化文档 {len(rows)}")
        batch = 64
        done = 0
        for i in range(0, len(rows), batch):
            chunk = rows[i:i + batch]
            texts = [f"{prefix}{r[1] + ' ' if r[1] else ''}{r[2][:3000]}" for r in chunk]
            vecs = list(model.embed(texts))
            with conn.cursor() as cur:
                cur.executemany(
                    "UPDATE search.document SET embed = %s::vector, embed_model = %s WHERE doc_id = %s",
                    [("[" + ",".join(f"{x:.7f}" for x in v) + "]", model_name, r[0])
                     for v, r in zip(vecs, chunk)])
            conn.commit()
            done += len(chunk)
            print(f"  {done}/{len(rows)}", end="\r")
    print(f"\n完成 {done} 条")
    return 0


def cmd_verify(args) -> int:
    lake = Lake(settings.lake_root)
    print("校验资产湖（重算 sha256）…")
    res = lake.verify()
    print(f"  对象 {res['objects']:,} 个，{res['bytes'] / 1e6:.1f} MB，损坏 {len(res['corrupted'])}")
    ok = not res["corrupted"]
    with connect() as conn:
        mismatch = conn.execute("""
            SELECT count(*) FROM lake.object o
            WHERE NOT EXISTS (SELECT 1 FROM lake.object_ref r WHERE r.object_id = o.object_id)
        """).fetchone()[0]
        print(f"  无引用的孤儿对象：{mismatch}")
        bad = conn.execute("""
            SELECT count(*) FROM core.sample_trace t
            WHERE EXISTS (SELECT 1 FROM unnest(t.block_ids) b
                          LEFT JOIN core.evidence_block e
                            ON e.paper_id = t.paper_id AND e.block_id = b
                          WHERE e.block_id IS NULL)
        """).fetchone()[0]
        print(f"  溯源断链行：{bad}")
        ok = ok and bad == 0
    return 0 if ok else 2


def cmd_curate(args) -> int:
    with connect() as conn:
        if args.action == "apply":
            res = curation.apply_changes(conn)
            conn.commit()
            print(f"已重放 {res['applied']} 条校订，失败 {res['failed']} 条")
        elif args.action == "list":
            rows = conn.execute("""
                SELECT change_id, op, target_table, target_key->>'paper_id' AS paper_id,
                       field, new_value, status, author, created_at
                FROM curate.change ORDER BY change_id DESC LIMIT %s
            """, (args.limit,)).fetchall()
            for r in rows:
                print(f"#{r[0]:<4} {r[1]:<7} {r[2]:<26} {r[3] or '':<28} "
                      f"{r[4] or '':<18} {str(r[5])[:24]:<26} {r[6]:<9} {r[7]}")
            st = curation.stats(conn)
            print(f"\n共 {st['total']} 条：生效 {st['applied']} / 已撤销 {st['reverted']} / 失败 {st['failed']}")
        elif args.action == "revert":
            ok = curation.revert(conn, args.change_id)
            conn.commit()
            print("已撤销" if ok else "撤销失败（不存在或已撤销）")
            if ok:
                print("提示：delete 类校订的撤销需要重新 ingest 该篇")
    return 0


def cmd_stats(args) -> int:
    with connect() as conn:
        row = conn.execute("""
            SELECT (SELECT count(*) FROM core.paper),
                   (SELECT count(*) FROM core.sample),
                   (SELECT count(*) FROM core.alloy),
                   (SELECT count(*) FROM core.property_value),
                   (SELECT count(*) FROM core.property_value WHERE value_canonical IS NOT NULL),
                   (SELECT count(*) FROM core.figure),
                   (SELECT count(*) FROM core.equation),
                   (SELECT count(*) FROM core.evidence_block),
                   (SELECT count(*) FROM search.document),
                   (SELECT count(*) FROM search.document WHERE embed IS NOT NULL),
                   (SELECT count(*) FROM lake.object)
        """).fetchone()
        labels = ["论文", "样品", "合金", "属性量", "可数值化属性", "图/表", "公式",
                  "证据块", "检索文档", "已向量化", "湖对象"]
        for label, val in zip(labels, row):
            print(f"  {label:<12} {val:>9,}")
        print("\n  属性量 top10：")
        for m, n, u in conn.execute("""
            SELECT metric, count(*), count(*) FILTER (WHERE value_canonical IS NOT NULL)
            FROM core.property_value GROUP BY 1 ORDER BY 2 DESC LIMIT 10""").fetchall():
            print(f"    {m[:34]:<34} {n:>6}  (numeric {u})")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="steeldig-db", description="SteelDig 材料知识库 ETL")
    p.add_argument("--version", action="version", version=f"steeldig-db {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("migrate", help="执行数据库迁移").set_defaults(func=cmd_migrate)

    rst = sub.add_parser("reset", help="[开发] 清空并重建全部 schema")
    rst.add_argument("--yes", action="store_true")
    rst.set_defaults(func=cmd_reset)

    pi = sub.add_parser("ingest", help="入库")
    pi.add_argument("--all", action="store_true", help="处理全部论文（默认）")
    pi.add_argument("--papers", nargs="*", help="指定 paper_id")
    pi.add_argument("--limit", type=int, help="只处理前 N 篇")
    pi.add_argument("--label", help="本次运行标签")
    pi.add_argument("--debug", action="store_true")
    pi.set_defaults(func=cmd_ingest)

    sub.add_parser("qa", help="质量门禁").set_defaults(func=cmd_qa)

    pr = sub.add_parser("report", help="覆盖率报告")
    pr.add_argument("--out", type=Path)
    pr.set_defaults(func=cmd_report)

    pe = sub.add_parser("embed", help="计算语义向量")
    pe.add_argument("--model", help="fastembed 模型名")
    pe.set_defaults(func=cmd_embed)

    pc = sub.add_parser("curate", help="人工校订（增删改）")
    pc.add_argument("action", choices=["apply", "list", "revert"])
    pc.add_argument("change_id", nargs="?", type=int)
    pc.add_argument("--limit", type=int, default=20)
    pc.set_defaults(func=cmd_curate)

    sub.add_parser("verify", help="校验资产湖与溯源链").set_defaults(func=cmd_verify)
    sub.add_parser("stats", help="控制台概览").set_defaults(func=cmd_stats)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
