# SteelDig 演示视频 v2

审看入口：[index.html](index.html)。直接打开即可播放视频，查看逐镜截图、旁白和原始录屏。

## 交付文件

| 文件 | 内容 |
| --- | --- |
| [SteelDig_演示预览_v2.mp4](SteelDig_演示预览_v2.mp4) | 2 分 32 秒，1920×1080，25 fps，H.264 / AAC，中文合成旁白及画面字幕 |
| [SteelDig_中文字幕_v2.srt](SteelDig_中文字幕_v2.srt) | 独立中文字幕，供剪辑使用；MP4 已含画面字幕 |
| [Word 分镜](../../../SteelDig_演示视频_分镜脚本.docx) | 新版分镜，已同步到用户原始文件位置 |
| [PDF 分镜](SteelDig_演示视频_分镜脚本.pdf) | 横向 A4，5 页，已检查表格和分页 |
| [Markdown 分镜](../脚本分镜.md) | 叙事、台词、操作、核验数据和复现命令 |
| [分镜总览.jpg](分镜总览.jpg) / [封面.png](封面.png) | 成片九镜总览及视频封面 |
| [scenes.json](scenes.json) / [narration_timing.json](narration_timing.json) | 可编辑台词、镜头长度及实际语音时间 |
| recordings/ / screenshots/ | 九段真实浏览器操作录屏及桌面、手机截图 |
| [verification.json](verification.json) | 录制时的服务数据与浏览器核验快照 |

## 本次完成

围绕同一 LN 样品串联成分筛选、性能查看、原文表格、最近候选、关键词检索、校订入口和质量状态。SQL 与重灌演示移到可选技术附录。

前端优化了首页、样品详情、证据表格和手机布局；修复了性能证据不能点击、校订属性选项缺少路径的问题。证据表格经过白名单清理后展示。相关测试 18 项通过。

实测 Al 8–11 / Mn 25–30 wt% 返回 41 个合金；LN 屈服强度为 685 MPa，与 b0029 来源表格一致。最近候选 Al 12.6 wt%，距目标下限 20 wt% 低 7.4 个百分点。当前质量快照为 0 error、844 warn。

录屏浏览器拦截 GET / HEAD / OPTIONS 以外的请求。校订只填写草稿，未提交；未重灌数据库。690 是演示草稿，不代表已核验的修正值。

## 使用边界

这是带本机合成旁白的完整审看预览，可用于确认节奏、画面和台词；正式发布前可替换真人配音并重新核对数据快照。0 error 不代表数据没有缺陷。原版视频保留在上级目录。

复现命令见 Markdown 分镜；浏览器播放检查可运行 `capture_demo.py --review`，结果写入 `playback_verification.json`。
