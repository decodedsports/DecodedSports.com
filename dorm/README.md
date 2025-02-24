# [D]ummy ORM (DORM)

<em>This library is an in-house product of [DecodedSports.com](https://www.decodedsports.com)</em>

DORM is a Python SQLite database Object-relational Mapper (ORM) that implements the simplest, most lightweight, most naive possible ORM.

# Features

- Incredibly light weight and fast.

- No preconfiguration or table Class mappings required.

- No migrations required.

- Saves you from writing painful SQL queries directly, while still allowing you to dabble in SQL if you want.

- Uses [Method Chaining](https://en.wikipedia.org/wiki/Method_chaining) by design.

- Returns data as a `list of tuple`, `list of dicts`, or `pandas.DataFrame`. The former retain the original SQLite3 generator, where possible.



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

- Dorm does not have fancy built in aggregating functions like AVG, SUM, COUNT to do the work for you. So you simply just tell it exactly what you want when defining your `SELECT` args, e.g. `dorm.select('team', 'AVG(score)')`

- DORM is intended for simple SQL use cases that follow the basic [SQLite clause structure](https://www.sqlite.org/lang_select.html). i.e. `SELECT - FROM - WHERE - GROUP BY - ORDER BY - LIMIT`

# Why DecodedSports.com loves DORM

- Sports data is messy and changes a lot as we iterate on how metrics are defined, create derivative metrics, or ingest new data sources.
- Sports data has LOTS of columns, could be hundreds for a single MLB game - we don't want to manually write mappings for all of these
- We often operate on data in bulk, meaning we don't care about the hundreds of MLB metrics individually, we just want to grab a giant batch of them, run some stats, and dump them to a user interface for exploring - we're happy with the default database types for that and don't need to configure each individually.

# Compatibility

DORM has only been tested with Python 3's standard library [sqlite3](https://docs.python.org/3/library/sqlite3.html).

# Caveats

As much as we love DORM, you really should be using a professional, full-featured ORM.

- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Django ORM](https://docs.djangoproject.com/en/5.1/topics/db/queries/)
- [peewee](https://docs.peewee-orm.com/en/latest/)

Recommend only using DORM for data science and non-production use cases for exploring evolving datasets.

# License

This project is licensed under the terms of the MIT license.

# Questions?
Please reach out to us via [DecodedSports here](https://www.decodedsports.com/contact).
