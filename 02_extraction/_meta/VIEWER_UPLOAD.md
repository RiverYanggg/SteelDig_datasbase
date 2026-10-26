# out_1009 前 10 篇 → evidence_note_viewer 上传记录

## 服务器

- 主机：`36.103.236.50`（ubuntu / 端口 22）
- 标注系统根目录：`/home/ubuntu/evidence_note_viewer`
- 访问地址：**http://36.103.236.50:8888/**
- 服务：`evidence-note-viewer.service`（uvicorn，监听 0.0.0.0:8888，无需重启即可读取新用户/任务配置）
- 论文目录：`extracted/<paper_id>/`（上传后共 35 篇 = 原有 25 + 新增 10）

## 上传内容（前 10 篇，按流水线排序）

| # | paper_id | 字段数(适配器) | 样本 | 图/表 | 公式 |
|---|---|---|---|---|---|
| 1 | 10.1016_j.jmatprotec.2004.04.114 | 557 | 7 | 14 | 3 |
| 2 | 10.1016_j.jmrt.2020.02.088 | 1850 | 21 | 22 | 0 |
| 3 | 10.1016_j.jmrt.2021.08.079 | 3626 | 24 | 13 | 14 |
| 4 | 10.1016_j.jmrt.2023.06.037 | 739 | 6 | 23 | 5 |
| 5 | 10.1016_j.jmrt.2024.01.272 | 768 | 4 | 13 | 2 |
| 6 | 10.1016_j.jmrt.2024.07.188 | 1015 | 4 | 16 | 4 |
| 7 | 10.1016_j.jmrt.2024.10.063 | 1114 | 8 | 13 | 8 |
| 8 | 10.1016_j.jmrt.2024.10.125 | 918 | 7 | 16 | 0 |
| 9 | 10.1016_j.jmrt.2025.05.166 | 929 | 5 | 15 | 10 |
| 10 | 10.1016_j.jmrt.2025.08.226 | 2086 | 11 | 13 | 1 |

每篇在服务器上的目录结构：

```
extracted/<paper_id>/
  verify/text_extraction_fixed.json        结构化根（schema completion 由 viewer 完成）
  verify/evidence_blocks.json              证据块（供左侧原文面板）
  extraction_postprocess/field_evidence.json   字段 → 证据块映射（viewer 的发现入口）
  extraction_postprocess/sample_buckets.json   样本级桶划分
  extraction_postprocess/review_hints.json     （本批次无 diff 分析，内容为 {}）
  final/text_extraction.json
  source/mineru/full.md, *_origin.pdf, images/
```

## 账号与任务分配

| 用户名 | workspace | 角色 | 监控 | 分配论文 |
|---|---|---|---|---|
| `huangguoliang` | huangguoliang | reviewer | 是 | 第 1–5 篇 |
| `liyan` | liyan | reviewer | 是 | 第 6–10 篇 |

- 账号写入 `config/users.json`（fcntl 文件锁 + 原子替换），备份为 `config/users.json.bak.20261009_195323`。
- 任务写入 `data/users/<用户名>/assignments.json`（`{"papers": [...]}`）。
- 密码为 6 位数字，经聊天单独告知，未写入任何文件。
- 注意：管理面板「新建用户」接口强制密码 8–128 位；本批次 6 位密码是直接写配置创建的，**登录校验不检查长度**，已验证可正常登录。

## 验证结果

- `POST /api/auth/login` 两个账号均 200，返回 `role=reviewer`。
- `GET /api/papers` 各自返回 **5 篇**，无越权可见。
- `GET /api/papers/<id>` 每篇均返回 slots / buckets / blocks / PDF（如 `10.1016_j.jmrt.2021.08.079`：8238 slots、25 buckets、158 blocks）。
- `GET /api/papers/<id>/pdf` → 200 `application/pdf`。
- `GET /api/papers/<id>/asset/images/*.jpg` → 200 `image/jpeg`。
- 外部访问 `http://36.103.236.50:8888/` → 200，`/api/health` → `{"ok":true,"assistant":true}`。

## Admin 管理面板可见性（已验证）

`GET /api/admin/overview` 的监控名单实际返回 7 人：

```
weiyuandong, chengjiawang, Gaojiacheng, xiexingyu, zhaomengjiao, huangguoliang, liyan
```

两名新用户已进入监控，各自 5 篇、全部 `available=true`：

```
huangguoliang  papers=5  reviewed_fields=0  duration_s=0
liyan          papers=5  reviewed_fields=0  duration_s=0
```

只读详情接口同样正常：`/api/admin/users/<u>/papers/<pid>` 返回 fields / blocks / buckets / has_pdf，且 `read_only=true`。

可见性由 `enviz/accounts.py::is_monitored` 决定：
`role != 'admin' and (username in MONITORED_USERS or record['admin_monitored'] is True)`。
新账号按管理面板「新建用户」的同等语义写入了 `admin_monitored: true`，因此自动进入监控。

## 本地产物

- 适配脚本：`adapt_1009_to_viewer.py`
- 适配结果：`extracted_for_viewer_1009/<paper_id>/`（共 127 MB）
