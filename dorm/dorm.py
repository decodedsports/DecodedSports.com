# Filename: dorm.py
# Author: DecodedSports.com
# License: MIT License
# Dependencies: None, optionally pandas

import datetime
import math
import sqlite3
import typing

try:
    import pandas
except ImportError:
    pass


class DORM:
    def __init__(self, path: str, _table: str = None,
                 parse_dates: typing.Iterable = None):
        self.path = path
        self._conn = None
        self.parse_dates = parse_dates or set()
        if parse_dates:
            self.parse_dates = set(parse_dates)

        # CLAUSES
        # manages state for self._build_query()
        self._table = _table
        self._select = {}
        self._where = {}
        self._group = {}
        self._having = {}
        self._order = {}
        self._limit = None

    def table(self, _table: str) -> typing.Self:
        self._table = _table
        return self

    def reset(self, _table: str = None) -> typing.Self:
        """
        Resets the internal state state of DORM.

        This is especially important when using DORM with a persistent
        connection that will be reused for multiple queries.

        Consider the following:

        >>> orm = DORM()
        >>> result_a = orm.select('age').run()
        >>> result_b = orm.select('name').run()

        'result_a' will only contain the column 'age'.
        However, 'result_b' will contain both the 'age' and 'name' columns
        if orm.reset() was not executed in between both run() calls.
        This is useful sometimes, but othertimes not.

        Args:
            _table: option to change which table DORM will query
                    without having to reinstantiate DORM or call table()
        """
        self._select = {}
        self._where = {}
        self._group = {}
        self._having = {}
        self._order = {}
        self._limit = None
        if _table:
            self._table = _table
        return self

    def open(self) -> typing.Self:
        """
        Opens a global and persistent sqlite3 connection.

        Intended for repeated conn.execute() operations
        without the overhead of opening and closing the connection
        each time.

        Will quietly pass and do nothing if there is already a globaly
        opened connection.
        """
        if not self._conn:
            self._conn = self._open()
        return self

    def close(self) -> typing.Self:
        """
        Closes a globaly opened connection, if there is one.

        Will quietly pass and do nothing if there is not a globaly
        open connection.
        """
        if self._conn:
            self._conn.close()
            self._conn = None
        return self

    def _open(self) -> sqlite3.Connection:
        """
        Sofly opens the sqlite3 connection.
        Meaning it will only open the connection if there is not
        already a globaly opened connection by self.open().

        When this method is used by itself, it is intended for
        temporary one-time use connections. i.e. open-execute-close.
        """
        if self._conn:
            return self._conn

        conn = sqlite3.connect(self.path)
        conn.create_aggregate("stdev", 1, Stdev)
        return conn

    def _close(self, conn: sqlite3.Connection):
        """
        Sofly closes the sqlite3 connection.
        Meaning it will only close the connection if it is not the
        same connection that was globaly opened by self.open().

        Will quietely pass and do nothing if the connection is the same
        as the global one.
        """
        if not self._conn:
            conn.close()

    def create(self, *cols: str) -> sqlite3.Connection:
        self._cols = cols

        cols_str = ', '.join(self._cols)
        query = f'CREATE TABLE {self._table}({cols_str})'

        conn = self._open()
        conn.cursor().execute(query)
        conn.commit()
        self._close(conn)
        return self

    def insert(self, data) -> sqlite3.Connection:
        if isinstance(data[0], dict):
            cols = [':%s' % k for k in data[0].keys()]
        else:
            cols = ['?'] * len(data[0])
        cols_str = ', '.join(cols)

        query = f'INSERT INTO {self._table} VALUES({cols_str})'

        conn = self._open()
        conn.cursor().executemany(query, data)
        conn.commit()
        self._close(conn)
        return self

    def select(self, *cols: str) -> sqlite3.Connection:
        for col in cols:
            self._select[col] = 1

        return self

    def deselect(self, *cols: str) -> sqlite3.Connection:
        cols = cols or self._select

        for col in cols:
            self._select.pop(col, None)

        return self

    def where(self, *cols: str) -> sqlite3.Connection:
        for col in cols:
            self._where[str(col)] = 1

        return self

    def group(self, *cols: str) -> sqlite3.Connection:
        for col in cols:
            self._group[col] = 1

        return self

    def degroup(self, *cols: str) -> sqlite3.Connection:
        cols = cols or self._group

        for col in cols:
            self._group.pop(col, None)

        return self

    def having(self, *cols: str) -> sqlite3.Connection:
        for col in cols:
            self._having[str(col)] = 1

        return self

    def order(self, *cols: str | typing.Tuple[str, str]) -> sqlite3.Connection:
        """
        Args:
            cols: if a Tuple, then it must be of form [column_name, direction],
                  e.g., [('age', 'DESC'), ('name', 'ASC')]
        """
        for col in cols:
            if isinstance(col, str):
                c, direction = col, 'ASC'
            else:
                c, direction = col

            self._order[c] = direction

        return self

    def deorder(self, cols: str = None) -> sqlite3.Connection:
        cols = cols or self._order

        for col in cols:
            self._order.pop(col, None)

        return self

    def limit(self, n: int) -> sqlite3.Connection:
        self._limit = n
        return self

    def delimit(self) -> sqlite3.Connection:
        self._limit = None
        return self

    def _build_query(self) -> str:
        # http://sqlite.org/lang_select.html
        q = ''

        # SElECT
        select = self._select or ['*']
        select_str = ', '.join(select)
        q += f'SELECT {select_str} '

        # FROM
        q += f'FROM {self._table}'

        # WHERE
        if self._where:
            where_str = ' AND '.join(self._where)
            q += f' WHERE {where_str}'

        # GROUP BY
        if self._group:
            order_str = ', '.join(self._group)
            q += f' GROUP BY {order_str}'

        # HAVING
        if self._having:
            having_str = ' AND '.join(self._having)
            q += f' HAVING {having_str}'

        # ORDER BY
        if self._order:
            order_str = ', '.join('%s %s' % (col, d)
                                  for col, d in self._order.items())
            q += f' ORDER BY {order_str}'

        # LIMIT
        if self._limit:
            q += f' LIMIT {self._limit}'

        return q

    def info(self) -> typing.List[typing.Tuple]:
        """
        Quick reference function to view the table definition.
        Primarily for checking column names and types.

        https://www.sqlite.org/pragma.html

        Returns:
            list of tuple
        """
        return self.run(query=f'PRAGMA table_info({self._table})').vals()

    def pandas(self, query: str = None) -> 'pandas.DataFrame':
        """
        Like self.run() but specifically for pandas without duplicating
        any other SQL overhead that self.run() performs.

        Returns:
            pandas.DataFrame
        """
        query = query or self._build_query()
        conn = self._open()
        result = pandas.read_sql(query, conn, parse_dates=self.parse_dates)
        self._close(conn)
        return result

    def first(self, *args, **kwargs):
        """Shorthand method equivalent to run().first()"""
        return self.run(*args, **kwargs).first()

    def vals(self, *args, **kwargs):
        """Shorthand method equivalent to run().vals()"""
        return self.run(*args, **kwargs).vals()

    def dicts(self, *args, **kwargs):
        """Shorthand method equivalent to run().dicts()"""
        return self.run(*args, **kwargs).dicts()

    def groups(self, *args, **kwargs):
        """Shorthand method equivalent to run().groups()"""
        return self.run(*args, **kwargs).groups()

    def run(self, immediate: bool = None, query: str = None) -> 'Result':
        """
        Runs query, but does not return the sql results itself.

        The raw SQL result is wrapped in a Result class for helper functions.

        Returns:
            Result
        """
        query = query or self._build_query()
        conn = self._open()
        pending_result = conn.cursor().execute(query)
        result = Result(self, pending_result, immediate, self.parse_dates)
        self._close(conn)
        return result


