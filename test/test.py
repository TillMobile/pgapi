# Copyright (c) 2016 Till Mobile Inc.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest, requests, os, psycopg2, os

DATABASE = os.environ.get("DB_DATABASE", "")
SCHEMA = os.environ.get("DB_SCHEMA", "")
USER = os.environ.get("DB_USER", "")
PASSWORD = os.environ.get("DB_PASSWORD", "")
HOST = os.environ.get("DB_HOST", "")
PORT = os.environ.get("DB_PORT", "")
ROW_LIMIT = os.environ.get("API_DEFAULT_COLLECTION_ROW_LIMIT", 25)

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.conn = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            database=DATABASE
        )
        self.conn.autocommit = True
        self.API_URL = "http://127.0.0.1:8000"
        self.ITEM_DICT = {
            "name"        : "Shoe X",
            "description" : "Awesome",
            "attributes"  : {
                "size"   : "XL",
                "sku"    : "123-456",
                "weight" : 0
            }
        }

        self.TYPE_RECORD = {
            "a" : 1,
            "b" : 1,
            "c" : 1,
            "d" : 1.0,
            "e" : 1.0,
            "f" : 1.0,
            "g" : 1.0,
            "h" : 1,
            "i" : 1,
            "j" : 1,
            "k" : 1.0,
            "l" : "11001100",
            "m" : True,
            "n" : "a",
            "o" : "a",
            "p" : "a",
            "q" : "2004-10-19 10:23:54",
            "r" : "2004-10-19 10:23:54",
            "s" : "2004-10-19 10:23:54",
            "t" : "2004-10-19 10:23:54",       
            "u" : "2004-10-19 10:23:54",
            "v" : {"a": [1,2,3,4,5,6]},
            "w" : {"x" : 123}
        }        

    def tearDown(self):
        try:
            with self.conn.cursor() as c:
                c.execute("delete from item;")
                c.execute("delete from supported_types;")
                c.execute("ALTER SEQUENCE item_id_seq RESTART")
        finally:
            if self.conn:
                self.conn.close()

    def get(self, path, pk=None, qs=None):
        return requests.get("%s/%s/%s%s" % (self.API_URL, path, pk if pk else "", qs if qs else ""))

    def insert(self, path, _dict):
        url = "%s/%s" % (self.API_URL, path)
        return requests.put(url, json=_dict)

    def update(self, path, _id, _dict):
        return requests.post("%s/%s/%s" % (self.API_URL, path, _id), json=_dict)

    def delete(self, path, _id=None):
        return requests.delete("%s/%s/%s" % (self.API_URL, path, _id if _id else ""))

    def assert_item_dicts_equal(self, dict_a, dict_b):
        self.assertEqual(dict_a["name"], dict_b["name"])
        self.assertEqual(dict_a["description"], dict_b["description"])
        self.assertEqual(dict_a["attributes"]["size"], dict_b["attributes"]["size"])
        self.assertEqual(str(dict_a["attributes"]["weight"]), str(dict_b["attributes"]["weight"]))
        self.assertEqual(dict_a["attributes"]["sku"], dict_b["attributes"]["sku"])

    def test_api_get(self):
        """
        Retrieve the collection and function schema
        GET /api
        """

        r = self.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.content) > 0)

    def test_collection_put(self):
        """
        Insert entities into the collection
        PUT /collection/<collection>
        """

        # Single entity
        r = self.insert("collection/item", self.ITEM_DICT)
        self.assertEqual(r.status_code, 204)

        r = self.get("collection/item")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.content) > 0)

        rlist = r.json()

        self.assertTrue(len(rlist) == 1)
        rdict = rlist[0]
        self.assertTrue(rdict["id"], 1)
        self.assertTrue("id" in rdict)
        self.assert_item_dicts_equal(rdict, self.ITEM_DICT)

        # Multiple entities
        r = self.insert("collection/item", [self.ITEM_DICT, self.ITEM_DICT, self.ITEM_DICT])
        self.assertEqual(r.status_code, 204)

        r = self.get("collection/item")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.content) > 0)

        rlist = r.json()
        self.assertTrue(len(rlist) == 4)

    def test_collection_post(self):
        """
        Update a single entity in the collection
        POST /collection/<collection>/<pk>
        """

        r = self.insert("collection/item", self.ITEM_DICT)
        self.assertEqual(r.status_code, 204)
        r = self.get("collection/item/1")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.content) > 0)
        rlist = r.json()
        rdict = rlist[0]
        self.assert_item_dicts_equal(rdict, self.ITEM_DICT)

        rdict["name"] = "Shoe Y"
        rdict["attributes"]["size"] = "XM"
        r = self.update("collection/item", rdict["id"], rdict)
        self.assertTrue(r.status_code, 200)

        r = self.get("collection/item/1")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.content) > 0)
        nlist = r.json()
        ndict = nlist[0]
        self.assert_item_dicts_equal(rdict, ndict)

    def test_collection_get(self):
        """
        Retrieve one of more entities
        GET /collection/<collection>/<pk>
        GET /collection/<collection>?limit=<limit>&offest=<offset>&<query>&order_by=<order_by>
        """

        # Retrieve single collection instance
        r = self.insert("collection/item", self.ITEM_DICT)
        self.assertEqual(r.status_code, 204)
        r = self.get("collection/item/1")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(len(r.content) > 0)
        rdict = r.json()
        self.assert_item_dicts_equal(rdict[0], self.ITEM_DICT)

        # Invalid pk
        r = self.get("collection/item/44")
        self.assertEqual(r.status_code, 404)

        r = self.get("collection/item/asdasd")
        self.assertEqual(r.status_code, 400)

        # Invalid collection
        r = self.get("collection/cars/1")
        self.assertEqual(r.status_code, 404)

        # Retrieve multiple collection instances
        r = self.insert("collection/item", [self.ITEM_DICT, self.ITEM_DICT, self.ITEM_DICT])
        self.assertEqual(r.status_code, 204)
        r = self.get("collection/item")
        rlist = r.json()
        for rdict in rlist:
            self.assert_item_dicts_equal(rdict, self.ITEM_DICT)

        # Limit and offset
        r = self.insert("collection/item", [self.ITEM_DICT, self.ITEM_DICT, self.ITEM_DICT])
        self.assertEqual(r.status_code, 204)
        r = self.get("collection/item", None, "?limit=2&offset=1")
        rlist = r.json()
        self.assertTrue(len(rlist) == 2)
        for rdict in rlist:
            if rdict["id"] == 1:
                self.assertTrue(False)

        # Query
        r = self.get("collection/item", None, "?id__exact=1")
        rlist = r.json()
        self.assertTrue(len(rlist) == 1)
        self.assert_item_dicts_equal(rlist[0], self.ITEM_DICT)

        r = self.get("collection/item", None, "?id__lt=2")
        rlist = r.json()
        self.assertTrue(len(rlist) == 1)
        self.assert_item_dicts_equal(rlist[0], self.ITEM_DICT)

        # Field vs. field comparison
        r = self.get("collection/item", None, "?id__exact=id")
        rlist = r.json()
        self.assertTrue(len(rlist) > 1)
        self.assert_item_dicts_equal(rlist[0], self.ITEM_DICT)

        r = self.get("collection/item", None, "?id__lte=1")
        rlist = r.json()
        self.assertTrue(len(rlist) == 1)
        self.assert_item_dicts_equal(rlist[0], self.ITEM_DICT)

        r = self.get("collection/item", None, "?id__gt=0&id__lt=2")
        rlist = r.json()
        self.assertTrue(len(rlist) == 1)
        self.assert_item_dicts_equal(rlist[0], self.ITEM_DICT)

        # Order by
        r = self.get("collection/item", None, "?order_by=id,name")
        rlist = r.json()
        self.assertTrue(rlist[0]["id"] == 1)

        r = self.get("collection/item", None, "?order_by=-id")
        rlist = r.json()
        self.assertTrue(rlist[0]["id"] != 1)

        # Nested hstore query
        r = self.get("collection/item", None, "?attributes.weight__lt=1")
        rlist = r.json()
        self.assertTrue(len(rlist) > 1)
        self.assert_item_dicts_equal(rlist[0], self.ITEM_DICT)

        # Bogus field
        r = self.get("collection/item", None, "?position__gt=0")
        self.assertTrue(r.status_code == 400)

        # Bogus operator
        r = self.get("collection/item", None, "?id__hmmm=0")
        self.assertTrue(r.status_code == 400)

    def test_count_get(self):
        """
        Reteive the row count for the passed query
        GET /collection/<collection>/count?<query>
        """

        # Retrieve single collection instance
        r = self.insert("collection/item", self.ITEM_DICT)
        self.assertEqual(r.status_code, 204)

        r = self.get("collection/item/count")
        self.assertTrue(r.status_code == 200)
        rdict = r.json()
        self.assertTrue(rdict["count"] == 1)

    def test_collection_delete(self):
        """
        Delete a collection entity
        DELETE /collection/<pk>/
        """

        # Retrieve single collection instance
        r = self.insert("collection/item", self.ITEM_DICT)
        self.assertEqual(r.status_code, 204)

        r = self.delete("collection/item/1")
        self.assertEqual(r.status_code, 204)

        r = self.get("collection/item/count")
        self.assertTrue(r.status_code == 200)
        rdict = r.json()
        self.assertTrue(rdict["count"] == 0)

    def test_function_get(self):
        """
        Call a function that returns an already defined collection type
        GET /api/function/<collection>?<function_params>
        """

        r = self.insert("collection/item", self.ITEM_DICT)
        self.assertEqual(r.status_code, 204)

        r = self.get("function/items_by_size", None, "?t_size=XL")
        self.assertEqual(r.status_code, 200)
        rlist = r.json()
        self.assertEqual(len(rlist), 1)
        rdict = rlist[0]
        self.assert_item_dicts_equal(rdict, self.ITEM_DICT)

        # Bogus function
        r = self.get("function/itemby_size", None, "?t_size=XL")
        self.assertEqual(r.status_code, 404)

        # Bogus parameter
        r = self.get("function/items_by_size", None, "?t_siaaze=XL")
        self.assertEqual(r.status_code, 400)

        # Missing parameter
        r = self.get("function/items_by_size")
        self.assertEqual(r.status_code, 400)

    def test_row_limit(self):
        """
        Make sure the default row limit is respected
        """

        r = self.insert("collection/item", [self.ITEM_DICT for x in range(50)])
        self.assertEqual(r.status_code, 204)
        r = self.get("collection/item")
        rlist = r.json()
        self.assertEqual(int(len(rlist)), int(ROW_LIMIT))

    def test_types(self):
        r = self.insert("collection/supported_types", self.TYPE_RECORD)
        self.assertEqual(r.status_code, 204)
        r = self.get("collection/supported_types")
        self.assertEqual(r.status_code, 200)
        rlist = r.json()
        self.assertEqual(len(rlist), 1)
        rdict = rlist[0]

    def test_types_multiple_inserts(self):
        record2 = self.TYPE_RECORD.copy()
        record2["a"] = 23
        r = self.insert("collection/supported_types", [self.TYPE_RECORD, record2])
        self.assertEqual(r.status_code, 204, r.text)
        r = self.get("collection/supported_types")
        self.assertEqual(r.status_code, 200, r.text)
        rlist = r.json()
        self.assertEqual(len(rlist), 2)

    def test_update_jsonb(self):
        r = self.insert("collection/supported_types", self.TYPE_RECORD)
        self.assertEqual(r.status_code, 204, r.text)
        r = self.get("collection/supported_types")
        self.assertEqual(r.status_code, 200, r.text)
        rlist = r.json()
        self.assertEqual(len(rlist), 1)
        rdict = rlist[0]
        rdict["v"]["a"] = "XXX"
        r = self.update("collection/supported_types", 1, rdict)
        self.assertEqual(r.status_code, 200, r.text)
        rlist = r.json()
        self.assertEqual(rlist[0], rdict)

    def test_jsonb_query(self):
        pass

    def test_hstore_query(self):
        pass

    def test_binary_comparison_query(self):
        pass

if __name__ == '__main__':
    unittest.main()