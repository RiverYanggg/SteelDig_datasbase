"""SteelDig 材料知识库 —— ETL 与治理工具包。

模块职责（对应总体架构图的四层）::

    lake.py        [资产湖] 内容寻址对象存储，写入后不可变
    quantity.py    [事实源] 自由文本 → 数值/区间/单位归一化
    blockresolve.py[事实源] 合成 block_id → 真实证据块（溯源对齐）
    composition.py [规范化] 成分 → formula / chemsys / 元素长表
    family.py      [规范化] 成分+关键词 → 合金族（规则引擎）
    searchidx.py   [检索层] 构建统一检索文档 + 分词 + 向量
    qa.py          [治理]   质量规则与问题上报
    ingest.py      [编排]   逐篇 ETL 主流程
"""

__version__ = "1.0.0"
