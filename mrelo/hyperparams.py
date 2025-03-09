import enum


class Param:
    """
    Hyperparameter Class
    Provides a common api as well as info for genetic
    algorithm to reference.

    Customized with magic functions to allow for usage as both
    an index for iterables as well as a key for dicts.
    """
    def __init__(self, _name: str, index: int, space: dict):
        """
        Args:
            name: descriptive name for user reference,
                currently not referenced in code anywhere.
            index: used for array indexing and
                dict key hashing. Important for genetic algorithm,
                since new hyperparameters are returned each generation
                as tuple.
            space: Value range/space used by pygad to determine
                range of values to try for this hyperparameter.
        """
        self._name = _name
        self.index = index
        self.space = space

    def __int__(self):
        return self.index

    def __index__(self):
        return self.index

    def __hash__(self):
        return hash(self.index)

    def __eq__(self, other):
        return self.index == other


def space_dict(low: float, high: float, step: float) -> dict:
    # formats dict to pygad gene space spec
    # https://pygad.readthedocs.io/en/latest/pygad.html#pygad-ga-class
    return {'low': low, 'high': high, 'step': step}


class Params(enum.IntEnum):
    """
    Hyperparameter class.

    Allows for easy indexing in either an iterable or dict
    with typed parameters.

    Naming convention:
        '*_mul': these are multipliers, i.e. multiplied to a value
        '*_mod': these are modifiers, i.e. added to a value
    """
    def __new__(cls, p: Param):
        obj = int.__new__(cls, p.index)
        obj._value_ = p.index
        obj._name = p._name
        obj.space = p.space
        return obj

    # SHIFT_ELO_PRE()
    # default evalut Elo rating when teams are first introduced
    start = Param('starting elo', 0, space_dict(800, 1500, 5))
    # target average Elo rating, used for mean reversion at start of season
    elo_avg = Param('elo_mean', 1, space_dict(900, 1700, 5))
    # percent of current Elo to revert to elo_mean
    revert = Param('revert_to_mean', 2, space_dict(0.05, 0.55, 0.01))

    # CALC_PRE_DIFF()
    # multiplier to apply to the diff between two teams rest days
    rest_mul = Param('rest_mul', 3, space_dict(-25, 25, 0.25))
    # modifier added to home team for non-neutral games
    hfa_mod = Param('home_field_advantage', 4, space_dict(-20, 120, 0.5))

    # SHIFT_ELO_POST()
    # Elo's K-factor starting value
    k_start = Param('k_start', 5, space_dict(2, 60, 1))
    # Elo's K-factor final value
    k_end = Param('k_end', 6, space_dict(2, 60, 1))
    # Number of games played when K-factor shifts from k_start to k_end.
    k_rate = Param('k_rate', 7, space_dict(4, 20, 1))
    # Control the sensitivity of the MOV multiplier to handle autocorrelation
    ac_mul = Param('ac_mul', 8, space_dict(0.001, 0.01, 0.001))
    # Limit MOV impact for wide rating differences to handle autocorrelation
    ac_mod = Param('ac_mod', 9, space_dict(3.5, 12, 0.25))
    # Margin of victory multiplier for handling autocorrelation
    mov_mul = Param('mov_mul', 10, space_dict(0.05, 0.95, 0.025))
    # Margin of victory modified for handling autocorrelation
    mov_mod = Param('mov_mod', 11, space_dict(0.0, 2, 0.2))
