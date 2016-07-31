# Copyright (c) 2016 Till Mobile Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

DB_DATABASE = os.environ.get("DB_DATABASE", "")
DB_SCHEMA = os.environ.get("DB_SCHEMA", "")
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_HOST = os.environ.get("DB_HOST", "")
DB_PORT = os.environ.get("DB_PORT", "")
DB_CONNECTION_POOL_MIN = os.environ.get("DB_CONNECTION_POOL_MIN", "")
DB_CONNECTION_POOL_MAX = os.environ.get("DB_CONNECTION_POOL_MAX", "")
DB_CONNECTION_TIMEOUT_SECONDS = os.environ.get("DB_CONNECTION_TIMEOUT_SECONDS", 15)
SCHEMA_MAX_WAIT_SECONDS = os.environ.get("SCHEMA_MAX_WAIT_SECONDS", 10)
API_DEFAULT_COLLECTION_ROW_LIMIT = os.environ.get("API_DEFAULT_COLLECTION_ROW_LIMIT", 25)
API_LOG_LEVEL = os.environ.get("API_LOG_LEVEL", "INFO")