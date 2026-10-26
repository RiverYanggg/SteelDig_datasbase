"""逐篇 ETL 主流程。

严格遵循"湖 → 仓"单向流：

    process(paper)
      ├─ 读 7 类产物 JSON
      ├─ 落湖（内容寻址，去重）
      ├─ 结构化为 core.* 行（列 = 可过滤维度，payload = 原文保真）
      ├─ block_id 对齐（合成 id → 真实证据块，全程留痕）
      └─ 构建检索文档
    load(paper)
      └─ 单事务写入；先删后插，因此可无限次重跑（幂等）

任何一篇失败都不影响其他篇，失败原因写入 ops.ingest_log。
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from psycopg import Connection

from . import searchidx
from .blockresolve import BlockResolver
from .composition import parse_composition
from .config import Settings
from .db import copy_rows
from .family import classify
from .lake import Lake
from .quantity import clean, normalize
from .resolve import TechniqueResolver, PhaseResolver
from .text import flatten_strings, lang_of, segment

# ---------------------------------------------------------------------------
# 列定义（COPY 顺序即此顺序）
# ---------------------------------------------------------------------------
COLS = {
    "paper": ("paper_id", "doi", "title", "abstract", "journal", "year", "research_type",
              "domain", "keywords", "authors", "paper_scope", "page_count", "block_count",
              "figure_count", "section_headings", "run_id", "source_dir", "qa_flags"),
    "evidence_block": ("paper_id", "block_id", "ordinal", "kind", "page_idx", "section",
                       "text", "char_len", "in_reading_view", "content_sha256"),
    "alloy": ("paper_id", "alloy_id", "name", "base_element", "elements", "formula",
              "formula_alpha", "chemsys", "n_elements", "aliases", "description", "notes",
              "family_key", "source_block_ids", "is_stub", "payload"),
    "alloy_element": ("paper_id", "alloy_id", "element", "weight_pct", "atomic_pct",
                      "raw_wt", "is_balance"),
    "process": ("paper_id", "process_id", "name", "state_label", "aliases", "description",
                "notes", "source_block_ids", "is_stub", "payload"),
    "process_edge": ("paper_id", "child_process_id", "parent_process_id"),
    "sample": ("paper_id", "sample_id", "alloy_id", "process_id", "label", "aliases",
               "source_block_ids", "payload"),
    "sample_data": ("paper_id", "sample_id", "run_id", "payload", "payload_bytes",
                    "sha256", "is_latest"),
    "sample_trace": ("paper_id", "sample_id", "run_id", "path", "reason", "block_ids",
                     "status", "depth"),
    "sample_wiki": ("paper_id", "sample_id", "run_id", "summary", "mechanisms",
                    "n_mechanisms", "conclusions", "payload", "content", "content_seg"),
    "processing_step": ("paper_id", "sample_id", "seq", "step_id", "step_type", "method",
                        "temperature_raw", "temperature_k", "duration_raw", "duration_s",
                        "atmosphere", "cooling_medium", "heating_rate", "reduction_ratio",
                        "notes", "source_block_ids"),
    "phase": ("paper_id", "sample_id", "microstructure_id", "idx", "phase_name", "phase_key",
              "crystal_structure", "volume_fraction_raw", "volume_fraction_pct", "morphology",
              "grain_size_raw", "grain_size_um", "texture", "source_block_ids", "payload"),
    "property_value": ("paper_id", "sample_id", "run_id", "path", "section", "group_path",
                       "metric", "idx", "value_raw", "value_kind", "value_num", "value_low",
                       "value_high", "value_unit", "unit_canonical", "value_canonical",
                       "value_low_canonical", "value_high_canonical", "qualifier",
                       "uncertainty_raw", "direction", "block_status", "conditions",
                       "source_block_ids"),
    "performance": ("paper_id", "sample_id", "perf_id", "benchmark_sample", "benchmark_alloy",
                    "comparison_metric", "improvement", "service_conditions", "lifetime", "payload"),
    "characterization": ("paper_id", "sample_id", "idx", "char_id", "technique", "technique_key",
                         "instrument", "conditions", "purpose", "key_findings", "payload"),
    "unmapped_finding": ("paper_id", "sample_id", "idx", "text", "source_block_ids"),
    "figure": ("paper_id", "figure_id", "kind", "label", "family", "image_type", "description",
               "confidence", "n_subfigures", "n_observations", "n_measured", "measured_quantities",
               "sample_hints", "image_paths", "block_ids", "page_idx", "ordinal", "payload"),
    "figure_panel": ("paper_id", "figure_id", "idx", "panel", "description"),
    "figure_observation": ("paper_id", "figure_id", "idx", "observation", "source", "confidence",
                           "evidence_raw", "block_ids", "block_status"),
    "equation": ("paper_id", "equation_id", "block_id", "equation_number", "is_image", "latex",
                 "latex_hint", "purpose", "applicability", "symbols", "n_symbols", "payload"),
}

KNOWN_SECTIONS = {
    "mechanical", "physical", "chemical", "radiation_properties", "thermodynamic",
    "fatigue_properties", "creep_properties", "hardness", "fracture_toughness",
    "other_properties", "tensile_properties", "elastic_constants", "magnetic_properties",
    "thermal_properties", "electrical_properties",
}

_MISSING = object()


def _first_dict(v: Any) -> dict:
    if isinstance(v, dict):
        return v
    if isinstance(v, list):
        for x in v:
            if isinstance(x, dict):
                return x
    return {}


def _as_list(v: Any) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _s(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, (dict, list)):
        return None
    return str(v).strip() or None


def _num(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _block_ids(src: Any) -> list[str]:
    """discover 里的 source.block_id 可能是 str / list / 嵌套。"""
    if not isinstance(src, dict):
        return []
    raw = src.get("block_id")
    return [b for b in _as_list(raw) if isinstance(b, str)]


def _reason(src: Any) -> str | None:
    return _s(src.get("reason")) if isinstance(src, dict) else None


@dataclass
class PaperResult:
    paper_id: str
    ingest_id: int = 0
    rows: dict[str, list[tuple]] = field(default_factory=dict)
    objects: list[tuple] = field(default_factory=list)        # (object_id, bytes, media, kind, uri)
    refs: list[tuple] = field(default_factory=list)           # (object_id, paper_id, rel_path, role)
    resolutions: list[tuple] = field(default_factory=list)    # ops.block_id_resolution
    qa_flags: list[str] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)          # 交给 qa.py 落库
    stats: dict[str, int] = field(default_factory=dict)

    def add(self, table: str, row: tuple) -> None:
        self.rows.setdefault(table, []).append(row)


class PaperIngest:
    def __init__(self, settings: Settings, lake: Lake, families: list[dict],
                 run_id: str, ingest_id: int,
                 phase_resolver: PhaseResolver | None = None,
                 technique_resolver: TechniqueResolver | None = None):
        self.s = settings
        self.lake = lake
        self.families = families
        self.phases = phase_resolver
        self.techniques = technique_resolver
        self.run_id = run_id
        self.ingest_id = ingest_id

    # ==================================================================
    # 入口
    # ==================================================================
    def process(self, paper_id: str) -> PaperResult:
        root = self.s.extraction_root / paper_id
        r = PaperResult(paper_id, ingest_id=self.ingest_id)
        self._root = root
        self._pid = paper_id
        self._res = r

        self._load(root)
        self._store_lake(root, r)

        self._emit_evidence(r)
        self._emit_paper(r)
        self._emit_alloys(r)
        self._emit_processes(r)
        self._emit_samples(r)
        self._emit_figures(r)
        self._emit_equations(r)
        self._emit_search_docs(r)

        r.stats = {k: len(v) for k, v in r.rows.items()}
        r.stats["objects"] = len(r.objects)
        return r

    # ==================================================================
    # 读取
    # ==================================================================
    def _read(self, rel: str) -> Any:
        p = self._root / rel
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def _load(self, root: Path) -> None:
        self.paper_context = self._read("preprocess/paper_context.json") or {}
        self.blocks_doc = self._read("preprocess/evidence_blocks.json") or {}
        self.image_groups = self._read("preprocess/image_groups.json") or {}
        self.manifest = self._read("preprocess/manifest.json") or {}
        self.eq_index = self._read("preprocess/equation_index.json") or {}
        self.discover = self._read("output/discover/result.json") or {}
        self.timing = self._read("timing.json") or {}

        self.samples: dict[str, dict] = {}
        for p in sorted((root / "output" / "sample").glob("*.data.json")):
            sid = p.name[: -len(".data.json")]
            data = self._read(f"output/sample/{p.name}")
            if data is not None:
                self.samples[sid] = data
        self.sample_rich = {}
        for p in sorted((root / "output" / "sample").glob("*.json")):
            if p.name.endswith(".data.json"):
                continue
            sid = p.stem
            self.sample_rich[sid] = self._read(f"output/sample/{p.name}")

        self.traces: dict[str, list] = {}
        for p in sorted((root / "output" / "sample_trace").glob("*.trace.json")):
            sid = p.name[: -len(".trace.json")]
            self.traces[sid] = self._read(f"output/sample_trace/{p.name}") or []

        self.wikis: dict[str, dict] = {}
        for p in sorted((root / "output" / "wiki").glob("*.wiki.json")):
            sid = p.name[: -len(".wiki.json")]
            self.wikis[sid] = self._read(f"output/wiki/{p.name}") or {}

        self.figures: dict[str, dict] = {}
        for p in sorted((root / "output" / "figure").glob("*.json")):
            self.figures[p.stem] = self._read(f"output/figure/{p.name}") or {}

        self.equations: dict[str, dict] = {}
        for p in sorted((root / "output" / "equation").glob("*.json")):
            self.equations[p.stem] = self._read(f"output/equation/{p.name}") or {}

        # --- block resolver
        recs = self.blocks_doc.get("records") or []
        self.blocks = [b for b in recs if isinstance(b, dict) and b.get("block_id")]
        self.real_ids = {b["block_id"] for b in self.blocks}
        self.resolver = BlockResolver(
            self.real_ids, self.image_groups.get("groups") or [],
            {b["block_id"]: (b.get("section") or "") for b in self.blocks})

    # ==================================================================
    # 落湖
    # ==================================================================
    LAKE_GLOBS = (
        ("preprocess/*.json", "preprocess"),
        ("preprocess/*.md", "preprocess"),
        ("output/discover/*.json", "discover"),
        ("output/sample/*.json", "sample"),
        ("output/sample_trace/*.json", "trace"),
        ("output/wiki/*.json", "wiki"),
        ("output/figure/*.json", "figure"),
        ("output/equation/*.json", "equation"),
        ("timing.json", "timing"),
    )

    def _store_lake(self, root: Path, r: PaperResult) -> None:
        seen: set[str] = set()
        manifest: list[dict] = []

        def put(obj, rel: str, role: str):
            st = self.lake.put_json(obj)
            if st.object_id not in seen:
                seen.add(st.object_id)
                r.objects.append((st.object_id, st.bytes, st.media_type, st.kind, st.uri))
            r.refs.append((st.object_id, self._pid, rel, role))
            manifest.append({"rel_path": rel, "object_id": st.object_id,
                             "bytes": st.bytes, "role": role, "media_type": st.media_type})

        for pattern, role in self.LAKE_GLOBS:
            for p in sorted(root.glob(pattern)):
                rel = str(p.relative_to(root))
                if p.suffix == ".json":
                    obj = self._read(rel)
                    if obj is None:
                        continue
                    put(obj, rel, role)
                else:
                    data = p.read_bytes()
                    st = self.lake.put_bytes(data, "text/markdown")
                    if st.object_id not in seen:
                        seen.add(st.object_id)
                        r.objects.append((st.object_id, st.bytes, st.media_type, st.kind, st.uri))
                    r.refs.append((st.object_id, self._pid, rel, role))
                    manifest.append({"rel_path": rel, "object_id": st.object_id,
                                     "bytes": st.bytes, "role": role, "media_type": st.media_type})

        # --- 图片（MinerU 解析产物里的 images/），内容寻址后跨论文自动去重
        mineru_dir = self.s.mineru_root / self._pid
        img_seen: set[str] = set()
        for g in self.image_groups.get("groups") or []:
            for rel in g.get("image_paths") or []:
                if rel in img_seen:
                    continue
                img_seen.add(rel)
                src = mineru_dir / rel
                if not src.exists():
                    continue
                st = self.lake.put_file(src)
                if st.object_id not in seen:
                    seen.add(st.object_id)
                    r.objects.append((st.object_id, st.bytes, st.media_type, st.kind, st.uri))
                r.refs.append((st.object_id, self._pid, f"{self._pid}/{rel}", "image"))
                manifest.append({"rel_path": f"{self._pid}/{rel}", "object_id": st.object_id,
                                 "bytes": st.bytes, "role": "image",
                                 "media_type": st.media_type})

        r.add("__lake_manifest__", (
            self._pid, self.run_id, len(manifest),
            sum(m["bytes"] for m in manifest), json.dumps(manifest, ensure_ascii=False),
        ))

    # ==================================================================
    # 证据块
    # ==================================================================
    def _emit_evidence(self, r: PaperResult) -> None:
        for i, b in enumerate(self.blocks, start=1):
            text = b.get("text") or ""
            r.add("evidence_block", (
                self._pid, b["block_id"], i, b.get("kind") or "text",
                b.get("page_idx"), _s(b.get("section")), text, len(text),
                bool(b.get("in_reading_view", True)),
                hashlib.sha256(text.encode("utf-8")).hexdigest(),
            ))

    # ==================================================================
    # 论文
    # ==================================================================
    def _emit_paper(self, r: PaperResult) -> None:
        pc = self.paper_context
        p = (self.discover.get("paper") or {}) if isinstance(self.discover, dict) else {}
        title = _s(p.get("title")) or _s(pc.get("title"))
        if not title:
            title = self._title_from_paper()
            r.qa_flags.append("TITLE_FALLBACK")
            r.issues.append({"rule_code": "VALUE_UNPARSED", "severity": "info",
                             "subject": "$.paper.title",
                             "message": "discover 未给出标题，回退到证据块首行",
                             "detail": {"title": title}})

        year = p.get("publication_year")
        if isinstance(year, str):
            m = re.search(r"(19|20)\d{2}", year)
            year = int(m.group(0)) if m else None

        r.add("paper", (
            self._pid, _s(p.get("doi")), title, _s(p.get("abstract")) or _s(pc.get("abstract")),
            _s(p.get("journal")), year, _s(p.get("research_type")),
            _s(self.discover.get("domain")) or "materials",
            _as_list(p.get("keywords")), _as_list(p.get("authors")),
            _s(p.get("paper_scope")),
            pc.get("page_count"), pc.get("block_count"), pc.get("figure_count"),
            json.dumps(pc.get("section_headings"), ensure_ascii=False),
            self.run_id, str(self._root),
            sorted(set(r.qa_flags)) if r.qa_flags else [],
        ))

    def _title_from_paper(self) -> str:
        """无 discover 时用第一个非参考文献的正文块兜底。"""
        for b in self.blocks:
            if b.get("kind") in ("heading", "text") and (b.get("text") or "").strip():
                return b["text"][:300]
        return self._pid

    # ==================================================================
    # 合金
    # ==================================================================
    def _emit_alloys(self, r: PaperResult) -> None:
        keywords_blob = " ".join(
            [str(k) for k in _as_list((self.discover.get("paper") or {}).get("keywords"))]
            + [(self.discover.get("paper") or {}).get("title") or "", self.paper_context.get("title") or ""]
        ).lower()

        declared: dict[str, dict] = {}
        for a in _as_list(self.discover.get("alloys")):
            if not isinstance(a, dict) or not a.get("alloy_id"):
                continue
            declared[a["alloy_id"]] = a

        # sample 引用但未声明的合金 → 补 stub，保证外键完整
        for s in _as_list(self.discover.get("samples")):
            aid = (s or {}).get("alloy_id")
            if aid and aid not in declared:
                declared[aid] = {"alloy_id": aid, "_stub": True}

        for aid, a in declared.items():
            comp = parse_composition(a.get("nominal_composition"), a.get("base_element"))
            family = classify(self.families, {
                "base_element": a.get("base_element") or comp.balance,
                "elements": set(comp.elements),
                "weight_pct": comp.weight_pct,
                "keywords_blob": keywords_blob,
                "title": (self.discover.get("paper") or {}).get("title") or "",
                "research_type": (self.discover.get("paper") or {}).get("research_type"),
            })
            if a.get("_stub"):
                r.issues.append({"rule_code": "SAMPLE_REF_MISSING", "severity": "warn",
                                 "subject": aid,
                                 "message": "sample 引用了未在 alloys[] 中声明的合金，已补 stub",
                                 "detail": {}})
                r.qa_flags.append("ALLOY_STUB")
            r.add("alloy", (
                self._pid, aid, _s(a.get("alloy_name")), _s(a.get("base_element")),
                comp.elements, comp.formula, comp.formula_alpha, comp.chemsys,
                comp.n_elements, _as_list(a.get("aliases")), _s(a.get("description")),
                _s(a.get("alloys_notes")), family, _block_ids(a.get("source")),
                bool(a.get("_stub")), json.dumps(a, ensure_ascii=False),
            ))
            for row in comp.rows:
                r.add("alloy_element", (self._pid, aid, row["element"], row["weight_pct"],
                                        row["atomic_pct"], row["raw_wt"], row["is_balance"]))

    # ==================================================================
    # 工艺
    # ==================================================================
    def _emit_processes(self, r: PaperResult) -> None:
        declared: dict[str, dict] = {}
        for p in _as_list(self.discover.get("processes")):
            if isinstance(p, dict) and p.get("process_id"):
                declared[p["process_id"]] = p
        for s in _as_list(self.discover.get("samples")):
            pid = (s or {}).get("process_id")
            if pid and pid not in declared:
                declared[pid] = {"process_id": pid, "_stub": True}

        for pid, p in declared.items():
            if p.get("_stub"):
                r.issues.append({"rule_code": "SAMPLE_REF_MISSING", "severity": "warn",
                                 "subject": pid,
                                 "message": "sample 引用了未声明的工艺，已补 stub",
                                 "detail": {}})
                r.qa_flags.append("PROCESS_STUB")
            r.add("process", (
                self._pid, pid, _s(p.get("process_name")), _s(p.get("state_label")),
                _as_list(p.get("aliases")), _s(p.get("description")),
                _s(p.get("processes_notes")), _block_ids(p.get("source")),
                bool(p.get("_stub")), json.dumps(p, ensure_ascii=False),
            ))
            for parent in _as_list(p.get("parent_process_ids")):
                if isinstance(parent, str) and parent:
                    r.add("process_edge", (self._pid, pid, parent))

    # ==================================================================
    # 样品
    # ==================================================================
    def _emit_samples(self, r: PaperResult) -> None:
        declared = {s.get("sample_id"): s for s in _as_list(self.discover.get("samples"))
                    if isinstance(s, dict) and s.get("sample_id")}

        all_ids = list(dict.fromkeys(list(declared) + list(self.samples) + list(self.sample_rich)))
        for sid in all_ids:
            d = declared.get(sid) or {}
            payload = self.samples.get(sid)
            alloy_id = d.get("alloy_id")
            process_id = d.get("process_id")
            if payload:
                head = _first_dict(payload.get("samples"))
                alloy_id = alloy_id or head.get("alloy_id")
                process_id = process_id or head.get("process_id")
            # sample_id 的构成规则：alloy_id + "__" + process_id
            if (not alloy_id or not process_id) and "__" in sid:
                a_part, p_part = sid.split("__", 1)
                # sample_id 约定：sample_<alloy_stem>__<process_stem>
                stem = re.sub(r"^sample_", "", a_part)
                alloy_id = alloy_id or f"alloy_{stem}"
                process_id = process_id or f"proc_{p_part}"

            r.add("sample", (
                self._pid, sid, alloy_id, process_id,
                _s(d.get("sample_label")), _as_list(d.get("aliases")),
                _block_ids(d.get("source")), json.dumps(d, ensure_ascii=False),
            ))

            if payload is None:
                r.issues.append({"rule_code": "EMPTY_SAMPLE_SECTION", "severity": "info",
                                 "subject": sid, "message": "缺少 <sample>.data.json",
                                 "detail": {}})
                continue

            blob = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            r.add("sample_data", (self._pid, sid, self.run_id, json.dumps(payload, ensure_ascii=False),
                                  len(blob), hashlib.sha256(blob).hexdigest(), True))

            self._emit_trace(r, sid)
            self._emit_wiki(r, sid, payload)
            self._emit_properties(r, sid, payload)
            self._emit_steps(r, sid, payload)
            self._emit_phases(r, sid, payload)
            self._emit_performance(r, sid, payload)
            self._emit_characterization(r, sid, payload)
            self._emit_unmapped(r, sid, payload)

    # ------------------------------------------------------------------
    def _emit_trace(self, r: PaperResult, sid: str) -> None:
        # 同一 path 可能被抽取器重复输出；保留"溯源更强"的那条（有 block_id 优先）
        best: dict[str, tuple] = {}
        for rec in self.traces.get(sid) or []:
            if not isinstance(rec, dict) or not rec.get("path"):
                continue
            raw_ids = list(dict.fromkeys(
                b for b in _as_list(rec.get("block_id")) if isinstance(b, str)))
            # 上游偶尔把 figure_00X 写进 block_id；按图组题注/引用还原成真实块
            ids: list[str] = []
            for rid in raw_ids:
                if rid in self.real_ids:
                    ids.append(rid)
                    continue
                res = self.resolver.resolve(rid)
                if res.block_ids:
                    r.resolutions.append((self.ingest_id, self._pid, "core.sample_trace",
                                          f"{sid}{rec['path']}", rid, res.method,
                                          res.confidence, res.block_ids, res.note))
                    ids.extend(res.block_ids)
                else:
                    ids.append(rid)
            dangling = [b for b in ids if b not in self.real_ids]
            if dangling:
                # 区分两种坏引用：
                #   bNNNN 形态但表里没有 → 真·断链（error，说明链路有 bug）
                #   figure_00X 之类的非块引用 → 上游把图表 id 写进了 block_id（warn，数据缺口）
                hard = [b for b in dangling if re.fullmatch(r"b\d{4}", b)]
                soft = [b for b in dangling if b not in hard]
                if hard:
                    r.issues.append({"rule_code": "BLOCK_ID_DANGLING", "severity": "error",
                                     "subject": f"{sid}{rec['path']}",
                                     "message": "trace 引用了不存在的证据块",
                                     "detail": {"dangling": hard}})
                    r.qa_flags.append("TRACE_DANGLING")
                if soft:
                    r.issues.append({"rule_code": "BLOCK_ID_UNRESOLVED", "severity": "warn",
                                     "subject": f"{sid}{rec['path']}",
                                     "message": "trace 引用了非块 id，且无法还原到证据块",
                                     "detail": {"raw": soft}})
            row = (
                self._pid, sid, self.run_id, rec["path"], _s(rec.get("reason")),
                [b for b in ids if b in self.real_ids],
                "ok" if rec.get("status") == "ok" else "insufficient",
                rec["path"].count(".") + rec["path"].count("["),
            )
            prev = best.get(rec["path"])
            if prev is None or (not prev[5] and row[5]) or (prev[6] != "ok" and row[6] == "ok"):
                best[rec["path"]] = row
        for row in best.values():
            r.add("sample_trace", row)

    def _emit_wiki(self, r: PaperResult, sid: str, payload: dict) -> None:
        w = self.wikis.get(sid)
        if not w:
            r.issues.append({"rule_code": "EMPTY_SAMPLE_SECTION", "severity": "info",
                             "subject": sid, "message": "缺少 wiki 词条", "detail": {}})
            return

        mechanisms = [m for m in _as_list(w.get("mechanisms")) if isinstance(m, str) and m.strip()]
        # 已知脏数据：LLM 把下一个键名（如 "conclusions"）混进了 mechanisms
        leaked = [m for m in mechanisms if len(m) < 40 and re.fullmatch(r"[a-z_ ]+", m)]
        if leaked:
            mechanisms = [m for m in mechanisms if m not in leaked]
            r.issues.append({"rule_code": "WIKI_SECTION_LEAK", "severity": "warn",
                             "subject": sid, "message": "mechanisms 中混入章节名，已剔除",
                             "detail": {"leaked": leaked}})
            r.qa_flags.append("WIKI_SECTION_LEAK")

        pairs = flatten_strings({k: v for k, v in w.items() if k != "identity"})
        content = "\n".join(f"{v}" for _, v in pairs)
        r.add("sample_wiki", (
            self._pid, sid, self.run_id, _s(w.get("summary")), mechanisms, len(mechanisms),
            _s(w.get("conclusions")), json.dumps(w, ensure_ascii=False),
            content, segment(content),
        ))

    # ------------------------------------------------------------------
    def _emit_properties(self, r: PaperResult, sid: str, payload: dict) -> None:
        trace_recs = {rec.get("path"): rec for rec in (self.traces.get(sid) or [])
                      if isinstance(rec, dict) and rec.get("path")}
        props = _as_list(payload.get("properties"))

        def walk(node: Any, path: str, section: str | None, parent_key: str | None,
                 conditions: dict, depth: int = 0) -> None:
            if depth > 8 or not isinstance(node, dict):
                return
            if "value" in node and not isinstance(node["value"], (dict, list)):
                metric = parent_key or path.rsplit(".", 1)[-1]
                q = normalize(node.get("value"), node.get("unit"), metric, section)
                if q["value_kind"] == "missing":
                    return
                trec = trace_recs.get(path) or {}
                status = "ok" if str(trec.get("status")) == "ok" else "insufficient"
                tblocks = [b for b in _as_list(trec.get("block_id"))
                           if isinstance(b, str) and b in self.real_ids]
                m_idx = re.search(r"\[(\d+)\]$", path)
                group = re.sub(r"\[\d+\]$", "", re.sub(r"^\$\.properties\[\d+\]\.", "", path))
                r.add("property_value", (
                    self._pid, sid, self.run_id, path, section or "other",
                    group or None,
                    metric, int(m_idx.group(1)) if m_idx else 0,
                    q["value_raw"], q["value_kind"], q["value_num"], q["value_low"],
                    q["value_high"], q["value_unit"], q["unit_canonical"],
                    q["value_canonical"], q["value_low_canonical"], q["value_high_canonical"],
                    q.get("qualifier"), _s(node.get("uncertainty")), _s(node.get("direction")),
                    status, json.dumps(conditions, ensure_ascii=False) if conditions else "{}",
                    tblocks,
                ))
                return
            for k, v in node.items():
                if k in ("property_set_id", "measurement_conditions"):
                    continue
                child = f"{path}.{k}"
                sec = section or (k if k in KNOWN_SECTIONS else None)
                if isinstance(v, dict):
                    walk(v, child, sec, k, conditions, depth + 1)
                elif isinstance(v, list):
                    for i, item in enumerate(v):
                        if isinstance(item, dict):
                            walk(item, f"{child}[{i}]", sec, k, conditions, depth + 1)

        for i, ps in enumerate(props):
            if not isinstance(ps, dict):
                continue
            conditions = ps.get("measurement_conditions") or {}
            for k, v in ps.items():
                if k in ("property_set_id", "measurement_conditions"):
                    continue
                sec = k if k in KNOWN_SECTIONS else None
                if isinstance(v, dict):
                    walk(v, f"$.properties[{i}].{k}", sec, k, conditions)
                elif isinstance(v, list):
                    for j, item in enumerate(v):
                        if isinstance(item, dict):
                            walk(item, f"$.properties[{i}].{k}[{j}]", sec, k, conditions)

    # ------------------------------------------------------------------
    def _emit_steps(self, r: PaperResult, sid: str, payload: dict) -> None:
        used: set[int] = set()
        for i, st in enumerate(_as_list(payload.get("processing_steps"))):
            if not isinstance(st, dict):
                continue
            # sequence 可能重复/缺失：保证 (paper,sample,seq) 唯一
            seq = int(_num(st.get("sequence")) or (i + 1))
            while seq in used:
                seq += 1
            used.add(seq)
            temp_raw = st.get("temperature")
            temp_unit = st.get("temperature_unit")
            tq = normalize(temp_raw, temp_unit, "temperature") if temp_raw else None
            dur = normalize(st.get("duration"), None, "duration") if st.get("duration") else None
            r.add("processing_step", (
                self._pid, sid, seq,
                _s(st.get("processing_step_id")), _s(st.get("type")), _s(st.get("method")),
                _s(temp_raw), tq["value_canonical"] if tq else None,
                _s(st.get("duration")), dur["value_canonical"] if dur else None,
                _s(st.get("atmosphere")), _s(st.get("cooling_medium")),
                _s(st.get("heating_or_cooling_rate")), _s(st.get("reduction_ratio")),
                _s(st.get("processing_steps_notes")), [],
            ))

    # ------------------------------------------------------------------
    def _emit_phases(self, r: PaperResult, sid: str, payload: dict) -> None:
        used_mid: set[str] = set()
        for si, st in enumerate(_as_list(payload.get("structures"))):
            if not isinstance(st, dict):
                continue
            micro = _as_list(st.get("microstructure_list"))
            for mi, m in enumerate(micro):
                if not isinstance(m, dict):
                    continue
                mid = _s(m.get("microstructure_id")) or f"microstructure_{mi + 1}"
                while mid in used_mid:
                    mid = f"{mid}_s{si + 1}"
                used_mid.add(mid)
                for pi, ph in enumerate(_as_list(m.get("phases_present"))):
                    if not isinstance(ph, dict):
                        continue
                    name = _s(ph.get("phase_name")) or "unknown"
                    pkey = None
                    if self.phases is not None:
                        m = self.phases.match(name)
                        pkey = m.key
                        if pkey is None:
                            r.qa_flags.append("PHASE_UNMAPPED")
                    vf = normalize(ph.get("volume_fraction"), None, "volume_fraction") \
                        if ph.get("volume_fraction") is not None else None
                    gs = normalize(ph.get("grain_size"), None, "grain_size") \
                        if ph.get("grain_size") is not None else None
                    r.add("phase", (
                        self._pid, sid, mid, pi, name, pkey,
                        _s(ph.get("crystal_structure")), _s(ph.get("volume_fraction")),
                        vf["value_canonical"] if vf else None,
                        _s(ph.get("morphology")), _s(ph.get("grain_size")),
                        gs["value_canonical"] if gs else None,
                        _s(ph.get("texture")), [], json.dumps(ph, ensure_ascii=False),
                    ))
            # 兜底：structure 里直接带 phases_present（未包在 microstructure_list 内）
            if not micro and st.get("phases_present"):
                for pi, ph in enumerate(_as_list(st.get("phases_present"))):
                    if not isinstance(ph, dict):
                        continue
                    vf = normalize(ph.get("volume_fraction"), None, "volume_fraction") \
                        if ph.get("volume_fraction") is not None else None
                    gs = normalize(ph.get("grain_size"), None, "grain_size") \
                        if ph.get("grain_size") is not None else None
                    pname2 = _s(ph.get("phase_name")) or "unknown"
                    pkey2 = self.phases.match(pname2).key if self.phases is not None else None
                    r.add("phase", (
                        self._pid, sid, f"structure_{si + 1}", pi,
                        pname2, pkey2,
                        _s(ph.get("crystal_structure")), _s(ph.get("volume_fraction")),
                        vf["value_canonical"] if vf else None, _s(ph.get("morphology")),
                        _s(ph.get("grain_size")), gs["value_canonical"] if gs else None,
                        _s(ph.get("texture")), [], json.dumps(ph, ensure_ascii=False),
                    ))

    # ------------------------------------------------------------------
    def _emit_performance(self, r: PaperResult, sid: str, payload: dict) -> None:
        for p in _as_list(payload.get("performance")):
            if not isinstance(p, dict):
                continue
            cp = _first_dict(p.get("comparative_performance"))
            r.add("performance", (
                self._pid, sid, _s(p.get("performance_id")),
                _s(cp.get("benchmark_sample_id")), _s(cp.get("benchmark_alloy_id")),
                _s(cp.get("comparison_metric")), _s(cp.get("improvement_percentage")),
                _s(p.get("service_conditions")), _s(p.get("lifetime_prediction")),
                json.dumps(p, ensure_ascii=False),
            ))

    def _emit_characterization(self, r: PaperResult, sid: str, payload: dict) -> None:
        for i, c in enumerate(_as_list(payload.get("characterization_methods"))):
            if not isinstance(c, dict):
                continue
            tech = _s(c.get("technique"))
            tkey = self.techniques.match(tech).key if (self.techniques and tech) else None
            r.add("characterization", (
                self._pid, sid, i, _s(c.get("characterization_id")), tech,
                tkey, _s(c.get("instrument_or_setup")), _s(c.get("measurement_conditions")),
                _s(c.get("purpose")), _s(c.get("key_findings")),
                json.dumps(c, ensure_ascii=False),
            ))

    def _emit_unmapped(self, r: PaperResult, sid: str, payload: dict) -> None:
        for i, u in enumerate(_as_list(payload.get("unmapped_findings"))):
            text = _s(u) if not isinstance(u, dict) else _s(u.get("finding") or u.get("text"))
            if text:
                r.add("unmapped_finding", (self._pid, sid, i, text, []))

    # ==================================================================
    # 图表
    # ==================================================================
    def _emit_figures(self, r: PaperResult) -> None:
        groups = {g.get("figure_id"): g for g in (self.image_groups.get("groups") or [])
                  if isinstance(g, dict)}
        for fid, f in self.figures.items():
            g = groups.get(fid) or {}
            kind = "table" if fid.startswith("table") else "figure"

            block_ids: list[str] = []
            for b in _as_list(g.get("caption_block_ids")) + _as_list(g.get("citation_block_ids")):
                if isinstance(b, str) and b in self.real_ids:
                    block_ids.append(b)
            block_ids = list(dict.fromkeys(block_ids))
            if not block_ids:
                r.issues.append({"rule_code": "FIGURE_EVIDENCE_EMPTY", "severity": "warn",
                                 "subject": fid, "message": "image_groups 未给出可用的题注/引用块",
                                 "detail": {}})

            imgs = [p for p in _as_list(f.get("image_paths")) if isinstance(p, str)]
            r.add("figure", (
                self._pid, fid, kind, _s(g.get("label")), _s(f.get("family")),
                _s(f.get("image_type")), _s(f.get("description")), _num(f.get("confidence")),
                len(_as_list(f.get("subfigures"))), len(_as_list(f.get("observations"))),
                len(_as_list(f.get("measured_quantities"))),
                json.dumps(f.get("measured_quantities"), ensure_ascii=False),
                json.dumps(f.get("sample_hints"), ensure_ascii=False),
                imgs, block_ids, g.get("page_idx"), g.get("ordinal"),
                json.dumps(f, ensure_ascii=False),
            ))

            for i, sub in enumerate(_as_list(f.get("subfigures"))):
                if isinstance(sub, dict):
                    r.add("figure_panel", (self._pid, fid, i, _s(sub.get("panel")),
                                           _s(sub.get("description"))))

            for i, obs in enumerate(_as_list(f.get("observations"))):
                if not isinstance(obs, dict):
                    continue
                src = _s(obs.get("source"))
                raw_ids = [str(e.get("id")) for e in _as_list(obs.get("evidence"))
                           if isinstance(e, dict) and e.get("id")]
                resolved: list[str] = []
                for raw in raw_ids:
                    res = self.resolver.resolve(raw, src, context_fid=fid)
                    r.resolutions.append((self.ingest_id, self._pid,
                                          "core.figure_observation", f"{fid}#{i}",
                                          raw, res.method, res.confidence,
                                          res.block_ids, res.note))
                    resolved.extend(res.block_ids)
                resolved = list(dict.fromkeys(resolved))
                status = "ok" if resolved and len(resolved) >= len(raw_ids) else (
                    "partial" if resolved else "unresolved")
                if not raw_ids:
                    # 纯视觉观察本来就没有文字证据；只有"本该有引用却没有"才算问题
                    status = "visual_only" if src == "visual" else "unresolved"
                    if src != "visual":
                        r.issues.append({"rule_code": "FIGURE_EVIDENCE_EMPTY", "severity": "warn",
                                         "subject": f"{fid}#{i}",
                                         "message": "非视觉观察项缺少 evidence 字段",
                                         "detail": {"source": src}})
                r.add("figure_observation", (
                    self._pid, fid, i, _s(obs.get("observation")) or "", src,
                    _num(obs.get("confidence")), raw_ids, resolved, status,
                ))

    # ==================================================================
    # 公式
    # ==================================================================
    def _emit_equations(self, r: PaperResult) -> None:
        for eid, e in self.equations.items():
            ident = e.get("identity") or {}
            bid = _s(ident.get("block_id"))
            if bid and bid not in self.real_ids:
                r.issues.append({"rule_code": "BLOCK_ID_DANGLING", "severity": "error",
                                 "subject": eid, "message": "公式 block_id 不存在",
                                 "detail": {"block_id": bid}})
                bid = None
            if not bid:
                r.issues.append({"rule_code": "EQUATION_NO_BLOCK", "severity": "warn",
                                 "subject": eid, "message": "公式无可回指 block", "detail": {}})
            symbols = _as_list(e.get("symbols"))
            r.add("equation", (
                self._pid, eid, bid, _s(ident.get("equation_number")),
                bool(ident.get("is_image")), _s(e.get("latex")), _s(ident.get("latex_hint")),
                _s(e.get("purpose")), _s(e.get("applicability_conditions")),
                json.dumps(symbols, ensure_ascii=False), len(symbols),
                json.dumps(e, ensure_ascii=False),
            ))

    # ==================================================================
    # 检索文档
    # ==================================================================
    def _emit_search_docs(self, r: PaperResult) -> None:
        docs = searchidx.build_docs(
            paper_id=self._pid,
            paper_row=next(iter(r.rows.get("paper", [])), None),
            paper_cols=COLS["paper"],
            wiki_rows=r.rows.get("sample_wiki", []),
            figure_rows=r.rows.get("figure", []),
            equation_rows=r.rows.get("equation", []),
            unmapped_rows=r.rows.get("unmapped_finding", []),
            figure_payloads=self.figures,
            sample_labels={sid: (self.sample_rich.get(sid) or {}) for sid in self.samples},
        )
        r.rows["search_document"] = docs


# ---------------------------------------------------------------------------
# 写库
# ---------------------------------------------------------------------------
DELETE_ORDER = ["search.document"]


def load_paper(conn: Connection, result: PaperResult) -> dict[str, int]:
    """单事务写入一篇的全部行。调用方负责事务边界。"""
    pid = result.paper_id
    counts: dict[str, int] = {}

    # 幂等：先清掉本篇（core.paper 级联到所有子表）
    # 但要把已算好的向量暂存下来——向量是昂贵外部计算，不该因重跑而丢失
    conn.execute("""
        CREATE TEMP TABLE IF NOT EXISTS embed_backup
        (doc_id text PRIMARY KEY, embed vector(384), embed_model text) ON COMMIT DROP
    """)
    conn.execute("DELETE FROM embed_backup")
    conn.execute("""
        INSERT INTO embed_backup (doc_id, embed, embed_model)
        SELECT doc_id, embed, embed_model FROM search.document
        WHERE paper_id = %s AND embed IS NOT NULL
    """, (pid,))

    conn.execute("DELETE FROM search.document WHERE paper_id = %s", (pid,))
    conn.execute("DELETE FROM ops.block_id_resolution WHERE paper_id = %s", (pid,))
    conn.execute("DELETE FROM ops.qa_issue WHERE paper_id = %s", (pid,))
    conn.execute("DELETE FROM lake.object_ref WHERE paper_id = %s", (pid,))
    conn.execute("DELETE FROM lake.paper_manifest WHERE paper_id = %s", (pid,))
    conn.execute("DELETE FROM core.paper WHERE paper_id = %s", (pid,))

    if result.objects:
        conn.execute("""
            CREATE TEMP TABLE IF NOT EXISTS lake_object_tmp
            (LIKE lake.object INCLUDING DEFAULTS) ON COMMIT DROP
        """)
        with conn.cursor() as cur:
            with cur.copy("COPY lake_object_tmp (object_id, bytes, media_type, kind, uri) FROM STDIN") as cp:
                for row in result.objects:
                    cp.write_row(row)
        conn.execute("""
            INSERT INTO lake.object (object_id, bytes, media_type, kind, uri)
            SELECT object_id, bytes, media_type, kind, uri FROM lake_object_tmp
            ON CONFLICT (object_id) DO NOTHING
        """)
        conn.execute("TRUNCATE lake_object_tmp")
        counts["lake.object"] = len(result.objects)

    # 顺序即外键顺序
    order = ["paper", "evidence_block", "alloy", "alloy_element", "process", "process_edge",
             "sample", "sample_data", "sample_trace", "sample_wiki", "processing_step",
             "phase", "property_value", "performance", "characterization", "unmapped_finding",
             "figure", "figure_panel", "figure_observation", "equation"]
    for table in order:
        rows = result.rows.get(table)
        if not rows:
            continue
        counts[f"core.{table}"] = copy_rows(conn, f"core.{table}", COLS[table], rows)

    if result.refs:
        counts["lake.object_ref"] = copy_rows(
            conn, "lake.object_ref", ("object_id", "paper_id", "rel_path", "role"), result.refs)

    for row in result.rows.get("__lake_manifest__", []):
        conn.execute(
            "INSERT INTO lake.paper_manifest (paper_id, run_id, object_count, total_bytes, manifest)"
            " VALUES (%s,%s,%s,%s,%s) ON CONFLICT (paper_id) DO UPDATE SET"
            " object_count=EXCLUDED.object_count, total_bytes=EXCLUDED.total_bytes,"
            " manifest=EXCLUDED.manifest, created_at=now()", row)
        counts["lake.paper_manifest"] = 1

    if result.rows.get("search_document"):
        counts["search.document"] = copy_rows(
            conn, "search.document", searchidx.DOC_COLS, result.rows["search_document"])
        # 还原上一轮已算好的向量（doc_id 稳定，内容未变则向量仍有效）
        restored = conn.execute("""
            UPDATE search.document d
               SET embed = b.embed, embed_model = b.embed_model
              FROM embed_backup b
             WHERE d.doc_id = b.doc_id AND d.paper_id = %s
        """, (pid,)).rowcount
        if restored:
            counts["search.document.embed_restored"] = restored

    if result.resolutions:
        # 同一 (src_table, src_id, raw_id) 只能有一行（PK 约束）
        result.resolutions = list({
            (r[2], r[3], r[4]): r for r in result.resolutions}.values())
        counts["ops.block_id_resolution"] = copy_rows(
            conn, "ops.block_id_resolution",
            ("ingest_id", "paper_id", "src_table", "src_id", "raw_id", "method",
             "confidence", "resolved_block_ids", "note"), result.resolutions)

    for issue in result.issues:
        conn.execute(
            "INSERT INTO ops.qa_issue (ingest_id, rule_code, severity, paper_id, subject, message, detail)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            (result.ingest_id, issue["rule_code"], issue["severity"], pid,
             issue.get("subject"), issue["message"], json.dumps(issue.get("detail") or {}, ensure_ascii=False)))

    return counts
