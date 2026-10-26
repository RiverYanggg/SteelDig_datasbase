"""文本处理：分词、语种判定、JSON Pointer 定位。"""
from __future__ import annotations

import logging
import re
from typing import Any

import jieba

jieba.setLogLevel(logging.WARNING)

_CJK = re.compile(r"[\u4e00-\u9fff]")
_PTR_TOKEN = re.compile(r"\.([^.\[\]]+)|\[(\d+)\]")
_TOKEN_SPLIT = re.compile(r"[\s\u3000]+")


def has_cjk(text: str) -> bool:
    return bool(_CJK.search(text or ""))


def lang_of(text: str) -> str:
    t = text or ""
    cjk = len(_CJK.findall(t))
    latin = len(re.findall(r"[A-Za-z]", t))
    if cjk and latin > cjk * 3:
        return "en"
    if cjk and latin:
        return "mixed"
    if cjk:
        return "zh"
    return "en"


def segment(text: str) -> str:
    """中文用 jieba 切分、空白连接；纯英文原样保留。

    这样 search.document.tsv 就能用 simple 配置索引中英文混合语料。
    生产环境若引入 zhparser / OpenSearch IK，可退化为原文直接索引。
    """
    t = (text or "").strip()
    if not t:
        return ""
    if not has_cjk(t):
        return t
    tokens = []
    for tok in jieba.cut(t, cut_all=False):
        tok = tok.strip()
        if tok and not _TOKEN_SPLIT.match(tok):
            tokens.append(tok)
    return " ".join(tokens)


def truncate(text: str | None, n: int = 320) -> str:
    t = re.sub(r"\s+", " ", text or "").strip()
    return t if len(t) <= n else t[: n - 1] + "…"


def json_pointer(obj: Any, path: str) -> Any:
    """解析 `$.a[0].b` 形式的路径；未命中时抛 KeyError。

    与 core.sample_trace.path 使用同一命名空间，用于校验"值-证据"一一对应。
    """
    if path in ("$", ""):
        return obj
    if not path.startswith("$"):
        raise ValueError(f"非法 JSON Pointer: {path}")
    cur = obj
    for m in _PTR_TOKEN.finditer(path[1:]):
        if m.group(1) is not None:
            key = m.group(1)
            if not isinstance(cur, dict) or key not in cur:
                raise KeyError(path)
            cur = cur[key]
        else:
            idx = int(m.group(2))
            if not isinstance(cur, list) or idx >= len(cur):
                raise KeyError(path)
            cur = cur[idx]
    return cur


def flatten_strings(node: Any, prefix: str = "$") -> list[tuple[str, str]]:
    """把 JSON 里所有字符串叶子展开为 (path, value)，用于 wiki 类文本拼接。"""
    out: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for k, v in node.items():
            out.extend(flatten_strings(v, f"{prefix}.{k}"))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.extend(flatten_strings(v, f"{prefix}[{i}]"))
    elif isinstance(node, str) and node.strip():
        out.append((prefix, node.strip()))
    return out
