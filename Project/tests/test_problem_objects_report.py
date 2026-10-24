from problem_objects_report import ProblemObjectsReportRepository


def test_problem_objects_report_extracts_summary_from_rows():
    repo = ProblemObjectsReportRepository(path="missing.xlsx")
    rows = [
        ["Единый реестр проблемных объектов"],
        ["по состоянию на 02.05.2026"],
        ["Общий итог", "", "71.0", "43.0", "518.95416"],
        ["Омская область", "", "7.0", "5.0", "84.3493"],
        ["Жилое", "", "2.0", "2.0", "40.09253"],
        ["Нарушены сроки завершения строительства более чем на 6 месяцев", "", "1.0", "1.0", "10.0"],
    ]

    report = repo._report_from_rows(rows)

    assert report.report_date == "02.05.2026"
    assert report.houses_count == 71
    assert report.developers_count == 43
    assert report.living_area_thousand_m2 == 518.95416
    assert len(report.regions) == 1
    assert report.regions[0].region == "Омская область"
