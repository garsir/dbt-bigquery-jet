import pytest
from dbt.tests.util import relation_from_name
from dbt.tests.adapter.constraints.test_constraints import (
    BaseTableConstraintsColumnsEqual,
    BaseViewConstraintsColumnsEqual,
    BaseConstraintsRuntimeEnforcement
)
from dbt.tests.adapter.constraints.fixtures import (
    my_model_sql,
    my_model_wrong_order_sql,
    my_model_wrong_name_sql,
    my_model_view_wrong_order_sql,
    my_model_view_wrong_name_sql,
    model_schema_yml,
)

_expected_sql_bigquery = """
create or replace table {0} (
    id integer  not null    ,
    color string  ,
    date_day date
)
OPTIONS()
as (
    select
        1 as id,
        'blue' as color,
        cast('2019-01-01' as date) as date_day
);
"""

# Different on BigQuery:
# - does not support a data type named 'text' (TODO handle this via type translation/aliasing!)
# - raises an explicit error, if you try to set a primary key constraint, because it's not enforced
constraints_yml = model_schema_yml.replace("text", "string").replace("primary key", "")


class BigQueryColumnEqualSetup:
    @pytest.fixture
    def string_type(self):
        return "STRING"

    @pytest.fixture
    def int_type(self):
        return "INT64"

    @pytest.fixture
    def data_types(self, int_type, string_type):
        # sql_column_value, schema_data_type, error_data_type
        return [
            ['1', int_type, int_type],
            ["'1'", string_type, string_type],
            ["cast('2019-01-01' as date)", 'date', 'DATE'],
            ["true", 'bool', 'BOOL'],
            ["cast('2013-11-03 00:00:00-07' as TIMESTAMP)", 'timestamp', 'TIMESTAMP'],
            ["['a','b','c']", f'ARRAY<{string_type}>', f'ARRAY<{string_type}>'],
            ["[1,2,3]", f'ARRAY<{int_type}>', f'ARRAY<{int_type}>'],
            ["cast(1 as NUMERIC)", 'numeric', 'NUMERIC'],
            ["""JSON '{"name": "Cooper", "forname": "Alice"}'""", 'json', 'JSON'],
            ['STRUCT("Rudisha" AS name, [23.4, 26.3, 26.4, 26.1] AS laps)', 'STRUCT<name STRING, laps ARRAY<FLOAT64>>', 'STRUCT<name STRING, laps ARRAY<FLOAT64>>']
        ]


class TestBigQueryTableConstraintsColumnsEqual(BigQueryColumnEqualSetup, BaseTableConstraintsColumnsEqual):
    @pytest.fixture(scope="class")
    def models(self):
        return {
            "my_model_wrong_order.sql": my_model_wrong_order_sql,
            "my_model_wrong_name.sql": my_model_wrong_name_sql,
            "constraints_schema.yml": constraints_yml,
        }


class TestBigQueryViewConstraintsColumnsEqual(BigQueryColumnEqualSetup, BaseViewConstraintsColumnsEqual):
    @pytest.fixture(scope="class")
    def models(self):
        return {
            "my_model_wrong_order.sql": my_model_view_wrong_order_sql,
            "my_model_wrong_name.sql": my_model_view_wrong_name_sql,
            "constraints_schema.yml": constraints_yml,
        }


class TestBigQueryConstraintsRuntimeEnforcement(BaseConstraintsRuntimeEnforcement):
    @pytest.fixture(scope="class")
    def models(self):
        return {
            "my_model.sql": my_model_sql,
            "constraints_schema.yml": constraints_yml,
        }

    @pytest.fixture(scope="class")
    def expected_sql(self, project):
        relation = relation_from_name(project.adapter, "my_model")
        return _expected_sql_bigquery.format(relation)

    @pytest.fixture(scope="class")
    def expected_error_messages(self):
        return ["Required field id cannot be null"]
