from dataclasses import dataclass

@dataclass
class RowProcessData:
    cnes: str
    ibge: str
    name: str
    chs_amb: float
    cbo_desc: str
    comp_value: str