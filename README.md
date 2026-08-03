# madden-ratings-breakdown

Madden NFL 27 player ratings database scraped directly from [EA's official ratings site](https://www.ea.com/games/madden-nfl/ratings).

## Output

`scraper/output/madden27_ratings.csv` — 2,365 players, 82 columns including all individual ratings, archetypes, X-Factors, and Superstar abilities.

## Usage

```bash
pip install -r requirements.txt
python scraper/scrape.py
```

The script fetches the current build ID from the EA site at runtime, paginates all 24 pages (100 players each), and writes the CSV to `scraper/output/madden27_ratings.csv`.

## Columns

| Group | Columns |
|-------|---------|
| Identity | `season`, `player_id`, `first_name`, `last_name`, `full_name`, `position`, `team_name`, `team_short` |
| Physical | `age`, `height_inches`, `weight_lbs`, `college`, `years_pro`, `jersey_num`, `birth_day`, `birth_month`, `birth_year`, `handedness` |
| Classification | `overall`, `archetype`, `iteration` |
| Abilities | `x_factor`, `ability_1`–`ability_6` |
| Ratings | 54 individual stat columns (`accel_rating` → `zone_cover_rating`) + `running_style` |
