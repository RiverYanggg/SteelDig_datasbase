# 入库质量与覆盖率报告

- ingest_id: `52`

## 表行数

| 表 | 行数 |
|---|---:|
| `canon.alloy_family` | 23 |
| `canon.characterization_technique` | 21 |
| `canon.element` | 83 |
| `canon.phase` | 41 |
| `core.alloy` | 250 |
| `core.alloy_element` | 986 |
| `core.characterization` | 2,183 |
| `core.equation` | 396 |
| `core.evidence_block` | 10,316 |
| `core.figure` | 1,041 |
| `core.figure_observation` | 12,405 |
| `core.figure_panel` | 3,406 |
| `core.paper` | 68 |
| `core.performance` | 294 |
| `core.phase` | 1,493 |
| `core.process` | 382 |
| `core.process_edge` | 195 |
| `core.processing_step` | 2,610 |
| `core.property_value` | 1,508 |
| `core.sample` | 638 |
| `core.sample_data` | 638 |
| `core.sample_trace` | 68,944 |
| `core.sample_wiki` | 638 |
| `core.unmapped_finding` | 2,956 |
| `lake.object` | 6,667 |
| `lake.object_ref` | 6,695 |
| `lake.paper_manifest` | 68 |
| `ops.block_id_resolution` | 12,793 |
| `ops.ingest_log` | 856 |
| `ops.ingest_run` | 52 |
| `ops.qa_issue` | 844 |
| `ops.qa_rule` | 12 |
| `ops.run` | 4 |
| `ops.schema_migration` | 13 |
| `search.document` | 5,099 |

## 属性量（按分区）

| 分区 | 总行 | 可数值化 | 区间 | 定性 |
|---|---:|---:|---:|---:|
| mechanical | 1,332 | 1,139 | 79 | 165 |
| physical | 176 | 165 | 2 | 7 |

## 关键指标分布（已单位归一）

| 指标 | 行数 | 可数值化 | 最小 | 最大 | 单位 |
|---|---:|---:|---:|---:|---|
| hardness | 329 | 312 | 150.0 | 16500.0 | MPa |
| elongation | 305 | 272 | 0.1 | 86.0 | % |
| yield_strength | 273 | 235 | 30.0 | 2046.0 | MPa |
| ultimate_tensile_strength | 268 | 244 | 53.8 | 2294.0 | MPa |
| reduction_of_area | 2 | 2 | 78.0 | 80.0 | % |

## block_id 对齐

| 方法 | 数量 |
|---|---:|
| figure_group | 11,796 |
| direct | 989 |
| unresolved | 8 |

## 质量问题

| 规则 | 级别 | 数量 |
|---|---|---:|
| FIGURE_EVIDENCE_EMPTY | warn | 821 |
| BLOCK_ID_UNRESOLVED | warn | 15 |
| WIKI_SECTION_LEAK | warn | 8 |

## 合金族分布

| 合金族 | 合金数 |
|---|---:|
| fe_mn_al_c | 160 |
| steel | 39 |
| fe_al | 24 |
| pure_metal | 12 |
| None | 7 |
| twip | 2 |
| fe_cr | 2 |
| fe_mn | 2 |
| low_density_steel | 1 |
| stainless | 1 |
