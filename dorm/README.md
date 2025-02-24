# [D]ummy ORM (DORM)

<em>This library is an in-house product of [DecodedSports.com](https://www.decodedsports.com)</em>

DORM is a Python SQLite database Object-relational Mapper (ORM) that implements the simplest, most lightweight, most naive possible ORM for quick and dirty data wrangling.

# Features

- Incredibly light weight and fast.

- No preconfiguration or table Class mappings required.

- No migrations required.

- Saves you from writing painful SQL queries directly, while still allowing you to dabble in SQL if you want.

- Uses [Method Chaining](https://en.wikipedia.org/wiki/Method_chaining) by design.

- Returns data as a `list of tuple`, `list of dicts`, or `pandas.DataFrame`. The former retain the original SQLite3 generator, where possible.

- Great for simple use cases, e.g. grabbing from SQL and dumping to UI or pandas

# Usage

```python
import dorm

orm = dorm.DORM(':memory:', _table='people')
orm.select('name', 'age', 'country')

results = orm.vals()
print(results)
"""
[
    ('Jeremy', 30, 'UK'),
    ('James', 20, 'UK'),
    ('Emma', 22, 'USA'),
    ('Chris', 31, 'USA'),
    ('Olivia', 40, 'UK'),
    ('Abby', 32, 'USA'),
    ('Joe', 26, 'USA')
]
"""
```

DORM can even post-process `GROUP BY` statements.

```python
orm.select('name', 'age', 'country') \
   .where(dorm.CMP('age', dorm.GT, 25)) \
   .group('country') \
   .order('age')

results= orm.groups()
print(results)
"""
{
    'UK': [
       {'name': 'Jeremy', 'age': 30},
       {'name': 'Olivia', 'age': 40}
    ],
    'USA': [
        {'name': 'Joe', 'age': 26},
        {'name': 'Chris', 'age': 31},
        {'name': 'Abby', 'age': 32}
    ]
}
"""
```

And if you don't want to fully commit to DORM, you can still just use it to generate SQL queries before shpiping them off to another engine.

```python
orm.select('name', 'age', 'country') \
   .where(dorm.CMP('age', dorm.GT, 25)) \
   .group('country') \
   .order('age')


query = orm._build_query()
print(query)
"""
SELECT name, age, country
FROM people
WHERE age > 25
GROUP BY country
ORDER BY age
"""
```

# Why a Dummy ORM

### Cons of Traditional ORMs

- Popular ORMs are heavy

- Normal ORMs are not dummies and require lots of setup to make sure they have every bit of knowledge about the database they relate to, i.e. Python Classes that manually map every column and data type

- Normal ORMs expect tables definitions to not change often

- Normal ORMs expect migrations when any aspect of a database definition changes


### Pros of DORM

- Does not care about the underlying database table definitions (it's a dummy!)

- Does not require preconfigured classes or table mappings

- Does not require migrations

- It is incredibly lightweight! At it's core, it just builds a query string and sends it straight to `cursor.execute()`

- Can get up and running instantly! Seriously, just start querying and dumping data!

- Picks up where pandas and pickle leave off. Meaning when your dataset grows just enough that working entirely in memory starts to become slow, but your use case is still simple enough that you don't want to both setting up a more advanced solution like [Dask](https://www.dask.org/), [Vaex](https://vaex.io/), [DuckDB](https://duckdb.org/docs/clients/python/overview.html), or [Apache Spark](https://spark.apache.org/).

### Cons of DORM

- DORM requires mildly mediocre SQL knowledge


- DORM does not do fancy column/name type checking for you

- DORM does not have fancy built in aggregating functions like AVG, SUM, COUNT to do the work for you. Instead, you simply just tell it exactly what you want when defining your `SELECT` args, e.g. `dorm.select('team', 'AVG(score)')`

- DORM is intended for simple SQL use cases that follow basic [SQLite clause structure](https://www.sqlite.org/lang_select.html). i.e. `SELECT - FROM - WHERE - GROUP BY - ORDER BY - LIMIT`


# Why DecodedSports loves DORM

- Sports data is messy and changes a lot as we iterate on how metrics are defined, create derivative metrics, or ingest new data sources.

- Sports data has LOTS of columns, could be hundreds for a single MLB game - we don't want to manually write mappings for all of these

- We often operate on data in bulk, meaning we don't care about the hundreds of MLB metrics individually, we just want to grab a giant batch of them, run some stats, and dump them to a user interface for exploring - we're happy with the default database types for that and don't need (or want) to configure each individually.

# Compatibility

DORM has only been tested with Python 3's standard library [sqlite3](https://docs.python.org/3/library/sqlite3.html).

# Caveats

As much as we love DORM, you really should be using a professional, full-featured ORM for anything but the most simple use cases.

- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Django ORM](https://docs.djangoproject.com/en/5.1/topics/db/queries/)
- [peewee](https://docs.peewee-orm.com/en/latest/)

Recommend only using DORM for data science and non-production use cases for exploring evolving datasets.

DecodedSports uses Django ORM for our CMS and production database for anything non-sports related.

# License

This project is licensed under the terms of the MIT license.

# Questions?
Please reach out to us via [DecodedSports here](https://www.decodedsports.com/contact).
