import math

from mrelo.hyperparams import Params


def elo_probability(rating_diff: float) -> float:
    """
    Returns the expected score (aka win probability) based on the
    difference in rating between two teams.

    https://en.wikipedia.org/wiki/Elo_rating_system#Mathematical_details

    Args:
        rating_diff: diff between team ratings,
            rating_diff = (team1_rating - team2_rating)

    Returns:
        probability of team1 winning

    Example:
        >>> elo_probability(0)
        0.5
        >>> round(elo_probability(50), 3)
        0.571
        >>> round(elo_probability(-50), 3)
        0.429
    """
    return 1.0 / (math.pow(10, (-rating_diff / 400)) + 1)


def shift_elo_pre(elo_pre: float,
                  n: int,
                  cfg: dict = None) -> float:
    """
    Shifts elo rating pre-match.

    Allows for adjustments like at start of season and other external
    non-game related factors for a single team.

    Currently only accounts for season_start adjustments.

    Args:
        elo_pre: pre_match Elo rating of the team
        n: number of games the team has played in the season thus far
        cfg: dict where the keys are one of hyperparams.Params
            if used, then Params.elo_avg and Params.revert must be set.

    Returns:
        Value to shift the existing elo by.

    Example:
        >>> cfg = {Params.elo_avg: 500, Params.revert: 0.5}
        >>> shift_elo_pre(elo_pre=1000, n=0, cfg=cfg)
        -250.0
    """
    if n > 0 or n is None:
        return 0

    # season start
    elo_post = elo_pre
    if Params.elo_avg in cfg:
        reverted_elo = cfg[Params.elo_avg] * cfg[Params.revert]
        existing_elo = elo_pre * (1 - cfg[Params.revert])
        elo_post = reverted_elo + existing_elo

    return elo_post - elo_pre


def calc_pre_diff(elo_pre1: float, elo_pre2: float,
                  rest1: int, rest2: int,
                  is_neutral: bool, cfg: dict) -> float:
    """
    Calculates the pre-match rating difference.

    Intended to be used after all pre-match rating adjustments
    have been applied to each team.

    This pre-match diff does not immediately affect a team's rating. It is
    only used as input into the post-match adjustments.

    Args:
        elo_pre1: pre-match rating for team1 (intended to be the home team)
        elo_pre2: pre-match rating for team2 (intended to be the away team)
        rest1: number of days of rest since team1's most recent game
        rest2: number of days of rest since team2's most recent game
        is_neutral: if the game is played a neutral venue, i.e. where
            no home-field advantage exists
        cfg: dict where the keys are one of hyperparams.Params
            if used, then Params.hfa_mod and or Params.rest_mul must be set.

    Returns:
        rating difference between both teams from the perspective of team1
            rating_diff = (team1_rating - team2_rating)
    """
    rating_diff = elo_pre1 - elo_pre2

    # Home field advantage
    if not is_neutral and Params.hfa_mod in cfg:
        rating_diff += cfg[Params.hfa_mod]

    # Rest diff
    if Params.rest_mul in cfg:
        rating_diff += cfg[Params.rest_mul] * (rest1 - rest2)

    return rating_diff


