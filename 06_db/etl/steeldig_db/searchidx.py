"""检索文档构建：把"事实单元"折叠成"检索单元"。

一篇论文会被拆成多类可检索单元：

    paper      标题 + 摘要 + 研究范围
    wiki       研究对象词条（中文，语义检索主力语料）
    figure     图/表的描述与观察项
    equation   公式用途 + latex
    finding    未归类发现（往往是最有信息量的残渣）

同一份文本在 DB 里存两份职责：search.document.body 给人看，
search.document.content_seg 给索引看（jieba 分词后的形态）。
"""
from __future__ import annotations

import json
from typing import Any, Iterable

from .text import lang_of, segment, truncate

DOC_COLS = ("doc_id", "doc_type", "paper_id", "sample_id", "ref_id",
            "title", "body", "content_seg", "lang", "meta")


def _doc(doc_type: str, paper_id: str, ref: str, title: str | None, body: str,
         sample_id: str | None = None, meta: dict | None = None) -> tuple:
    body = (body or "").strip()
    doc_id = f"{doc_type}:{paper_id}:{ref}"
    return (
        doc_id, doc_type, paper_id, sample_id, ref,
        title, body, segment(body), lang_of(body),
        json.dumps(meta or {}, ensure_ascii=False),
    )


def build_docs(*, paper_id: str, paper_row: tuple | None, paper_cols: tuple,
               wiki_rows: Iterable[tuple], figure_rows: Iterable[tuple],
               equation_rows: Iterable[tuple], unmapped_rows: Iterable[tuple],
               figure_payloads: dict[str, dict],
               sample_labels: dict[str, dict]) -> list[tuple]:
    docs: list[tuple] = []
    idx = {c: i for i, c in enumerate(paper_cols)}

    if paper_row:
        g = lambda c: paper_row[idx[c]]
        body = "\n".join(x for x in [
            g("title"), g("abstract"), g("paper_scope"),
            "关键字: " + "、".join(g("keywords") or []),
            "作者: " + "、".join(g("authors") or []),
            "期刊: " + (g("journal") or ""), "年份: " + str(g("year") or ""),
        ] if x)
        docs.append(_doc("paper", paper_id, paper_id, g("title"), body,
                         meta={"doi": g("doi"), "year": g("year"),
                               "research_type": g("research_type")}))

    wcols = ("paper_id", "sample_id", "run_id", "summary", "mechanisms", "n_mechanisms",
             "conclusions", "payload", "content", "content_seg")
    widx = {c: i for i, c in enumerate(wcols)}
    for row in wiki_rows:
        g = lambda c: row[widx[c]]
        body = "\n".join(x for x in [
            g("summary"), "\n".join(g("mechanisms") or []), g("conclusions"),
        ] if x)
        if not body:
            body = g("content") or ""
        docs.append(_doc("wiki", paper_id, g("sample_id"), g("sample_id"), body,
                         sample_id=g("sample_id"),
                         meta={"n_mechanisms": g("n_mechanisms")}))

    fcols = ("paper_id", "figure_id", "kind", "label", "family", "image_type", "description",
             "confidence", "n_subfigures", "n_observations", "n_measured", "measured_quantities",
             "sample_hints", "image_paths", "block_ids", "page_idx", "ordinal", "payload")
    fidx = {c: i for i, c in enumerate(fcols)}
    for row in figure_rows:
        g = lambda c: row[fidx[c]]
        payload = figure_payloads.get(g("figure_id")) or json.loads(g("payload") or "{}")
        obs = [o.get("observation") for o in (payload.get("observations") or [])
               if isinstance(o, dict) and o.get("observation")]
        body = "\n".join(x for x in [g("label"), g("description"), "\n".join(obs)] if x)
        docs.append(_doc(g("kind"), paper_id, g("figure_id"), g("label"), body,
                         meta={"image_type": g("image_type"), "n_observations": g("n_observations"),
                               "block_ids": g("block_ids")}))

    ecols = ("paper_id", "equation_id", "block_id", "equation_number", "is_image", "latex",
             "latex_hint", "purpose", "applicability", "symbols", "n_symbols", "payload")
    eidx = {c: i for i, c in enumerate(ecols)}
    for row in equation_rows:
        g = lambda c: row[eidx[c]]
        body = "\n".join(x for x in [g("purpose"), g("applicability"), g("latex")] if x)
        docs.append(_doc("equation", paper_id, g("equation_id"), g("equation_number"), body,
                         meta={"block_id": g("block_id")}))

    for row in unmapped_rows:
        # (paper_id, sample_id, idx, text, block_ids)
        body = row[3]
        if body:
            docs.append(_doc("finding", paper_id, f"{row[1]}#{row[2]}", None, body,
                             sample_id=row[1]))

    return docs
