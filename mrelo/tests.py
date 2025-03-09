import unittest

from mrelo.elo import (
    calc_elo, calc_pre_diff, elo_probability, shift_elo_post, shift_elo_pre
    )
from mrelo.hyperparams import Params


class Test(unittest.TestCase):

    def test_probability(self):
        self.assertEqual(elo_probability(0), 0.5)
        p = 0.57146311  # precomputed
        self.assertAlmostEqual(elo_probability(50), p)
        self.assertAlmostEqual(elo_probability(-50), 1 - p)

    def test_shift_elo_pre(self):
        cfg = {Params.elo_avg: 1000, Params.revert: 0.5}
        r = shift_elo_pre(2000, 1, cfg)
        self.assertEqual(r, 0)

        r = shift_elo_pre(2000, 0, cfg)
        self.assertEqual(r, -500)

    def test_calc_pre_diff(self):
        cfg = {Params.hfa_mod: 10, Params.rest_mul: 5}

        # Non-neutral Game
        r = calc_pre_diff(1000, 1200, 2, 5, False, cfg)
        expected = (
            # Elo diff
            (1000 - 1200) +
            # Home field advantage when not neutral
            10 +
            # Rest diff
            (5 * (2 - 5)))
        self.assertEqual(r, expected)

        # Neutral Game
        r = calc_pre_diff(1000, 1200, 2, 5, True, cfg)
        expected = expected - 10  # remove home field advantage
        self.assertEqual(r, expected)

    def test_shift_elo_post(self):
        cfg = {Params.k_start: 10}

        r = shift_elo_post(0, 3, 0, 0, cfg)
        self.assertEqual(r, 5)

        r1 = shift_elo_post(100, 3, 0, 0, cfg)
        r2 = shift_elo_post(150, 3, 0, 0, cfg)
        self.assertGreater(r1, r2)

        r1 = shift_elo_post(100, 3, 0, 0, cfg)
        r2 = shift_elo_post(-100, -3, 0, 0, cfg)
        self.assertAlmostEqual(r1, -r2)

    def test_calc_elo(self):
        args = {
            'cfg': {
                Params.k_start: 10
            },
            'elo_pre1': 1000,
            'elo_pre2': 1500,
            'mov': 3,
        }
        r = calc_elo(**args)
        elo_pre2, elo_post2 = r[1], r[3]
        self.assertLess(elo_post2, elo_pre2)


if __name__ == '__main__':
    unittest.main()