class Result:
    def __init__(self, orm: DORM, result: sqlite3.Cursor | typing.List,
                 immediate: bool = None, parse_dates: typing.List = None):
        """
        Wrapper class around a sqlite3.Cursor or the results
        of said Cursor.execute().fetchall().

        Args:
            orm: the original DORM instance that generated the query and result
                 this is used to check the current connection state and
                 determine what type of result we have
        """
        self.orm = orm
        self.result = result
        self._result = result
        self.parse_dates = parse_dates or set()
        if parse_dates:
            self.parse_dates = set(parse_dates)
        self._fmt = None
        self._setup(immediate)

    def _setup(self, immediate: bool):
        if immediate is not False and (not self.orm._conn or immediate):
            self.result = self.result.fetchall()

    def first(self):
        """
        Fetcher method: Returns a singular value.

        Helpful for queries like below without having
        to do any post-processing to grab result[0][0]

        without first():
        >>> orm = DORM()
        >>> result = orm.select('AVG(age)').run().vals()
        >>> avg_age = result[0][0]

        with first():
        >>> orm = DORM()
        >>> avg_age = orm.select('AVG(age)').run().first()
        """
        for item in self:
            return item[0]
        return None

    def vals(self) -> typing.List[typing.Tuple]:
        """
        Fetcher method: Returns a list of tuples

        This is the equivalent of sqlite3.Cursor().fetchall()
        """
        return list(self)

    def dicts(self) -> typing.List[typing.Dict]:
        """
        Fetcher method: Returns a list of dicts

        See self._to_dict()
        """
        self._fmt = 'dict'
        if not self.orm._select or '*' in self.orm._select:
            found_cols = ', '.join(self.orm._select)
            raise ValueError('select must be actual columns, '
                             f'not ({found_cols})')
        return list(self)

    def groups(self):
        """
        Fetcher method: Returns a dict of dicts

        See self._to_group()
        """
        self._fmt = 'group'
        return dict(list(self))

    def _to_dict(self, item):
        """
        This takes a singular item from sqlite3.Cursor().fetchall()
        and then postprocesses the tuple into dict by introspecting
        the column names from the original DORM._select state.
        """
        item_dict = {}
        for i, k in enumerate(self.orm._select):
            val = item[i]
            if k in self.parse_dates:
                val = datetime.datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
            item_dict[k] = val
        return item_dict

    def _to_group(self, item):
        """
        This takes a singular item from self._to_dict()
        then introspects the original GROUP BY column name from DORM._group
        then extracts said column to form a (key, value) pair.
        """
        item_dict = self._to_dict(item)
        key = tuple(item_dict[groupk] for groupk in self.orm._group)
        if len(self.orm._group) == 1:
            key = key[0]
        (item_dict.pop(groupk) for groupk in self.orm._group)
        return (key, item_dict)

    def __iter__(self):
        """
        Instantiates Result as an iterable

        Passes quietely and does nothing is self.result is already
        an iterable from the original sqlite3.Cursor().execute() call.
        """
        if isinstance(self.result, list):
            self._result = iter(self.result)
        return self

    def __next__(self):
        item = next(self._result)
        if self._fmt == 'dict':
            return self._to_dict(item)
        elif self._fmt == 'group':
            return self._to_group(item)
        else:
            return item


