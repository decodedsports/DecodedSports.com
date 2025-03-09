# MrElo

<em>This package is an in-house product of [DecodedSports.com](https://www.decodedsports.com).</em>

Named after the one and only [Mr. Elo](https://en.wikipedia.org/wiki/Arpad_Elo) (ELO is not an acronym!!).

This package implements an Elo ratings model, generalized to any form of A vs. B competitions. MrElo also provides the means to compute the hyperparameters (aka magic values) that are often an enigma in most Elo tutorials.

[Read more here](https://www.decodedsports.com/blog/our-elo-model/).

# Features

- Supports any arbitrary competition (sport agnostic) that is A vs. B format.
- Handles autocorrelation for both winning likelihood and Margin of Victory.
- Offers two methods for Margin of Victory autocorrelation handling.
- Allows for pre-match rating adjustments along with the default post-match adjustments.
- Allows rating differences to be converted into probabilities.
- Provides a pre-configured genetic algorithm to tune hyperparameters for your sport.

# Usage

Basic usage with the all-in-one `calc_elo` function which handles `pre-match elo shifts`, `pre-match diff adjustment`, and `post-match rating shift`.

```python
import mrelo

result = mrelo.calc_elo(
    cfg=hyperparams,
    elo_pre1=1250,  # home team
    elo_pre2=1070,  # away team
    mov=(4 - 6)     # home upset
)

print(result)
"""
(
    1250,  # elo_pre1
    1070,  # elo_pre2
    1235.24,  # elo_post1
    1084.76,  # elo_post2
    0.738  # elo_prob1
)
"""
```

The red herring in the above example is the `hyperparams` variable. You can tune your own like this with a genetic algorithm.

```python
import pandas

import mrelo

from your_custom_code import fetch_data

cols = [
    'fr_team1', 'fr_team2',
    'score1', 'score2',
    'played1', 'played2',
    'rest1', 'rest2',
    'neutral'
]
data = fetch_data(cols)
"""
[
    ('a', 'b', 4, 6, 0, 0, 1, 1, 0),
    ('a', 'c', 8, 3, 1, 0, 1, 1, 0),
    ('b', 'c', 4, 2, 1, 1, 1, 1, 0),
    ('b', 'a', 1, 3, 2, 2, 1, 1, 0),
    ...
]
"""

df = pandas.DataFrame(data, columns=cols)
hyperparams = mrelo.ga_optimize(df)
"""
{
    <Params.start: 0>: 1125,
    <Params.elo_avg: 1>: 1300,    
    <Params.revert: 2>: 0.3,
    <Params.hfa_mod: 4>: 21,
    ...
}
"""
```

And of course, the default Elo formula for computing win probability:

```python
import mrelo

# Example: Home is favorite
rating_diff = 75  # home_elo - away_elo
mrelo.elo_probability(rating_diff)
>>> 0.60629

# Example: Home is underdog
rating_diff = -75  # home_elo - away_elo
mrelo.elo_probability(rating_diff)
>>> 0.39371
```

# Why DecodedSports loves MrElo

Elo is everthing to DecodedSports. It allows us to:

- Rank teams
- Compute matchup probabilities
- Incorporate external non-game factors to adjust ratings
- Determine favorites/underdogs for situational based stats

An Elo rating model is the closest you can get to reproducing Vegas sportsbook odds and thus an extremely powertool for analyzing sports.

# Inspiration

[FiveThirtyEight's](https://projects.fivethirtyeight.com/polls/) infamous sports prediction algorithm was significant inspiration for the MrElo's implementation. Painstaking detail was taken to recreate it and many dark corners of the internet were reached to understand what was unwritten between the lines. 

### Models
- [FiveThirtyEight NFL Model Pt.1](https://fivethirtyeight.com/features/introducing-nfl-elo-ratings/)
- [FiveThirtyEight NFL Model Pt.2](https://fivethirtyeight.com/methodology/how-our-nfl-predictions-work/)
- [FiveThirtyEight MLB Model](https://fivethirtyeight.com/methodology/how-our-mlb-predictions-work/)
- [FiveThirtyEight NHL Model](https://fivethirtyeight.com/methodology/how-our-nhl-predictions-work/)
- [FiveThirtyEight NBA Model](https://fivethirtyeight.com/methodology/how-our-nba-predictions-work/)

### Autocorrelation
- [Autocorrelation in Elo Ratings](https://stats.stackexchange.com/questions/168047/accounting-for-autocorrelation-in-margin-based-elo-ratings)
- [Autocorrelation and Margin of Victory in Elo Ratings](https://andr3w321.com/elo-ratings-part-2-margin-of-victory-adjustments/)


# Caveats

### Hyperparameters

The most mysterious portions of FiveThirtyEight's models (and any Elo tutorial) are the hyperparameters and how they are derived, e.g. why there is a `rest adjustment by 25`, `playoff multiplier of 1.2`, or `home field advantage of 23.6`, etc.

These values will not work in any setting other than the specific implementation they tuned were for. Even the simplest Elo implementations will vary enough that new hyperparameters need to be retuned. Just like race cars on a track!

Hyperparameters are sometimes called `magic values` for a reason, always be cautious of them and tune them yourself!

We do not provide our internal hyperparameters, but do give you a way to tune yours.

### Autocorrelation

Most Elo implementations differ the most with their handling of autocorrelation. Mr. Elo himself did not incorpoate this into his original formulas. There are two types that most sports models must account for:

- <b>Win Autocorrelation</b>

<i>Those likely to win will keep winning.</i>

MrElo mirrors the default implementation on FiveThirtyEight.

- <b>Margin of Victory (MoV) Autocorrelation</b>

<i>Those likely to win, are more likely to win by a lot.</i>

MrElo offers two approaches, both of which are used across different sports on FiveThirtyEight.

# License

This project is licensed under the terms of the MIT license.

# Questions?
Please reach out to us via [DecodedSports here](https://www.decodedsports.com/contact).
