# Copyright (c) 2016 Till Mobile Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import schema
import cStringIO
import json

JSON_TYPE = "jsonb"
HSTORE_TYPE = "hstore"

QUERY_OPERATORS = {
    "lt"       : ("Less than",                "%s < %s"),
    "lte"      : ("Less than or equal to",    "%s <= %s"),
    "gt"       : ("Greater than",             "%s > %s"),
    "gte"      : ("Greater than or equal to", "%s >= %s"),
    "not"      : ("Not equal to",             "%s::text <> %s::text"),
    "exact"    : ("Equal to",                 "%s::text = %s::text"),
    "contains" : ("Contains i.e. like",       "%s::text like %s::text"),
    "match"    : ("Regex match",              "%s::text ~ %s::text")
}

class QueryGenError(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

def typeify(_dict, table):
    columns = schema.SCHEMA[table]["columns"]
    for key in _dict:
        ctype = columns[key]
        val = _dict[key]
        if ctype == JSON_TYPE and (isinstance(val, dict) or isinstance(val, list)):
            _dict[key] = json.dumps(val)
        elif ctype == HSTORE_TYPE and isinstance(val, dict):
            for ikey in _dict[key]:
                _dict[key][ikey] = str(_dict[key][ikey])
    return _dict

def get_order_by(table, columns):
    ordering = []
    for column in columns:
        ordering.append("%s %s" % (
            column.replace("-", ""), "desc" if column.find("-") == 0 else "asc"
        ))
    return "order by %s" % ",".join(ordering)

def get_row_count_query(base_query):
    return "select count(*) as \"count\" from (%s) count_base" % base_query

def get_filtered_rows_query(table, filters, limit=None, offset=None, order=None):
    operator_map = {x : QUERY_OPERATORS[x][1] for x in QUERY_OPERATORS}
    columns = schema.SCHEMA[table]["columns"]

    blocks = []
    params = []
    for f in filters:
        chunks = f.split("__")
        if len(chunks) != 2:
            continue
        column = chunks[0]
        # Don't allow comparisons to map parents
        if column in columns and  \
           columns[column] == "map":
            continue        
        operator = chunks[1]
        # Must be a valid operator
        if operator not in operator_map:
            raise QueryGenError("Bad operator for filter. Valid operators are: %s" %  ", ".join(operator_map.keys()))
        # Dot syntax for drilling into hstore columns with operators
        is_map_ref = column.find(".") >= 0
        if is_map_ref:
            column_chunks = column.split(".")
            column_ref = "%s->'%s'" % (column_chunks[0], column_chunks[1])
            column = column_chunks[0]
        else:
            column_ref = column
        # Must be a column that exists in the schema
        if column not in columns:
            raise QueryGenError("Invalid field. Valid fields are: %s" % ", ".join(columns.keys()))
        # No dot syntax for non map type's columns
        if columns[column] != "map" and is_map_ref:
            continue
        val = filters[f]
        val_is_column = val in columns
        if not val_is_column:
            params.append("%%%s%%" % val if operator == "contains" else val)
        # Contains on another column is not allowed (yet)
        if val_is_column and operator == "contains":
            continue
        blocks.append(operator_map[operator] % (
            column_ref, 
            "%s"
            if not val_is_column else val
        ))

    return "select * from %s %s %s %s %s %s" % (
        table,
        "where" if len(blocks) > 0 else "",
        " and ".join(blocks),
        get_order_by(table, order) if order else "",
        ("limit %s" % limit) if limit else "",
        ("offset %s" % offset) if offset else ""
    ), params
            
def get_function_query(function, args=[], limit=None, offset=None, order=None):
    return "select * from %s(%s) %s %s %s" % (
        function, 
        ",".join(["%s := %%s" % arg for arg in args]),
        get_order_by(table, order) if order else "",
        ("limit %s" % limit) if limit else "",
        ("offset %s" % offset) if offset else ""
    ), [args[arg] for arg in args]

def get_table_rows_query(table, limit=None, offset=None, order=None):
    return "select * from %s %s %s" % (
        table,
        get_order_by(table, order) if order else "",
        ("limit %s" % limit) if limit else "",
        ("offset %s" % offset) if offset else ""
    )

def get_table_row_query(pk_lookup, table, pk):
    return "select * from %s where %s = %%s " % (table, pk_lookup[table])

def delete_table_row_query(pk_lookup, table, pk):
    return "delete from %s where %s = %%s " % (table, pk_lookup[table])

def insert_table_row_query(table, _dict):
    values = ",".join(["%s" for x in _dict])
    columns = ",".join(["%s" % x for x in _dict])
    if table in schema.PKS:
        returning = "returning %s" % schema.PKS[table]
    else:
        returning = ""
    return "insert into %s (%s) values(%s) %s" % (table, columns, values, returning)

def insert_table_rows_query(table, _list):
    _dict = _list[0]
    _dict_len = len(_dict)
    columns = ",".join(["%s" % x for x in _dict])
    pg_copy_separator = "~"
    pg_copy_csv_quote = "`"
    pg_copy_lb = "\n"

    def copy_escape(val):
      return str(val).replace(pg_copy_separator, "").replace(pg_copy_csv_quote, "").replace(pg_copy_lb, "") 

    def normalize_value(val, ctype):
        if ctype == HSTORE_TYPE and isinstance(val, dict):
            hstore_buff = []
            for key in val:
                hstore_buff.append('"%s"=>"%s"' % (key, copy_escape(val[key]).replace('"',"")))
            return ",".join(hstore_buff)
        elif ctype == JSON_TYPE and isinstance(val, dict) or isinstance(val, list):
            return json.dumps(val)
        else:
            return copy_escape(val)

    records_to_insert_buffer = cStringIO.StringIO()
    for _dict in _list:
        if len(_dict) != _dict_len:
            raise QueryGenError("Found jagged JSON when importing multiple rows")
        row = pg_copy_separator.join(
            [normalize_value(_dict[x], schema.SCHEMA[table]["columns"][x]) for x in _dict]
        ) + "\n"

        records_to_insert_buffer.write(row)

    copy_stmt = "COPY %s(%s) FROM STDIN WITH DELIMITER '%s' CSV QUOTE '%s'" % (
        table,
        columns,
        pg_copy_separator,
        pg_copy_csv_quote
    )

    records_to_insert_buffer.seek(0)
    return copy_stmt, records_to_insert_buffer

def update_table_row_query(pk_lookup, table, _dict):
    sets = ",".join(["%s = %%s" % x for x in _dict])
    return "update %s set %s where %s = %%s returning %s" % (table, sets, pk_lookup[table], pk_lookup[table])