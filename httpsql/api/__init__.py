# Copyright (c) 2016 Till Mobile Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import psycopg2
import falcon
import json
import os
import time
import datetime
import settings
import db
import schema
import query_gen

from decimal import Decimal

MAX_SCHEMA_WAIT = 15 #seconds

# TODO Add logging
# TODO Add update by query
# TODO Add delete by query
# TODO Add query syntax for JSONB columns
# TODO Add distinct values endpoint
# TODO Add mass upsert support
# TODO Add support for ARRAY
# TODO Add Geo data types
# TODO Add a POST handler for functions

###################################################################################################
# (De)serialization
###################################################################################################

def error_serializer(req, exception):
    return ("application/json", exception.to_json())

def json_serializer(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, datetime.date):
        return obj.isoformat() 
    elif isinstance(obj, datetime.time):
        return obj.isoformat()                       
    elif isinstance(obj, bool):
        return obj
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, buffer):
        return unicode(obj)
    raise_internal_error("Type %s not serializable: %s" % (str(type(obj)), obj))

def to_json(obj):
    return json.dumps(obj, default=json_serializer, sort_keys=True)

def from_json(obj):
    return json.loads(obj)

###################################################################################################
# Fuzzy int match for pagination
###################################################################################################

def is_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

###################################################################################################
# Wait for the schema to load up before accepting requests
###################################################################################################

def wait_for_schema():
    interval = 0.5
    wait = 0
    while (schema.SCHEMA == None or schema.FUNCTIONS == None) and wait < MAX_SCHEMA_WAIT:
        time.sleep(interval)
        wait += interval

###################################################################################################
# Request exceptions
###################################################################################################

def raise_bad_request(msg):
    raise falcon.HTTPError(falcon.HTTP_400, "Error", msg)

def raise_not_found():
    raise falcon.HTTPError(falcon.HTTP_404, "Error", "Not Found")

def raise_internal_error(msg):
    raise falcon.HTTPError(falcon.HTTP_500, "Error", msg)        

###################################################################################################
# Request guards
###################################################################################################

def check_table(table):
    if table not in schema.SCHEMA:
        raise_not_found()

def check_function(function, args):        
    if function not in schema.FUNCTIONS:
        raise_not_found()
    if len(args) != len(schema.FUNCTIONS[function]["parameters"]):
        raise_bad_request("Incorrect arguments passed")        

def check_pk(table, pk):
    if table not in schema.PKS:
        raise_bad_request("Object doesn't have primary key. Try a query instead.")

def check_pagination(req):
    def get_param(param, req, default=None):
        if param in req.params:
            value = req.params[param]
            if not is_int(value):
                raise_bad_request("Invalid '%s' parameter passed" % param)
            value = int(value)
            if value > 0:
                return value
        return default
    return get_param("limit", req, settings.API_DEFAULT_COLLECTION_ROW_LIMIT), get_param("offset", req)

def check_order_by(table, req):
    if "order_by" in req.params:
        order_by = req.params["order_by"]
        if not isinstance(order_by, list):
            order_by = [order_by]
        return [x for x in order_by if x.replace("-", "") in schema.SCHEMA[table]["columns"]]
    return None

###################################################################################################
# Data manipulation
###################################################################################################

def get_function_rows(conn, function, args, limit=None, offset=None, order=None):
    try:
        with conn.cursor() as c:
            query, _args = query_gen.get_function_query(function, args, limit, offset, order)
            c.execute(query, _args)
            return db.dictfetchall(c)
    except (query_gen.QueryGenError, psycopg2.DataError, psycopg2.IntegrityError), e:
        raise_bad_request(str(e))
    except Exception, e:
        raise_internal_error(str(e))        

def get_table_rows(conn, table, limit=None, offset=None, order=None):
    try:
        with conn.cursor() as c:
            c.execute(query_gen.get_table_rows_query(table, limit, offset))
            return db.dictfetchall(c)
    except (query_gen.QueryGenError, psycopg2.DataError, psycopg2.IntegrityError), e:
        raise_bad_request(str(e))
    except Exception, e:
        raise_internal_error(str(e))        

def get_table_row(conn, table, pk):
    try:
        with conn.cursor() as c:
            c.execute(query_gen.get_table_row_query(schema.PKS, table, pk), [pk])
            rows = db.dictfetchall(c)
            if len(rows) > 0:
                return rows
        return None
    except (query_gen.QueryGenError, psycopg2.DataError, psycopg2.IntegrityError), e:
        raise_bad_request(str(e))
    except Exception, e:
        raise_internal_error(str(e))        

def delete_table_row(conn, table, pk):
    try:
        with conn.cursor() as c:
            c.execute(query_gen.delete_table_row_query(schema.PKS, table, pk), [pk])
    except (query_gen.QueryGenError, psycopg2.DataError, psycopg2.IntegrityError), e:
        raise_bad_request(str(e))
    except Exception, e:
        raise_internal_error(str(e))        

def insert_table_row(conn, table, obj):
    try:
        params = [obj[x] for x in query_gen.typeify(obj, table)]
        with conn.cursor() as c:
            q = query_gen.insert_table_row_query(table, obj)
            c.execute(q, params)
            try:
                rows = db.dictfetchall(c)
                if len(rows) > 0:
                    return rows
                else:
                    return []
            except:
                pass
    except (query_gen.QueryGenError, psycopg2.DataError, psycopg2.IntegrityError), e:
        raise_bad_request(str(e))
    except Exception, e:
        raise_internal_error(str(e))        

def insert_table_rows(conn, table, objs):
    try:
        copy_stmt, insert_buffer = query_gen.insert_table_rows_query(table, objs)
        with conn.cursor() as c:
            c.copy_expert(copy_stmt, insert_buffer)
            return []
    except (query_gen.QueryGenError, psycopg2.DataError, psycopg2.IntegrityError), e:
        raise_bad_request(str(e))
    except Exception, e:
        raise_internal_error(str(e))        

