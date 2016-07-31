# HTTPSQL

PostgreSQL DB to RESTful API in seconds flat

## Quickstart

Create your `.env` file with a few variables:
- `DB_DATABASE`
- `DB_SCHEMA`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `DB_CONNECTION_POOL_MIN`
- `DB_CONNECTION_POOL_MAX`
- `API_COLLECTION_ROW_LIMIT` (Optional. Default `25`)
- `API_LOG_LEVEL` (Optional. Default `INFO`)

Create and source a fresh environment:
- `virtualenv venv`
- `source venv/bin/activate`

Install:
- `pip install https://github.com/TillMobile/httpsql/zipball/master/`

Serve via gunicorn or your favorite WSGI server:
- `pip install gunicorn`
- `gunicorn httpsql.api:app`
- http://127.0.0.1:8000/

## DB Support 

PostgreSQL >= 9.4 supported.

Types:
* smallint
* integer
* bigint  
* decimal  
* numeric  
* real  
* double precision  
* smallserial  
* serial  
* bigserial  
* money  
* bytea  
* boolean  
* varchar  
* char  
* text  
* timestamp without time zone  
* timestamp with time zone  
* date  
* time without time zone  
* time with time zone  
* jsonb  
* hstore  

**Not** supported:
* ARRAY

## Usage via HTTP(S)

### Schema
Retrieve the list of available collections and functions. Each collection lists its fields w/data-type and query operators Each exposed function lists it's return type and parameters. Both collections and functions list available methods (enforced via DB grants for Insert/Select/Delete/Execute) and any comments for the object set in the DB.

GET `/`

```
{
  collection: {
    item: {
      comments: null,
      endpoint: "/collection/item/",
      methods: ["PUT", "GET", "POST", "DELETE"],
      columns: {
        attributes: "hstore",
        description: "character varying",
        id: "integer",
        name: "character varying"
      },
      operators: {
        contains: "Contains i.e. like",
        exact: "Equal to",
        gt: "Greater than",
        gte: "Greater than or equal to",
        lt: "Less than",
        lte: "Less than or equal to",
        match: "Regex match",
        not: "Not equal to"
      }
    }
  },
  function: {
    items_by_size: {
      type: "item",
      comments: null,
      endpoint: "/function/items_by_size/",
      methods: ["GET", "POST"],
      parameters: {
        t_size: "character varying"
      }
    }
  }
}
```

### Insert
Insert records that conform to the defined schema.

PUT `/collection/{collection}/`

Single record body JSON
```
{
  "name" : "Shoe X",
  "description" : "Awesome shoe",
  "attributes" : {
    "weight" : 0,
    "size" : "XL"
  }
}
```

Multiple record body JSON
```
[{
  "name" : "Shoe X",
  "description" : "Awesome shoe",
  "attributes" : {
    "weight" : 0,
    "size" : "XL"
  }
}]
```

### Update
Update an existing record.

POST `/collection/{collection}/{pk}`

Single record body JSON
```
{
  "id" : 1, // optional
  "name" : "Shoe X",
  "description" : "Awesome shoe",
  "attributes" : {
    "weight" : 0,
    "size" : "XL"
  }
}
```

### Delete
Delete an existing record.

DELETE `/collection/{collection}/{pk}`

### Retrieve by Primary Key
Retrieve a record from a collection by primary key.

GET `/collection/{collection}/{pk}`

Response JSON
```
{
  "id" : 1,
  "name" : "Shoe X",
  "description" : "Awesome shoe",
  "attributes" : {
    "weight" : 0,
    "size" : "XL"
  }
}

```

### Retrieve by Query
Retrieve a list of records by query.

GET `/collection/{collection}/?{query}&order_by={order_by}&offset={offset}&limit={limit}`

Response JSON
```
[{
  "id" : 1,
  "name" : "Shoe X",
  "description" : "Awesome shoe",
  "attributes" : {
    "weight" : 0,
    "size" : "XL"
  }
}]
```

Query examples:
- `name__exact=Shoe X`
- `attributes.weight__lte=5`
- `description__exact=name`

Order by examples:
- `id` order by id ascending
- `-id` order by id descending

Offset example:
- `1`

Limit example:
- `20`


### Row Count 
Retrieve the row count for the passed collection.

GET `/collection/{collection}/count?{query}`

Response JSON
```
{
  "count" : 1
}
```

### Retrieve by Function
Retrieve records by calling a function. Note: the parameters passed must match the function's schema. To function properly the return type of the function must match an a collection defined in the schema.  


GET `/function/{function}/?{parameters}`

Response JSON
```
[{
  "id" : 1,
  "name" : "Shoe X",
  "description" : "Awesome shoe",
  "attributes" : {
    "weight" : 0,
    "size" : "XL"
  }
}]
```

## Usage via embedded client

```
from httpsql import client

# Make sure to set the HTTP_ENDPOINT env varible
# e.g. export HTTP_ENDPOINT=http://localhost:8000

# Retrieve filtered records
client.collection.table_or_view.filter(name__exact="Awesome")

# Retrieve count of filtered records
client.collection.table_or_view.count(id__gte=52)

# Paginate filtered records
client.collection.table_or_view.filter(limit=25, offset=25)

# Order filtered records
client.collection.table_or_view.filter(order_by="-id,name")

# Retrieve a single record by PK
client.collection.table_or_view.get(1)

# Insert record(s)
client.collection.table_or_view.insert([{
  "name" : "Nice" 
}])

# Update record
client.collection.table_or_view.update(1, {
  "name" : "Dang"
})

# Describe collection
client.collection.table_or_view.describe()

# Call a function
client.function.func_name.call(param1=1, param2="asd")

...

```


