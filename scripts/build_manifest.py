import json, os, re, hashlib
from pathlib import Path
from datetime import datetime

DB = Path('/Users/mac/Desktop/SteelDig/database')
MINERU = DB / '01_raw/mineru_source'
EXT = DB / '02_extraction'
OUT = DB / '03_manifests'
OUT.mkdir(parents=True, exist_ok=True)

UUID_RE = re.compile(r'^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})_(.+)$')
HASH_RE = re.compile(r'^[0-9a-f]{40,64}\.[a-zA-Z]+$')

def load(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except Exception:
        return None


def title_from_md(pd):
    md = pd / 'full.md'
    if not md.is_file():
        return None
    try:
        for line in md.read_text(encoding='utf-8').splitlines():
            t = line.strip()
            if t.startswith('#'):
                t = t.lstrip('#').strip()
                if len(t) > 3:
                    return t
    except Exception:
        pass
    return None

# ---------- 1. MinerU 资产 ----------
mineru = {}
for pd in sorted(MINERU.iterdir()):
    if not pd.is_dir():
        continue
    pid = pd.name
    rec = {'paper_id': pid, 'files': {}, 'images': [], 'bytes': 0}
    uuid = None
    for f in sorted(pd.iterdir()):
        if f.is_dir():
            continue
        m = UUID_RE.match(f.name)
        suffix = m.group(2) if m else f.name
        if m:
            uuid = m.group(1)
        rec['files'][suffix] = f.name
    imgdir = pd / 'images'
    if imgdir.is_dir():
        rec['images'] = sorted(x.name for x in imgdir.iterdir() if x.is_file())
        rec['bytes'] += sum(x.stat().st_size for x in imgdir.iterdir() if x.is_file())
    rec['bytes'] += sum(f.stat().st_size for f in pd.iterdir() if f.is_file())
    rec['uuid'] = uuid
    rec['image_count'] = len(rec['images'])

    # 论文元信息（从 preprocess 若已有；否则留空由提取端补）
    pc = None
    for cand in EXT.glob(f'*/{pid}/preprocess/paper_context.json'):
        pc = load(cand)
        break
    rec['title'] = (pc or {}).get('title') or title_from_md(pd)
    rec['page_count'] = (pc or {}).get('page_count')
    rec['block_count'] = (pc or {}).get('block_count')
    rec['figure_count'] = (pc or {}).get('figure_count')
    rec['has_pdf'] = 'origin.pdf' in rec['files']
    mineru[pid] = rec

# ---------- 2. 提取资产 ----------
def scan_paper(pd):
    """扫描 02_extraction/<paper_id>/ 单个论文目录（已平铺，无批次层级）"""
    papers = []
    if True:
        pid = pd.name
        out = pd / 'output'
        fig = sorted((out / 'figure').glob('*.json')) if (out / 'figure').is_dir() else []
        samples = sorted([x for x in (out / 'sample').glob('*.json') if not x.name.endswith('.data.json')]) if (out / 'sample').is_dir() else []
        data = sorted((out / 'sample').glob('*.data.json')) if (out / 'sample').is_dir() else []
        traces = sorted((out / 'sample_trace').glob('*.json')) if (out / 'sample_trace').is_dir() else []
        wikis = sorted((out / 'wiki').glob('*.json')) if (out / 'wiki').is_dir() else []
        eqs = sorted((out / 'equation').glob('*.json')) if (out / 'equation').is_dir() else []
        disc = out / 'discover' / 'result.json'
        pc = load(pd / 'preprocess' / 'paper_context.json') or {}
        timing = load(pd / 'timing.json')
        nbytes = sum(f.stat().st_size for f in pd.rglob('*') if f.is_file())
        papers.append({
            'paper_id': pid,
            'title': pc.get('title') or title_from_md(MINERU / pid), 'page_count': pc.get('page_count'),
            'block_count': pc.get('block_count'),
            'counts': {'figure': len(fig), 'sample': len(samples), 'data': len(data),
                       'trace': len(traces), 'wiki': len(wikis), 'equation': len(eqs)},
            'has_discover': disc.is_file(),
            'has_preprocess': (pd / 'preprocess').is_dir(),
            'has_timing': timing is not None,
            'bytes': nbytes,
        })
    return papers

# 74 篇提取结果已平铺在 02_extraction/<paper_id>/，不区分日期与模型
# ---------- 3. 汇总 ----------
all_papers = []
for pd in sorted(EXT.iterdir()):
    if pd.is_dir() and not pd.name.startswith('_'):
        all_papers += scan_paper(pd)
ext_by_pid = {}
for r in all_papers:
    ext_by_pid.setdefault(r['paper_id'], []).append(r)

summary = {
    'schema_version': 'database-manifest-v1',
    'generated_at': datetime.now().astimezone().isoformat(timespec='seconds'),
    'sources': {
        'mineru': '01_extraction_verification/workspaces_82/.mineru_source',
        'extraction': [
            'Agentic_extract4paper/Agentic_Extractor_2.0/out_0915/pro',
            'Agentic_extract4paper/Agentic_Extractor_2.0/out_0917/pro',
            'Agentic_extract4paper/Agentic_Extractor_2.0/out_0919/pro',
            'Agentic_extract4paper/Agentic_Extractor_2.0/out_1009',
        ],
        'layout_note': '四个批次已合并平铺为 02_extraction/<paper_id>/，不区分日期与模型',
    },
    'mineru_papers': len(mineru),
    'extraction_papers_unique': len(ext_by_pid),
    'papers_with_both_assets': len(set(mineru) & set(ext_by_pid)),
}
json.dump(summary, open(OUT / 'dataset_summary.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump({'schema_version': 'mineru-manifest-v1', 'papers': mineru},
          open(OUT / 'mineru_manifest.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump({'schema_version': 'extraction-manifest-v1', 'papers': all_papers},
          open(OUT / 'extraction_manifest.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# 逐论文主索引（横向合并 MinerU + 提取）
rows = []
for pid in sorted(set(mineru) | set(ext_by_pid)):
    m = mineru.get(pid, {})
    e = ext_by_pid.get(pid, [])
    rows.append({
        'paper_id': pid,
        'title': (e[0]['title'] if e else None) or m.get('title'),
        'page_count': (e[0]['page_count'] if e else None) or m.get('page_count'),
        'has_mineru': pid in mineru,
        'mineru_images': m.get('image_count', 0),
        'has_pdf': m.get('has_pdf', False),
        'has_extraction': bool(e),
        'figures': sum(x['counts']['figure'] for x in e),
        'samples': sum(x['counts']['sample'] for x in e),
        'equations': sum(x['counts']['equation'] for x in e),
    })
json.dump({'schema_version': 'paper-index-v1', 'papers': rows},
          open(OUT / 'paper_index.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# CSV 便于查看
import csv
with open(OUT / 'paper_index.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows:
        w.writerow(dict(r))

print(json.dumps(summary, ensure_ascii=False, indent=2))
print('\nmissing in mineru:', sorted(set(ext_by_pid) - set(mineru)))
print('mineru but not extracted:', sorted(set(mineru) - set(ext_by_pid)))