def update_table_row(conn, table, pk, obj):
    try:
        query = query_gen.update_table_row_query(schema.PKS, table, obj)
        params = [obj[x] for x in query_gen.typeify(obj, table)] + [pk]
        with conn.cursor() as c:
            c.execute(query, params)
            try:
                rows = db.dictfetchall(c)
                if len(rows) > 0:
                    return rows            
                else:
                    return []
            except:
                pass
    except (query_gen.QueryGenError, psycopg2.DataError, psycopg2.IntegrityError), e:
        raise_bad_request(str(e))
    except Exception, e:
        raise_internal_error(str(e))

def get_table_query_row_count(conn, table, filters, limit=None, offset=None, order=None):
    try:
        with conn.cursor() as c:
            query, params = query_gen.get_filtered_rows_query(table, filters, limit, offset, order)
            c.execute(query_gen.get_row_count_query(query), params)
            return db.dictfetchall(c)[0]
    except (query_gen.QueryGenError, psycopg2.DataError, psycopg2.IntegrityError), e:
        raise_bad_request(str(e))
    except Exception, e:
        raise_internal_error(str(e))        

def get_table_query_rows(conn, table, filters, limit=None, offset=None, order=None):
    try:
        with conn.cursor() as c:
            query, params = query_gen.get_filtered_rows_query(table, filters, limit, offset, order)
            c.execute(query, params)
            return db.dictfetchall(c)
    except (query_gen.QueryGenError, psycopg2.DataError, psycopg2.IntegrityError), e:
        raise_bad_request(str(e))
    except Exception, e:
        raise_internal_error(str(e))        

###################################################################################################
# API Resources
###################################################################################################

class SchemaResource(object):
    def on_get(self, req, resp):
        wait_for_schema()    
        resp.body = to_json({
            "collection" : schema.SCHEMA,
            "function"   : schema.FUNCTIONS
        })
        resp.status = falcon.HTTP_200

class FunctionSchemaResource(object):
    def on_get(self, req, resp):
        wait_for_schema()    
        resp.body = to_json(schema.FUNCTIONS)
        resp.status = falcon.HTTP_200

class CollectionSchemaResource(object):
    def on_get(self, req, resp):
        wait_for_schema()    
        resp.body = to_json(schema.SCHEMA)
        resp.status = falcon.HTTP_200

class FunctionResource(object):
  def on_get(self, req, resp, object_name):
        wait_for_schema()
        args = {x:req.params[x] 
                for x in req.params 
                if object_name in schema.FUNCTIONS and x in schema.FUNCTIONS[object_name]["parameters"]}
        check_function(object_name, args)
        limit, offset = check_pagination(req)
        with db.conn() as conn:
            order_by = check_order_by(schema.SCHEMA[schema.FUNCTIONS[object_name]["type"]], req)
            resp.body = to_json(get_function_rows(conn, object_name, args, limit, offset, order_by))
            resp.status = falcon.HTTP_200

class CountResource(object):
    def on_get(self, req, resp, object_name):
        wait_for_schema()
        check_table(object_name)
        with db.conn() as conn:
            resp.body = to_json(get_table_query_row_count(conn, object_name, req.params))
            resp.status = falcon.HTTP_200

class MultiResource(object):
    def on_get(self, req, resp, object_name):
        wait_for_schema()
        check_table(object_name)
        limit, offset = check_pagination(req)
        with db.conn() as conn:
            order_by = check_order_by(object_name, req)
            resp.body = to_json(get_table_query_rows(conn, object_name, req.params, limit, offset, order_by))
            resp.status = falcon.HTTP_200    

    def on_put(self, req, resp, object_name):
        wait_for_schema()
        check_table(object_name)
        with db.conn() as conn:
            objs = from_json(req.stream.read())
            if not isinstance(objs, list):
                resp.body = to_json(insert_table_row(conn, object_name, objs))
            else:
                resp.body = to_json(insert_table_rows(conn, object_name, objs))
            resp.status = falcon.HTTP_204

class SingleResource(object):
    def on_get(self, req, resp, object_name, pk):
        wait_for_schema()
        with db.conn() as conn:
            check_table(object_name)
            check_pk(object_name, pk)
            row = get_table_row(conn, object_name, pk)
            if row:
                resp.body = to_json(row)
                resp.status = falcon.HTTP_200
            else:
                raise_not_found()

    def on_post(self, req, resp, object_name, pk):
        wait_for_schema()
        check_table(object_name)
        check_pk(object_name, pk)
        with db.conn() as conn:
            obj = from_json(req.stream.read())
            update_table_row(conn, object_name, pk, obj)
            row = get_table_row(conn, object_name, pk)
            if row:
                resp.body = to_json(row)
                resp.status = falcon.HTTP_200
            else:
                raise_not_found()

    def on_delete(self, req, resp, object_name, pk):
        wait_for_schema()
        check_table(object_name)
        check_pk(object_name, pk)
        with db.conn() as conn:
            delete_table_row(conn, object_name, pk)
            resp.status = falcon.HTTP_204

###################################################################################################
# Initialize the API
###################################################################################################

app = falcon.API()
app.set_error_serializer(error_serializer)
app.add_route('/',                               SchemaResource())
app.add_route('/function',                       FunctionSchemaResource())
app.add_route('/collection',                     CollectionSchemaResource())
app.add_route('/function/{object_name}',         FunctionResource())
app.add_route('/collection/{object_name}',       MultiResource())
app.add_route('/collection/{object_name}/count', CountResource())
app.add_route('/collection/{object_name}/{pk}',  SingleResource())