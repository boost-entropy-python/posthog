import re

from posthog.hogql.database.models import (
    BooleanDatabaseField,
    DateDatabaseField,
    DateTimeDatabaseField,
    IntegerDatabaseField,
    FloatDatabaseField,
    DecimalDatabaseField,
    StringArrayDatabaseField,
    StringDatabaseField,
    StringJSONDatabaseField,
    UnknownDatabaseField,
)

from django.db.models import Q
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from posthog.warehouse.models import DataWarehouseSavedQuery, DataWarehouseTable


def get_view_or_table_by_name(team, name) -> Union["DataWarehouseSavedQuery", "DataWarehouseTable", None]:
    from posthog.warehouse.models import DataWarehouseSavedQuery, DataWarehouseTable

    table_name = name
    if "." in name:
        chain = name.split(".")
        if len(chain) == 2:
            table_name = f"{chain[0]}_{chain[1]}"
        elif len(chain) == 3:
            table_name = f"{chain[1]}_{chain[0]}_{chain[2]}"

    table: DataWarehouseSavedQuery | DataWarehouseTable | None = (
        DataWarehouseTable.objects.filter(Q(deleted__isnull=True) | Q(deleted=False))
        .filter(team=team, name=table_name)
        .first()
    )
    if table is None:
        table = DataWarehouseSavedQuery.objects.exclude(deleted=True).filter(team=team, name=name).first()
    return table


def remove_named_tuples(type):
    """Remove named tuples from query"""
    from posthog.warehouse.models.table import CLICKHOUSE_HOGQL_MAPPING

    tokenified_type = re.split(r"(\W)", type)
    filtered_tokens = []
    i = 0
    while i < len(tokenified_type):
        token = tokenified_type[i]
        # handle tokenization of DateTime types that need to be parsed in a specific way ie) DateTime64(3, 'UTC')
        if token == "DateTime64" or token == "DateTime32":
            filtered_tokens.append(token)
            i += 1
            if i < len(tokenified_type) and tokenified_type[i] == "(":
                filtered_tokens.append(tokenified_type[i])
                i += 1
                while i < len(tokenified_type) and tokenified_type[i] != ")":
                    if tokenified_type[i] == "'":
                        filtered_tokens.append(tokenified_type[i])
                        i += 1
                        while i < len(tokenified_type) and tokenified_type[i] != "'":
                            filtered_tokens.append(tokenified_type[i])
                            i += 1
                        if i < len(tokenified_type):
                            filtered_tokens.append(tokenified_type[i])
                    else:
                        filtered_tokens.append(tokenified_type[i])
                    i += 1
                if i < len(tokenified_type):
                    filtered_tokens.append(tokenified_type[i])
        elif (
            token == "Nullable" or (len(token) == 1 and not token.isalnum()) or token in CLICKHOUSE_HOGQL_MAPPING.keys()
        ):
            filtered_tokens.append(token)
        i += 1
    return "".join(filtered_tokens)


def clean_type(column_type: str) -> str:
    # Replace newline characters followed by empty space
    column_type = re.sub(r"\n\s+", "", column_type)

    if column_type.startswith("Nullable("):
        column_type = column_type.replace("Nullable(", "")[:-1]

    if column_type.startswith("Array("):
        column_type = remove_named_tuples(column_type)

    column_type = re.sub(r"\(.+\)+", "", column_type)

    return column_type


CLICKHOUSE_HOGQL_MAPPING = {
    "UUID": StringDatabaseField,
    "String": StringDatabaseField,
    "Nothing": UnknownDatabaseField,
    "DateTime64": DateTimeDatabaseField,
    "DateTime32": DateTimeDatabaseField,
    "DateTime": DateTimeDatabaseField,
    "Date": DateDatabaseField,
    "Date32": DateDatabaseField,
    "UInt8": IntegerDatabaseField,
    "UInt16": IntegerDatabaseField,
    "UInt32": IntegerDatabaseField,
    "UInt64": IntegerDatabaseField,
    "Float8": FloatDatabaseField,
    "Float16": FloatDatabaseField,
    "Float32": FloatDatabaseField,
    "Float64": FloatDatabaseField,
    "Int8": IntegerDatabaseField,
    "Int16": IntegerDatabaseField,
    "Int32": IntegerDatabaseField,
    "Int64": IntegerDatabaseField,
    "Tuple": StringJSONDatabaseField,
    "Array": StringArrayDatabaseField,
    "Map": StringJSONDatabaseField,
    "Bool": BooleanDatabaseField,
    "Decimal": DecimalDatabaseField,
    "FixedString": StringDatabaseField,
}

STR_TO_HOGQL_MAPPING = {
    "BooleanDatabaseField": BooleanDatabaseField,
    "DateDatabaseField": DateDatabaseField,
    "DateTimeDatabaseField": DateTimeDatabaseField,
    "IntegerDatabaseField": IntegerDatabaseField,
    "DecimalDatabaseField": DecimalDatabaseField,
    "FloatDatabaseField": FloatDatabaseField,
    "StringArrayDatabaseField": StringArrayDatabaseField,
    "StringDatabaseField": StringDatabaseField,
    "StringJSONDatabaseField": StringJSONDatabaseField,
    "UnknownDatabaseField": UnknownDatabaseField,
}
