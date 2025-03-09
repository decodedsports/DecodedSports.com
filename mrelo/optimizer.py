import itertools
import math
import random
import typing

import numpy
import pandas
import pygad

from sklearn import metrics

from mrelo.elo import calc_elo
from mrelo.hyperparams import Params


def brier_skill_score(y_true, y_pred, y_ref=None) -> float:
    """
    Brier Skill Score (BSS)

    # https://en.wikipedia.org/wiki/Brier_score#Brier_skill_score_(BSS)

    This is the same as metrics.r2_score when y_ref is None

    Args:
        y_true: array of true values
        y_pred: array of predicted values
        y_ref: optional array of reference predicted values.
            If None, then mean(y_true) will be used, which effectively
            makes BSS the same as R2

    Returns:
        BSS
    """
    bs = metrics.brier_score_loss(y_true, y_pred)
    y_true_mean = numpy.mean(y_true)
    if y_ref is None:
        y_true_mean = numpy.mean(y_true)
        y_ref = [y_true_mean] * len(y_true)
    bs_ref = metrics.brier_score_loss(y_true, y_ref)
    bss = 1 - (bs / bs_ref)
    return bss


def pretty_dict(d: dict, key_conv: typing.Callable = None,
                rnd: int = 5) -> dict:
    """
    Utility for making a dict of ugly vals pretty for printing.

    Args:
        d: dict of ugly int|float values to prettify
        key_conv: optional function to convert the key value type.
            useful if the key is a verbose enum.
        rnd: number of decimal places to round values.

    Returns:
        pretty dict

    Example:
        >>> d = {'1': 0.238431, '2': 14.9811234321232, '3': 3.422}
        >>> pretty_dict(d, key_conv=int, rnd=2)
        {1: 0.24, 2: 14.98, 3: 3.42}
    """
    return {key_conv(k) if key_conv else k: round(v, rnd) if v else v
            for k, v in d.items()}


def tuple_to_dict(tup, keys=None) -> dict:
    """
    Utility for converting a tuple into a dict.

    Args:
        tup: tuple with values of any type
        keys: Optional list of key names.
            If not provided, will use int index as the key

    Returns:
        dict version of the tuple

    Example:
        >>> tup = (42, 84, 126)
        >>> tuple_to_dict(tup, keys=['a', 'b', 'c'])
        {'a': 42, 'b': 84, 'c': 126}
    """
    keys = keys or list(keys)
    d = {k: tup[i] for i, k in enumerate(keys)}
    return d


def print_solution(sol: dict, scores: dict, gen: int = None,
                   no_print=False) -> str:
    """
    Prints formatted optimization solution.
    Useful for copying into script or json to save solution for use later.

    Args:
        sol: solution formatted as a dict (not a tuple).
        r2: as in sklearn.metrics.r2_score
        ll: as in sklearn.metrics.log_loss
        ac: as in sklearn.metrics.accuracy_score
        gen: generation the solution was generated in
        no_print: if the formatted solution should be printed or only returned

    Returns:
        formatted solution string

    Example:
        >>> sol = {0: 21, 1: 42, 2: 84}
        >>> scores = {'r2': 1.42, 'll': 2.14, 'ac': 3.43}
        >>> print_solution(sol, scores, no_print=True)
        '{0: 21, 1: 42, 2: 84},  # noqa, r2=1.4200 ll=2.1400 ac=3.4300'
    """
    if gen is not None:
        print(f'{gen}: ', end='')

    score_strs = [f'{k}={v:2.4f}' for k, v in scores.items() if k != 'score']
    fmt = '%s,  # noqa, %s'
    fmt_sol = fmt % (pretty_dict(sol, int), ' '.join(score_strs))
    if not no_print:
        print(fmt_sol)

    return fmt_sol


class ModelMeta:
    def __init__(self, data):
        self._i = 0
        self._genes = Params
        self._valid = 0
        self._best = {'score': -math.inf}
        self._best_config: dict = None
        self._data: pandas.DataFrame = data


def enrich_elo_vec(df: pandas.DataFrame, cfg: dict) -> numpy.array:
    """
    Non-vectorized version of enrich_elo()
    See enrich_elo docstring.
    """
    # INIT TEAMS
    team_elos = {}
    all_teams = pandas.concat([df['fr_team1'], df['fr_team2']]).unique()
    for t in all_teams:
        team_elos[t] = cfg[Params.start]

    # PREP RESULTS AND EXTRACT DF VALUES
    results = numpy.empty((1, 5))[1:]
    cols = [
        'fr_team1', 'fr_team2', 'score1', 'score2',
        'played1', 'played2', 'rest1', 'rest2', 'neutral'
    ]
    values = df[cols].values

    # ENRICH
    for vals in values:
        team1, team2 = vals[0], vals[1]
        mov = vals[2] - vals[3]  # score1 - score2
        r = calc_elo(cfg, team_elos[team1], team_elos[team2], mov, *vals[4:])
        team_elos[team1] = r[2]  # elo_post1
        team_elos[team2] = r[3]  # elo_post2
        results = numpy.append(results, [r], axis=0)

    return results


def stateful_enricher(team_elos: dict, cfg: dict):
    # Closure for use with vectorized itertools.accumulate

    def wrapped(_, vals: tuple):
        # Signature must conform to https://docs.python.org/3/library/itertools.html#itertools.accumulate  # noqa
        team1, team2 = vals[0], vals[1]
        mov = vals[2] - vals[3]  # score1 - score2
        r = calc_elo(cfg, team_elos[team1], team_elos[team2], mov, *vals[4:])
        team_elos[team1] = r[2]  # elo_post1
        team_elos[team2] = r[3]  # elo_post2
        return r

    return wrapped


