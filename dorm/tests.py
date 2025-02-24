import unittest

import dorm


# source: imdb.com
DATA = [
    # Marvel
    ('Iron Man', 2008, 7.9, 'Marvel'),
    ('The Incredible Hulk', 2008, 6.6, 'Marvel'),
    ('Thor', 2011, 7, 'Marvel'),
    ('Guardians of the Galaxy', 2014, 8, 'Marvel'),
    ('Captain America: Civil War', 2016, 7.8, 'Marvel'),
    ('Doctor Strange', 2016, 7.5, 'Marvel'),
    ('Deadpool', 2016, 8, 'Marvel'),
    ('Deadpool 2', 2018, 7.6, 'Marvel'),
    ('Venom', 2018, 6.6, 'Marvel'),
    ('Guardians of the Galaxy Vol. 3', 2023, 7.9, 'Marvel'),
    # DC
    ('Suicide Squad', 2016, 5.9, 'DC'),
    ('Justice League', 2017, 6, 'DC'),
    ('Wonder Woman', 2017, 7.3, 'DC'),
    ('Aquaman', 2018, 6.8, 'DC'),
    ('The Batman', 2022, 7.8, 'DC'),
    ('Blue Beetle', 2023, 5.9, 'DC'),
    ('The Flash', 2023, 6.6, 'DC'),
    ('Joker: Folie a Deuz', 2024, 5.2, 'DC'),
]


class Key:
    title = 0
    year = 1
    score = 2
    franchise = 3


class TestDORM(unittest.TestCase):
    def setUp(self):
        orm = dorm.DORM(':memory:', 'movie')
        orm.open()
        orm.create('title', 'year', 'score', 'franchise')
        orm.insert(DATA)
        self.orm = orm

    def tearDown(self):
        return self.orm.close()

    def get_orm(self) -> dorm.DORM:
        return self.orm.reset()

    def test_query_builder(self):
        orm = self.get_orm()
        orm.select('year', 'title') \
           .where(
               dorm.OR(
                    dorm.AND(
                        dorm.CMP('year', dorm.GTE, 2011),
                        dorm.CMP('year', dorm.LTE, 2017)
                    ),
                    dorm.CMP('year', dorm.EQ, 2023)
               )
            ) \
           .order('title')
        result = orm._build_query()
        expected = (
            'SELECT year, title FROM movie '
            'WHERE ((year >= 2011 AND year <= 2017) OR year = 2023) '
            'ORDER BY title ASC'
        )
        self.assertEqual(result, expected)

    def test_first(self):
        orm = self.get_orm()
        orm.select('AVG(score)', 'title') \
           .where(dorm.CMP('year', dorm.GTE, 2023)) \

        result = orm.first()
        expected = [d for d in DATA if d[Key.year] >= 2023]
        expected = sum(d[Key.score] for d in expected) / len(expected)
        self.assertAlmostEqual(result, expected)

    def test_vals(self):
        orm = self.get_orm()
        orm.select('*') \
           .where(dorm.CMP('year', dorm.GTE, 2023)) \
           .order(('year', 'DESC'))

        result = orm.vals()
        expected = [d for d in DATA if d[Key.year] >= 2023]
        expected = sorted(expected, key=lambda i: i[Key.year], reverse=True)
        self.assertEqual(len(result), len(expected))
        self.assertEqual(result[0], expected[0])

    def test_dicts(self):
        orm = self.get_orm()
        orm.select('year', 'title') \
           .where(dorm.CMP('year', dorm.GTE, 2023)) \

        result = orm.dicts()
        expected = [d for d in DATA if d[Key.year] >= 2023]
        self.assertEqual(len(result), len(expected))

        expected = {
            'year': expected[0][Key.year],
            'title': expected[0][Key.title]
        }
        self.assertEqual(result[0], expected)

    def test_groups(self):
        orm = self.get_orm()
        orm.select('franchise', 'year', 'title') \
           .group('franchise')

        result = orm.groups()
        self.assertEqual(len(result), 2)
        self.assertIn('Marvel', result)
        self.assertIn('DC', result)


if __name__ == '__main__':
    unittest.main()
