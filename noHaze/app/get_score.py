import os
from sqlalchemy import create_engine, text

from columns import column_mapping

DB_URL = os.getenv("NOHAZE_DB_URL", "postgresql://postgres:Huma2005@localhost:5432/practicum")
engine = create_engine(DB_URL)

ALLOWED_SCORE_COLUMNS = set(column_mapping.values())
RELIABILITY_FILTERS = {
    "any": None,
    "known": "a.developer_reliability_score IS NOT NULL",
    "medium": "a.developer_reliability_score >= 60",
    "high": "a.developer_reliability_score >= 80",
}


def quote_column(column):
    if column not in ALLOWED_SCORE_COLUMNS:
        raise ValueError(f"Недопустимый критерий: {column}")
    return f'a."{column}"'


def get_buildings(data, reliability_mode="any"):
    def build_weighted_query(weights_dict):
        weighted_terms = []
        params = {}

        for idx, (column, weight) in enumerate(weights_dict.items()):
            column_expr = quote_column(column)
            param_name = f"weight_{idx}"
            weighted_terms.append(f"COALESCE({column_expr}, 0) * :{param_name}")
            params[param_name] = weight

        weighted_sum_expr = " +\n    ".join(weighted_terms) or "0"
        selected_score_columns = ",\n                ".join(
            f"{quote_column(column)} AS \"{column}\""
            for column in weights_dict
        )
        if selected_score_columns:
            selected_score_columns += ","

        reliability_condition = RELIABILITY_FILTERS.get(reliability_mode)
        where_clause = f"WHERE {reliability_condition}" if reliability_condition else ""
        order_expr = "weighted_score DESC, a.id" if weights_dict else "a.developer_reliability_score DESC NULLS LAST, a.id"

        query = text(f"""
            SELECT
                a.id,
                a.address,
                a.developer_name,
                a.developer_inn,
                a.developer_reliability_score,
                {selected_score_columns}
                ({weighted_sum_expr}) AS weighted_score,
                ST_X(ST_Centroid(a.geometry)) AS longitude,
                ST_Y(ST_Centroid(a.geometry)) AS latitude
            FROM public.new_buildings a
            {where_clause}
            ORDER BY {order_expr}
            LIMIT 5
        """)

        return query, params

    query, params = build_weighted_query(data)
    res_buildings = {}

    with engine.connect() as conn:
        result = conn.execute(query, params).mappings().all()

    for idx, row in enumerate(result):
        res_buildings[idx] = {
            "id": row["id"],
            "address": row["address"],
            "developer_name": row["developer_name"],
            "developer_inn": row["developer_inn"],
            "developer_reliability_score": row["developer_reliability_score"],
            "longitude": row["longitude"],
            "latitude": row["latitude"],
        }
        for key in data:
            res_buildings[idx][key] = row[key]

    return res_buildings


def get_known_developer_inns():
    query = text(
        """
        SELECT DISTINCT developer_inn
        FROM public.new_buildings
        WHERE developer_inn IS NOT NULL AND developer_inn <> ''
        ORDER BY developer_inn
        """
    )

    with engine.connect() as conn:
        return [row[0] for row in conn.execute(query).all()]


def save_developer_rating(inn, score):
    query = text(
        """
        UPDATE public.new_buildings
        SET developer_reliability_score = :score
        WHERE developer_inn = :inn
        """
    )

    with engine.begin() as conn:
        result = conn.execute(query, {"inn": inn, "score": score})

    return result.rowcount


def get_rating_coverage():
    query = text(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(developer_inn) AS with_inn,
            COUNT(developer_reliability_score) AS with_rating
        FROM public.new_buildings
        """
    )

    with engine.connect() as conn:
        row = conn.execute(query).mappings().one()

    return {
        "total": row["total"],
        "with_inn": row["with_inn"],
        "with_rating": row["with_rating"],
        "missing_inn": row["total"] - row["with_inn"],
        "missing_rating": row["with_inn"] - row["with_rating"],
    }