def enrich_elo(df: pandas.DataFrame, cfg: dict) -> numpy.array:
    """
    Enriches given DataFrame with computed Elo rating columns.

    This is partially vectorized, but still ~2.8x faster than non-vectorized.

    Args:
        df: DataFrame that has the below 9 columns:
            'fr_team1', 'fr_team2', 'score1', 'score2',
            'played1', 'played2', 'rest1', 'rest2', 'neutral'
        cfg: dict where the keys are one of hyperparams.Params
            if used, then Params.hfa_mod and or Params.rest_mul must be set.

    Returns:
        the original df, but updated with five new columns:
        'elo_pre1', 'elo_pre2', 'elo_post1', 'elo_post2', 'elo_prob1'
        which were computed from the Elo model
    """
    # INIT TEAMS
    team_elos = {}
    all_teams = pandas.concat([df['fr_team1'], df['fr_team2']]).unique()
    for t in all_teams:
        team_elos[t] = cfg[Params.start]

    # EXTRACT DATAFRAME VALUES
    cols = [
        'fr_team1', 'fr_team2', 'score1', 'score2',
        'played1', 'played2', 'rest1', 'rest2', 'neutral'
    ]
    values = df[cols].values
    # The accumulator skips the first item, so need to pad w/bogey first item
    values = numpy.append(numpy.zeros((1, values.shape[1])), values, axis=0)

    # ENRICH
    enricher = stateful_enricher(team_elos, cfg)
    results = itertools.accumulate(values, func=enricher)
    results = numpy.array(list(results)[1:])  # remove bogey first item

    return results


def fitness_func_wrapper(forecaster):

    def fitness_func(model: ModelMeta, solution: tuple, args=None) -> float:
        """
        Fitness function to evaluate a solution.

        Args:
            model: could be a variety of types based on the type of solver
                being used, e.g. pygad passes the pygad.GA class to the
                fitness function. Regardless of the source of this class
                instance, we enrich it ahead of time to add a few meta
                attributes to help us later, like the list of genes,
                current best score, etc. These are accessed via `model._<attr>`
            solution: tuple of floats with the values optimized by the solver
            args: some solvers pass an additional parameters that we do not use

        Returns:
            score for the solution
        """
        df = model._data
        model._i += 1

        try:
            results = forecaster(df, solution)
        except OverflowError:
            return -math.inf

        model._valid += 1
        elo_prob1 = results[:, -1]
        score = r2 = metrics.r2_score(df['win1'], elo_prob1)
        predicted = elo_prob1.round()
        if score > model._best['score']:
            scores = {
                'score': score,
                'r2': r2,
                'll': metrics.log_loss(df['win1'], elo_prob1),
                'ac': metrics.accuracy_score(df['win1'], predicted)
            }
            model._best = scores
            config = tuple_to_dict(solution, model._genes)
            model._best_config = config
            print_solution(config, scores, gen=model._i)
        return score

    return fitness_func


def random_optimize(df: pandas.DataFrame, num_gens: int = 10_000):
    """
    Random Optimizer.

    This is horrible, do not use in practice, only for troubleshooting.

    Args:
        df: DataFrame that has the below 9 columns:
            'fr_team1', 'fr_team2', 'score1', 'score2',
            'played1', 'played2', 'rest1', 'rest2', 'neutral'
        num_gens: number of generations to attempt to fit the model

    Returns:
        Best fitted model config, that conforms to hyperparms.Params spec
    """
    # GET GENE SPACE
    spaces = []
    for g in Params:
        space = g.space
        if isinstance(space, list):
            spaces.append(space)
            continue
        space_rng = numpy.arange(space['low'], space['high'], space['step'])
        spaces.append((g, list(space_rng)))

    # OPTIMIZE
    model = ModelMeta(df)
    fitness_func = fitness_func_wrapper(enrich_elo)
    for _ in range(num_gens):
        config = {g: random.choice(s) for g, s in spaces}
        fitness_func(model, config)

    return model._best_config


def ga_optimize(df: pandas.DataFrame, num_gens: int = 1000) -> dict:
    """
    Genetic Algorithm Optimizer using pygad.

    Args:
        df: DataFrame that has the below 9 columns:
            'fr_team1', 'fr_team2', 'score1', 'score2',
            'played1', 'played2', 'rest1', 'rest2', 'neutral'
        num_gens: number of generations to attempt to fit the model

    Returns:
        Best fitted model config, that conforms to hyperparms.Params spec
    """
    fitness_func = fitness_func_wrapper(enrich_elo)
    gene_space = [g.space for g in Params]

    # https://pygad.readthedocs.io/en/latest/pygad.html#pygad-ga-class
    model = pygad.GA(
        # REQUIRED PARAMS
        fitness_func=fitness_func,
        gene_space=gene_space,
        num_generations=num_gens,
        num_genes=len(Params),
        num_parents_mating=100,
        sol_per_pop=300,

        # OPTIONAL: TYPICAL PARAMS
        parallel_processing=["thread", 10],
        crossover_probability=0.75,  # exploitation
        mutation_probability=0.25  # (0.25, 0.1),  # exploration

        # OPTIONAL: RARE PARAMS
        # single_point (default), two_points, uniform, scattered
        # crossover_type='single_point',
        # random (default), swap, inversion, scramble, adaptive
        # mutation_type='adaptive',
        # sss (default), rws, sus, rank, random, tournament
        # parent_selection_type='sss',
        # suppress_warnings=True,
    )

    # SET META ATTRIBUTES FOR USE IN FITNESS FUNC
    model._genes = Params
    model._i = 0
    model._valid = 0
    model._data = df
    model._best = {'score': -math.inf}
    model.run()

    return model._best_config
