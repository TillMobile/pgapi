# Copyright (c) 2016 Till Mobile Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import settings
import psycopg2
import psycopg2.pool
import psycopg2.extras
import log

DB_ONLINE = False
DB_POOL = None

try:
    DB_POOL = psycopg2.pool.SimpleConnectionPool(
        settings.DB_CONNECTION_POOL_MIN,
        settings.DB_CONNECTION_POOL_MAX,
        database=settings.DB_DATABASE,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        connect_timeout=settings.DB_CONNECTION_TIMEOUT_SECONDS
    )
    DB_ONLINE = True
    log.info("Connected to DB")
except psycopg2.OperationalError, e:
    log.error("Could not connect to DB: %s" % str(e))

def get_conn(autocommit=True):
    conn = DB_POOL.getconn()
    conn.autocommit = autocommit
    try:
        psycopg2.extras.register_hstore(conn)
    except:
        pass
    return conn

def release_conn(conn):
    if conn:
        DB_POOL.putconn(conn)

def dictfetchall(c):
    rows = []
    if c:
        if c.rowcount > 0:
            if c.description:
                cols = [desc[0] for desc in c.description]
                len_cols = len(cols)
            for r in c:
                row = {}
                for x in range(len_cols):
                    row[cols[x]] = r[x]
                rows.append(row)
    return rows

class conn:
    def __enter__(self):
        self.conn = get_conn()
        return self.conn
    def __exit__(self, type, value, traceback):
        release_conn(self.conn)