def shift_elo_post(rating_diff: float,
                   mov: int,
                   n1: int,
                   n2: int,
                   cfg: dict,
                   ac_mov_log: bool = True) -> float:
    """

    Shifts elo rating post-match.

    Args:
        rating_diff: Rating difference between both teams from
            perspective of team1, rating_diff = (team1_rating - team2_rating)
        mov: Margin of Victory (MoV) from the perspective of team1.
            mov = team1_score - team2_score.
            Positive means team1 won. Negative means team2 won.
        n1: # of games that have been played by team1
        n2: # of games that have been played by team2
        cfg: dict where the keys are one of hyperparams.Params
            if used, then Params.hfa_mod and or Params.rest_mul must be set.
        ac_mov_log: Two methods for handling margin of victory autocorrelation,
            If True (method #1): uses natural logarithm
            If False (method #2): uses exponential multiplier

    Returns:
        Value to shift the existing elo by.
        If Positive:
            This means team1 won
        If Negative:
            This means team2 won

        This is a zero-sum value meaning it should be applied to
        both teams equally. Added to team1 and subtracted from team2.

    Example:
        >>> team1_elo, team2_elo = 1000, 1200
        >>> rating_diff = team1_elo - team2_elo
        >>> cfg = {Params.k_start: 30}
        >>> shift = shift_elo_post(rating_diff, -2, 1, 1, cfg)
        >>> team1_elo = round(team1_elo + shift)
        >>> team2_elo = round(team2_elo - shift)
        >>> print(team1_elo, team2_elo)
        993 1207
    """
    # CHANGE RATING DIFF TO WINNER'S PERSPECTIVE
    winner_r_diff = rating_diff
    if mov > 0:  # home win
        winner_r_diff = rating_diff
    elif mov == 0:  # tie
        winner_r_diff = 0
    else:  # away win
        winner_r_diff = -rating_diff

    # AUTOCORRELATION (AC)
    ac_adj, mov_mult = 1, 1

    # AC: Winner:
    if Params.ac_mod in cfg:
        ac_adj = (cfg[Params.ac_mod] /
                  (winner_r_diff * cfg[Params.ac_mul] + cfg[Params.ac_mod]))

    # AC: MOV
    if Params.mov_mul in cfg:
        if ac_mov_log:
            abs_mov = max(abs(mov), 1)
            mov_mult = (cfg[Params.mov_mul] * math.log(abs_mov) +
                        cfg[Params.mov_mod])
        else:
            mov_mult = (mov + cfg[Params.mov_mod])**cfg[Params.mov_mul]

    # COMPARE TO PRE-MATCH EXPECTED OUTCOME
    win_prob1 = elo_probability(rating_diff)
    win1 = 1 if mov > 0 else 0
    expectation_adj = win1 - win_prob1

    # COMBINE ALL MODIFIERS
    k = cfg[Params.k_start]
    if Params.k_rate in cfg:
        n_adj = (n1 + n2) / 2  # could use min/max
        k = k if n_adj <= cfg[Params.k_rate] else cfg[Params.k_end]

    shift = k * expectation_adj * mov_mult * ac_adj

    return shift


def calc_elo(cfg: dict,
             elo_pre1: float,
             elo_pre2: float,
             mov: int,
             n1: int = 0,
             n2: int = 0,
             rest1: int = 0,
             rest2: int = 0,
             neutral: bool = False) -> tuple:
    """
    All-in-one Elo calculation function that performs the following
    standard Elo update pipeline:

    - pre-match update
    - pre-match diff calculation
    - post-match update

    Args:
        cfg: dict where the keys are one of hyperparams.Params
            if used, then Params.hfa_mod and or Params.rest_mul must be set.
        elo_pre1: pre-match rating for team1 (intended to be the home team)
        elo_pre2: pre-match rating for team2 (intended to be the away team)
        mov: Margin of Victory (MoV) from the perspective of team1.
            mov = team1_score - team2_score.
            Positive means team1 won. Negative means team2 won.
        n1: number of games that have been played by team1
        n2: number of games that have been played by team2
        rest1: number of days of rest since team1's most recent game
        rest2: number of days of rest since team2's most recent game
        is_neutral: if the game is played a neutral venue, i.e. where
            no home-field advantage exists

    Returns:
        A tuple with five float values in the following order:
        - 'elo_pre1': adjuted pre-match Elo for team1
        - 'elo_pre2': adjuted pre-match Elo for team2
        - 'elo_post1': post-match Elo for team1
        - 'elo_post2': post-match Elo for team2
        - 'elo_prob1': pre-match win probability for team1

    Example:
        >>> result = calc_elo(
        ...     cfg={Params.k_start: 25},
        ...     elo_pre1=1250,  # home team
        ...     elo_pre2=1070,  # away team
        ...     mov=(4 - 6),  # home upset
        ... )
        >>> print([round(x, 2) for x in result])
        [1250, 1070, 1231.55, 1088.45, 0.74]
    """
    elo_pre1 += shift_elo_pre(elo_pre1, n1, cfg)
    elo_pre2 += shift_elo_pre(elo_pre2, n2, cfg)
    pre_diff = calc_pre_diff(elo_pre1, elo_pre2, rest1, rest2, neutral, cfg)

    post_shift = 0
    if mov and not math.isnan(mov):
        post_shift = shift_elo_post(pre_diff, mov, n1, n2, cfg)

    elo_post1 = elo_pre1 + post_shift
    elo_post2 = elo_pre2 - post_shift
    elo_prob1 = elo_probability(pre_diff)

    return elo_pre1, elo_pre2, elo_post1, elo_post2, elo_prob1
