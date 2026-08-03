# Madden 27 Ratings Scraper — Plan

## Top-Level Overview

Build a Python scraper (`scraper/scrape.py`) that produces `scraper/output/madden27_ratings.csv` containing every player (all 2,365) from EA's Madden NFL 27 ratings site. The EA site is a Next.js app; all player data is served by a public paginated JSON endpoint — no individual player page visits needed.

**Endpoint:** `https://www.ea.com/_next/data/{buildId}/games/madden-nfl/ratings.json?page=N`
- 100 players per page, 24 pages total, `totalItems=2365`
- The build ID rotates on redeploys — fetched fresh each run from the homepage HTML

**Only external dependency:** `requests>=2.32.0`

---

## Column Schema (matches `players.csv` format, with M27 additions)

Columns with no EA data equivalent (`snapshot_id`, `source_url`, `draft_round`, `draft_pick`, `draft_position`, `long_snap_rating`, `throw_acc_rating`) are **dropped entirely** — not included in the output CSV.

| Column | Source | Notes |
|--------|--------|-------|
| `season` | hardcoded | `"m27-1"` |
| `player_id` | `id` | EA numeric player ID |
| `first_name` | `firstName` | |
| `last_name` | `lastName` | |
| `full_name` | computed | `firstName + " " + lastName` |
| `position` | `position.id` | e.g. `"WR"` |
| `team_name` | `team.label` | e.g. `"Cincinnati Bengals"` |
| `team_short` | `team.label` | Last word of team name, e.g. `"Bengals"` |
| `age` | `age` | |
| `height_inches` | `height` | |
| `weight_lbs` | `weight` | |
| `college` | `college` | |
| `years_pro` | `yearsPro` | |
| `jersey_num` | `jerseyNum` | |
| `birth_day` | `birthdate` | parsed from `"M/D/YY"` |
| `birth_month` | `birthdate` | parsed from `"M/D/YY"` |
| `birth_year` | `birthdate` | parsed from `"M/D/YY"` (2-digit → 4-digit) |
| `overall` | `overallRating` | |
| `archetype` | `archetype.label` | **M27 addition** e.g. `"Deep Threat - WR"` |
| `iteration` | `iteration.label` | **M27 addition** e.g. `"Launch Ratings"` |
| `handedness` | `handedness` | **M27 addition** `1`=right, `0`=left |
| `x_factor` | `playerAbilities` | ability where `type.id == "xFactor"`, label only; blank if none |
| `ability_1`…`ability_6` | `playerAbilities` | Superstar abilities only (`type.id == "superstarAbility"`), label; blank if fewer than 6 |
| `accel_rating` | `stats.acceleration` | |
| `agility_rating` | `stats.agility` | |
| `awareness_rating` | `stats.awareness` | |
| `bcv_rating` | `stats.bCVision` | |
| `block_shed_rating` | `stats.blockShedding` | |
| `break_sack_rating` | `stats.breakSack` | |
| `break_tackle_rating` | `stats.breakTackle` | |
| `carry_rating` | `stats.carrying` | |
| `catch_rating` | `stats.catching` | |
| `change_of_direction_rating` | `stats.changeOfDirection` | |
| `cit_rating` | `stats.catchInTraffic` | |
| `finesse_moves_rating` | `stats.finesseMoves` | |
| `hit_power_rating` | `stats.hitPower` | |
| `impact_block_rating` | `stats.impactBlocking` | |
| `injury_rating` | `stats.injury` | |
| `juke_move_rating` | `stats.jukeMove` | |
| `jump_rating` | `stats.jumping` | |
| `kick_acc_rating` | `stats.kickAccuracy` | |
| `kick_power_rating` | `stats.kickPower` | |
| `kick_ret_rating` | `stats.kickReturn` | |
| `lead_block_rating` | `stats.leadBlock` | |
| `man_cover_rating` | `stats.manCoverage` | |
| `pass_block_finesse_rating` | `stats.passBlockFinesse` | |
| `pass_block_power_rating` | `stats.passBlockPower` | |
| `pass_block_rating` | `stats.passBlock` | |
| `play_action_rating` | `stats.playAction` | |
| `play_rec_rating` | `stats.playRecognition` | |
| `power_moves_rating` | `stats.powerMoves` | |
| `press_rating` | `stats.press` | |
| `pursuit_rating` | `stats.pursuit` | |
| `release_rating` | `stats.release` | |
| `route_run_deep_rating` | `stats.deepRouteRunning` | |
| `route_run_med_rating` | `stats.mediumRouteRunning` | |
| `route_run_short_rating` | `stats.shortRouteRunning` | |
| `run_block_finesse_rating` | `stats.runBlockFinesse` | |
| `run_block_power_rating` | `stats.runBlockPower` | |
| `run_block_rating` | `stats.runBlock` | |
| `running_style` | `stats.runningStyle` | **M27 addition** string e.g. `"Default"` |
| `spec_catch_rating` | `stats.spectacularCatch` | |
| `speed_rating` | `stats.speed` | |
| `spin_move_rating` | `stats.spinMove` | |
| `stamina_rating` | `stats.stamina` | |
| `stiff_arm_rating` | `stats.stiffArm` | |
| `strength_rating` | `stats.strength` | |
| `tackle_rating` | `stats.tackle` | |
| `throw_acc_deep_rating` | `stats.throwAccuracyDeep` | |
| `throw_acc_mid_rating` | `stats.throwAccuracyMid` | |
| `throw_acc_short_rating` | `stats.throwAccuracyShort` | |
| `throw_on_run_rating` | `stats.throwOnTheRun` | |
| `throw_power_rating` | `stats.throwPower` | |
| `throw_under_pressure_rating` | `stats.throwUnderPressure` | |
| `tough_rating` | `stats.toughness` | |
| `truck_rating` | `stats.trucking` | |
| `zone_cover_rating` | `stats.zoneCoverage` | |

