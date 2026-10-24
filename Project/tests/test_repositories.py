import json

from repositories import LocalDevelopersRepository, LocalProjectsRepository


def test_local_developers_repository_finds_developer_by_inn(tmp_path):
    data_path = tmp_path / "developers.jsonl"
    data_path.write_text(
        json.dumps(
            {
                "devInn": "5050102110",
                "devOgrn": "1135050000447",
                "devShortCleanNm": "10 КВАРТАЛ",
                "regRegionDesc": "Московская область",
                "problObjCnt": 1,
                "buildObjCnt": 2,
                "comissObjCnt": 3,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    repo = LocalDevelopersRepository(data_path)

    profile = repo.find_by_inn("5050102110")

    assert profile is not None
    assert profile.name == "10 КВАРТАЛ"
    assert profile.region == "Московская область"
    assert profile.problem_objects_count == 1
    assert profile.building_objects_count == 2
    assert profile.commissioned_objects_count == 3
    assert profile.registration_date.year == 2013


def test_local_developers_repository_searches_by_name_and_inn(tmp_path):
    data_path = tmp_path / "developers.jsonl"
    rows = [
        {
            "devInn": "5050102110",
            "devOgrn": "1135050000447",
            "devShortCleanNm": "10 КВАРТАЛ",
        },
        {
            "devInn": "7701651356",
            "devOgrn": "1067746000000",
            "devShortCleanNm": "2МЕН ГРУПП",
        },
    ]
    data_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )

    repo = LocalDevelopersRepository(data_path)

    by_name = repo.search("квартал")
    by_inn = repo.search("770165")

    assert len(by_name) == 1
    assert by_name[0].inn == "5050102110"
    assert len(by_inn) == 1
    assert by_inn[0].name == "2МЕН ГРУПП"


def test_local_projects_repository_finds_projects_by_developer_inn(tmp_path):
    data_path = tmp_path / "projects.jsonl"
    data_path.write_text(
        json.dumps(
            {
                "objId": 25002,
                "developer": {"devInn": "5050102110"},
                "objAddr": "село Озерецкое, д. 30",
                "objCommercNm": "ЖК Мечта",
                "objReady100PercDt": "2021-12-31",
                "objSquareLiving": 5487.8,
                "objProblemFlg": 1,
                "problemFlag": "PROBLEM",
                "siteStatus": "Строящиеся",
                "objStatus": 0,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    repo = LocalProjectsRepository(data_path, snapshot_date="2022-01-10")

    projects = repo.find_by_developer_inn("5050102110")

    assert len(projects) == 1
    assert projects[0].name == "ЖК Мечта"
    assert projects[0].planned_date.year == 2021
    assert projects[0].area == 5487.8
    assert projects[0].is_problem is True
    assert projects[0].delay_days_avg == 10
    assert projects[0].delay_count == 1
