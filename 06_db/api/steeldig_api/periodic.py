"""元素周期表布局（用于成分检索页）。

只做布局，不承载化学数据——元素的名称/原子量在 canon.element 里。
采用 18 列标准布局，镧系/锕系单独两行（La、Ac 占第 3 列，Ce–Lu / Th–Lr 在下方）。
"""
from __future__ import annotations

MAIN = [
    ["H"] + [None] * 16 + ["He"],
    ["Li", "Be"] + [None] * 10 + ["B", "C", "N", "O", "F", "Ne"],
    ["Na", "Mg"] + [None] * 10 + ["Al", "Si", "P", "S", "Cl", "Ar"],
    ["K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni",
     "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr"],
    ["Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd",
     "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe"],
    ["Cs", "Ba", "La", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt",
     "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn"],
    ["Fr", "Ra", "Ac", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds",
     "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og"],
]

F_BLOCK = [
    ["Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"],
    ["Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"],
]

# 常见基体/合金元素的中文名（表格里悬停提示用，缺失则显示符号）
ZH_NAME = {
    "H": "氢", "B": "硼", "C": "碳", "N": "氮", "O": "氧", "Mg": "镁", "Al": "铝",
    "Si": "硅", "P": "磷", "S": "硫", "Ca": "钙", "Ti": "钛", "V": "钒", "Cr": "铬",
    "Mn": "锰", "Fe": "铁", "Co": "钴", "Ni": "镍", "Cu": "铜", "Zn": "锌",
    "Y": "钇", "Zr": "锆", "Nb": "铌", "Mo": "钼", "W": "钨", "Be": "铍",
    "Sn": "锡", "Sb": "锑", "Pb": "铅", "As": "砷", "La": "镧", "Ce": "铈",
    "Nd": "钕", "Ta": "钽",
}


def cells(available: dict[str, int] | None = None) -> list[dict]:
    """返回带 grid 坐标的单元格；available 为 {元素: 合金数}，用于提示“库里有多少”。"""
    available = available or {}
    out: list[dict] = []
    for r, row in enumerate(MAIN, start=1):
        for c, sym in enumerate(row, start=1):
            if not sym:
                continue
            out.append({
                "symbol": sym, "row": r, "col": c,
                "zh": ZH_NAME.get(sym, ""),
                "n": available.get(sym, 0),
                "f": False,
            })
    for i, row in enumerate(F_BLOCK):
        for j, sym in enumerate(row):
            out.append({
                "symbol": sym, "row": 8 + i, "col": 3 + j,
                "zh": ZH_NAME.get(sym, ""),
                "n": available.get(sym, 0),
                "f": True,
            })
    return out


def symbols() -> set[str]:
    return {c["symbol"] for c in cells()}