**New columns vs `players.csv`:** `archetype`, `iteration`, `handedness`, `running_style`, `ability_6`

---

## Sub-Tasks

---

### Sub-Task 1 — Discover and lock the build ID

**Intent:** The Next.js data API URL contains a build hash that may rotate on redeploys. The scraper must fetch the live homepage once to extract the current build ID.

**Expected Outcomes:**
- A `get_build_id(session)` function that returns the current build ID string.

**Todo List:**
1. `GET https://www.ea.com/games/madden-nfl/ratings` with a browser-like `User-Agent`.
2. Regex-extract build ID from `/_next/static/<buildId>/_buildManifest.js`.
3. Return the string; raise `RuntimeError` if not found.

**Relevant Context:**
- Confirmed build ID in saved HTML: `KwZplYqdSSe4iXkQsTuuI`
- Regex pattern: `/_next/static/([^/]+)/_buildManifest\.js`

**Status:** `[ ] pending`

---

### Sub-Task 2 — Paginate and collect all player records

**Intent:** Fetch every page of the ratings list endpoint and accumulate raw player dicts.

**Expected Outcomes:**
- A `fetch_all_players(session, build_id)` function returning a list of ~2,365 raw player dicts.

**Todo List:**
1. Fetch page 1, read `pageProps.ratingDetails.totalItems` to compute page count (`ceil(total / 100)`).
2. Loop pages 1..N, collecting `pageProps.ratingDetails.items` into a list.
3. Add a 1-second polite delay between requests.
4. Deduplicate by `id` before returning.
5. Print progress: `Fetched page N/total (M players so far)`.

**Relevant Context:**
- URL: `https://www.ea.com/_next/data/{build_id}/games/madden-nfl/ratings.json?page={n}`
- No auth token required — endpoint is public.
- `?page=1` → Ja'Marr Chase first; `?page=2` → Jake Matthews first — confirmed working.

**Status:** `[ ] pending`

---

### Sub-Task 3 — Flatten player dicts to CSV rows

**Intent:** Transform nested player JSON into flat dicts matching the column schema above.

**Expected Outcomes:**
- A `flatten_player(player)` function returning a single flat dict.

**Todo List:**
1. Extract identity scalars: `player_id`, `first_name`, `last_name`, `full_name`, `age`, `height_inches`, `weight_lbs`, `college`, `years_pro`, `jersey_num`, `handedness`, `overall`.
2. Parse `birthdate` (`"M/D/YY"`) into `birth_day`, `birth_month`, `birth_year` (2-digit year: add 2000 if `<= 30`, else 1900).
3. Extract classification: `position`, `team_name`, `team_short` (last word of `team.label`), `archetype`, `iteration`.
4. Extract abilities: separate `playerAbilities` into xFactor (`type.id == "xFactor"`) → `x_factor` label, and superstar (`type.id == "superstarAbility"`) → `ability_1`…`ability_6`. Leave extras blank.
5. Flatten all stats: map EA key → CSV column name per the schema table. For `runningStyle` emit `running_style` as a string. Do not emit `long_snap_rating`, `throw_acc_rating`, `snapshot_id`, `source_url`, `draft_round`, `draft_pick`, or `draft_position` — these columns are dropped entirely.
6. Prepend `season = "m27-1"`.

**Relevant Context:**
- `runningStyle.value` is a string `"Default"`, not an integer — don't cast it.
- All 55 stat keys are present for every player (non-applicable stats get low placeholder values).
- `handedness`: `1` = right, `0` = left (integer, keep as-is).

**Status:** `[ ] pending`

---

### Sub-Task 4 — Write CSV and main entry point

**Intent:** Wire everything together into a single runnable script that produces the CSV.

**Expected Outcomes:**
- Running `python scraper/scrape.py` creates `scraper/output/madden27_ratings.csv`.
- Console output shows per-page progress and a final row count.

**Todo List:**
1. Create `scraper/scrape.py` with `main()` calling the three functions above.
2. Define `COLUMNS` list matching the full column order in the schema table (identity → classification → abilities → stats alphabetically, with M27 additions in their logical positions).
3. Create `scraper/output/` if it doesn't exist (`os.makedirs(..., exist_ok=True)`).
4. Write with `csv.DictWriter(f, fieldnames=COLUMNS, extrasaction='ignore')`.
5. Create `requirements.txt` at repo root with `requests>=2.32.0`.

**Relevant Context:**
- Output path: `scraper/output/madden27_ratings.csv`
- Column order should keep `players.csv` columns in their original positions, with M27-only additions (`archetype`, `iteration`, `handedness`, `running_style`, `ability_6`) appended at the end of their respective groups.

**Status:** `[ ] pending`

---

### Sub-Task 5 — Validate and commit

**Intent:** Confirm the CSV is complete and well-formed, then commit everything.

**Expected Outcomes:**
- Row count matches `totalItems` (~2,365).
- No duplicate `player_id` values.
- All stat columns populated for first 10 players.
- Committed to the `madden-ratings-breakdown` repo.

**Todo List:**
1. Run `python scraper/scrape.py` and verify exit 0.
2. Validate: `python -c "import csv; rows=list(csv.DictReader(open('scraper/output/madden27_ratings.csv'))); print(len(rows), rows[0].keys())"`.
3. Confirm row count ~2,365 and expected columns present.
4. Update `README.md` with usage instructions.
5. Commit `scraper/scrape.py`, `requirements.txt`, `scraper/output/madden27_ratings.csv`, and updated `README.md`.

**Status:** `[ ] pending`