# AGGREGATORS
# https://www.sqlite.org/lang_corefunc.html


class Stdev:
    # https://stackoverflow.com/questions/2298339/standard-deviation-for-sqlite

    def __init__(self):
        self.M = 0.0
        self.S = 0.0
        self.k = 1

    def step(self, value):
        if value is None:
            return
        tM = self.M
        self.M += (value - tM) / self.k
        self.S += (value - tM) * (value - self.M)
        self.k += 1

    def finalize(self):
        if self.k < 3:
            return None
        return math.sqrt(self.S / (self.k-2))


# COMPARISONS

# Helper comparisons, not limited by these though
LT = '<'
GT = '>'
LTE = '<='
GTE = '>='
EQ = '='
IN = 'in'


class CMP:
    def __init__(self, lhs: str, cmp: str, rhs: str):
        """
        Wrapper class to construct simple comparisons.

        Args:
            lhs: left hand side
            cmp: comparison, can use any of the above helpers
                or any that are defined by SQLite spec.
            rhs: right hand side
        """
        self.lhs = lhs
        self.cmp = cmp
        self.rhs = rhs

    def __hash__(self):
        return hash(self.__str__())

    def __str__(self):
        rhs = self.rhs
        if isinstance(self.rhs, str):
            rhs = f'"{self.rhs}"'
        elif isinstance(self.rhs, datetime.datetime):
            rhs = self.rhs.strftime('%Y-%m-%d %H:%M:%S')
            rhs = f'"{rhs}"'
        elif isinstance(self.rhs, typing.Iterable):
            rhs = ", ".join('"%s"' % s if isinstance(s, str) else str(s)
                            for s in rhs)
            rhs = f'({rhs})'

        return f'{self.lhs} {self.cmp} {rhs}'


# Simple wrapper functions to help format complex comparison queries
# Example:
# >>> statement = (
# >>>     OR(
# >>>         AND(
# >>>             CMP('age', GTE, 25),
# >>>             CMP('age', LTE, 40)
# >>>         ),
# >>>         CMP('age', EQ, 60)
# >>>     )
# >>> )
# '((age >= 25 AND age <= 40) OR age = 60)'

def AND(*items): return f'({" AND ".join(str(i) for i in items)})'


def OR(*items): return f'({" OR ".join(str(i) for i in items)})'
