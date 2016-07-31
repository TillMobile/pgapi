# Copyright (c) 2016 Till Mobile Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import collections
import settings
import db
import log
import query_gen

SCHEMA    = None
FUNCTIONS = None
PKS       = None

def get_schema(conn):
    functions = collections.OrderedDict()
    schema = collections.OrderedDict()    
    pks = {}

    with conn.cursor() as c:
        c.execute("""
        select
        table_name,
        column_name,
        case when data_type = 'USER-DEFINED'
        then udt_name else data_type
        end as data_type,
        (
            select true
            from pg_index i
            join pg_attribute a
            on a.attrelid = i.indrelid and a.attnum = any(i.indkey)
            where i.indrelid = x.table_name::regclass
            and a.attname = x.column_name
            and i.indisprimary
            limit 1
        )
        as is_primary_key,
        (
            select ('{' || string_agg(
                case
                    when privilege_type = 'SELECT' then 'GET'
                    when privilege_type = 'UPDATE' then 'POST'
                    when privilege_type = 'INSERT' then 'PUT'
                    when privilege_type = 'DELETE' then 'DELETE'
                    else null
                end, ',') || '}')::text[]
            from information_schema.role_table_grants 
            where grantee = %s
            and table_name = x.table_name
            limit 1
        ) as methods,
        obj_description(x.table_name::regclass, 'pg_class') as table_comments
        from information_schema.columns x
        where table_catalog = %s
        and table_schema= %s
        and exists 
        (
            select 1
            from information_schema.role_table_grants 
            where grantee = %s
            and table_name = x.table_name
            and privilege_type = 'SELECT'
        )
        order by table_name
        """, (settings.DB_USER, settings.DB_DATABASE, settings.DB_SCHEMA, settings.DB_USER))

        for r in c:
            obj       = r[0]
            column    = r[1]
            data_type = r[2]
            is_pk     = r[3]
            methods   = r[4]
            comments  = r[5]

            if obj not in schema:
                schema[obj] = {
                    "columns" : {},
                    "methods" : methods,
                    "comments" : comments,
                    "endpoint" : "/collection/%s/" % obj,
                    "operators" : {x : query_gen.QUERY_OPERATORS[x][0] for x in query_gen.QUERY_OPERATORS}
                }

            schema[obj]["columns"][column] = data_type

            if is_pk:
                pks[obj] = column

        c.execute("""
        select
        routines.routine_name,
        case when routines.data_type = 'USER-DEFINED'
        then routines.type_udt_name
        else routines.data_type
        end as routine_data_type,
        parameters.parameter_name,
        case when parameters.data_type = 'USER-DEFINED'
        then parameters.udt_name
        else parameters.data_type
        end as parameter_data_type,
        (
            SELECT d.description
            FROM pg_proc p
            INNER JOIN pg_namespace n ON n.oid = p.pronamespace
            LEFT JOIN pg_description As d ON (d.objoid = p.oid )
            WHERE  p.proname = routines.routine_name
            limit 1
        ) as routine_comments
        from information_schema.routines
        full outer join information_schema.parameters
        on routines.specific_name = parameters.specific_name
        where routines.specific_schema = %s
        and exists (
            select 1
            from information_schema.role_routine_grants
            where grantee = %s
            and routine_name = routines.routine_name
            and privilege_type = 'EXECUTE'
        )
        order by routines.routine_name, parameters.ordinal_position;
        """, [settings.DB_SCHEMA, settings.DB_USER])

        for r in c:
            routine_name, routine_data_type, parameter_name, parameter_data_type, routine_comments = r
            if routine_name in functions:
                routine = functions[routine_name]
            else:
                if routine_data_type not in schema:
                    continue

                routine = {
                    "comments" : routine_comments,
                    "endpoint" : "/function/%s/" % routine_name,
                    "type" : routine_data_type,
                    "parameters" : collections.OrderedDict(),
                    "methods" : ["GET", "POST"]
                }

            if parameter_name:
                routine["parameters"][parameter_name] = parameter_data_type
            functions[routine_name] = routine

    return schema, functions, pks

if db.DB_ONLINE:
    log.debug("Start retrieve schema")
    with db.conn() as conn:
        SCHEMA, FUNCTIONS, PKS = get_schema(conn)
        log.debug("Finish retrieve schema")
