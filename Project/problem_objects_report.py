import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from config import settings


@dataclass(frozen=True)
class ProblemObjectsRegionSummary:
    region: str
    houses_count: int
    developers_count: int
    living_area_thousand_m2: float


@dataclass(frozen=True)
class ProblemObjectsReport:
    report_date: str | None
    houses_count: int
    developers_count: int
    living_area_thousand_m2: float
    regions: list[ProblemObjectsRegionSummary]


class ProblemObjectsReportRepository:
    NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    NON_REGION_LABELS = {
        "общий итог",
        "жилое",
        "нежилое",
        "открыто конкурсное производство в соответствии с федеральным законом №127-фз",
        "введена иная процедура банкротства в соответствии с федеральным законом №127-фз",
        "нарушены сроки завершения строительства более чем на 6 месяцев",
        "нарушены сроки передачи объекта долевого строительства более чем на 6 месяцев",
    }

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or settings.problem_objects_report_path)
        self._report: ProblemObjectsReport | None = None

    def load(self) -> ProblemObjectsReport | None:
        if self._report is None:
            self._report = self._load_report()
        return self._report

    def _load_report(self) -> ProblemObjectsReport | None:
        if not self.path.exists():
            print(f"[ProblemObjectsReport] Файл не найден: {self.path}")
            return None

        rows = self._read_xlsx_rows(self.path)
        report = self._report_from_rows(rows)
        print(
            "[ProblemObjectsReport] Загружено: "
            f"{report.houses_count} домов, {report.developers_count} застройщиков"
        )
        return report

    def _report_from_rows(self, rows: list[list[str]]) -> ProblemObjectsReport:
        report_date = self._extract_report_date(rows)
        total_row = next((row for row in rows if self._cell(row, 0).lower() == "общий итог"), [])

        return ProblemObjectsReport(
            report_date=report_date,
            houses_count=self._int_cell(total_row, 2),
            developers_count=self._int_cell(total_row, 3),
            living_area_thousand_m2=self._float_cell(total_row, 4),
            regions=self._extract_regions(rows),
        )

    def _extract_report_date(self, rows: list[list[str]]) -> str | None:
        for row in rows[:5]:
            text = " ".join(cell for cell in row if cell)
            match = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
            if match:
                return match.group(1)
        return None

    def _extract_regions(self, rows: list[list[str]]) -> list[ProblemObjectsRegionSummary]:
        regions = []
        for row in rows:
            label = self._cell(row, 0)
            if not label or self._is_non_region_label(label):
                continue

            houses = self._int_cell(row, 2)
            developers = self._int_cell(row, 3)
            area = self._float_cell(row, 4)
            if houses == 0 and developers == 0 and area == 0:
                continue

            regions.append(
                ProblemObjectsRegionSummary(
                    region=label,
                    houses_count=houses,
                    developers_count=developers,
                    living_area_thousand_m2=area,
                )
            )
        return regions

    def _read_xlsx_rows(self, path: Path) -> list[list[str]]:
        with zipfile.ZipFile(path) as archive:
            shared = self._read_shared_strings(archive)
            sheet_path = self._first_sheet_path(archive)
            root = ET.fromstring(archive.read(sheet_path))
            rows = []
            for row in root.findall(".//m:sheetData/m:row", self.NS):
                rows.append(self._read_row(row, shared))
            return rows

    def _read_shared_strings(self, archive: zipfile.ZipFile) -> list[str]:
        if "xl/sharedStrings.xml" not in archive.namelist():
            return []

        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        return [
            "".join(text.text or "" for text in item.findall(".//m:t", self.NS))
            for item in root.findall("m:si", self.NS)
        ]

    def _first_sheet_path(self, archive: zipfile.ZipFile) -> str:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        relmap = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
        sheet = workbook.find(".//m:sheet", self.NS)
        rel_id = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        target = relmap[rel_id].lstrip("/")
        return target if target.startswith("xl/") else f"xl/{target}"

    def _read_row(self, row: ET.Element, shared: list[str]) -> list[str]:
        values = {}
        for cell in row.findall("m:c", self.NS):
            index = self._column_index(cell.attrib.get("r", ""))
            value_node = cell.find("m:v", self.NS)
            value = "" if value_node is None else value_node.text or ""
            if cell.attrib.get("t") == "s" and value:
                value = shared[int(value)]
            values[index] = value

        max_index = max(values.keys(), default=-1)
        return [values.get(index, "") for index in range(max_index + 1)]

    def _column_index(self, cell_reference: str) -> int:
        letters = "".join(char for char in cell_reference if char.isalpha())
        index = 0
        for char in letters:
            index = index * 26 + ord(char.upper()) - 64
        return index - 1

    def _is_non_region_label(self, label: str) -> bool:
        return label.lower() in self.NON_REGION_LABELS

    def _cell(self, row: list[str], index: int) -> str:
        return str(row[index]).strip() if len(row) > index else ""

    def _int_cell(self, row: list[str], index: int) -> int:
        return int(float(self._cell(row, index) or 0))

    def _float_cell(self, row: list[str], index: int) -> float:
        return float(self._cell(row, index) or 0)
