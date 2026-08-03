import csv
import math
import os
import re
import time

import requests

BASE_URL = "https://www.ea.com"
RATINGS_HOME = f"{BASE_URL}/games/madden-nfl/ratings"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "output", "madden27_ratings.csv")

COLUMNS = [
    "season",
    "player_id",
    "first_name",
    "last_name",
    "full_name",
    "position",
    "team_name",
    "team_short",
    "age",
    "height_inches",
    "weight_lbs",
    "college",
    "years_pro",
    "jersey_num",
    "birth_day",
    "birth_month",
    "birth_year",
    "overall",
    "archetype",
    "iteration",
    "handedness",
    "x_factor",
    "ability_1",
    "ability_2",
    "ability_3",
    "ability_4",
    "ability_5",
    "ability_6",
    "accel_rating",
    "agility_rating",
    "awareness_rating",
    "bcv_rating",
    "block_shed_rating",
    "break_sack_rating",
    "break_tackle_rating",
    "carry_rating",
    "catch_rating",
    "change_of_direction_rating",
    "cit_rating",
    "finesse_moves_rating",
    "hit_power_rating",
    "impact_block_rating",
    "injury_rating",
    "juke_move_rating",
    "jump_rating",
    "kick_acc_rating",
    "kick_power_rating",
    "kick_ret_rating",
    "lead_block_rating",
    "man_cover_rating",
    "pass_block_finesse_rating",
    "pass_block_power_rating",
    "pass_block_rating",
    "play_action_rating",
    "play_rec_rating",
    "power_moves_rating",
    "press_rating",
    "pursuit_rating",
    "release_rating",
    "route_run_deep_rating",
    "route_run_med_rating",
    "route_run_short_rating",
    "run_block_finesse_rating",
    "run_block_power_rating",
    "run_block_rating",
    "running_style",
    "spec_catch_rating",
    "speed_rating",
    "spin_move_rating",
    "stamina_rating",
    "stiff_arm_rating",
    "strength_rating",
    "tackle_rating",
    "throw_acc_deep_rating",
    "throw_acc_mid_rating",
    "throw_acc_short_rating",
    "throw_on_run_rating",
    "throw_power_rating",
    "throw_under_pressure_rating",
    "tough_rating",
    "truck_rating",
    "zone_cover_rating",
]

# EA stat key → CSV column name
STAT_MAP = {
    "acceleration":       "accel_rating",
    "agility":            "agility_rating",
    "awareness":          "awareness_rating",
    "bCVision":           "bcv_rating",
    "blockShedding":      "block_shed_rating",
    "breakSack":          "break_sack_rating",
    "breakTackle":        "break_tackle_rating",
    "carrying":           "carry_rating",
    "catching":           "catch_rating",
    "changeOfDirection":  "change_of_direction_rating",
    "catchInTraffic":     "cit_rating",
    "finesseMoves":       "finesse_moves_rating",
    "hitPower":           "hit_power_rating",
    "impactBlocking":     "impact_block_rating",
    "injury":             "injury_rating",
    "jukeMove":           "juke_move_rating",
    "jumping":            "jump_rating",
    "kickAccuracy":       "kick_acc_rating",
    "kickPower":          "kick_power_rating",
    "kickReturn":         "kick_ret_rating",
    "leadBlock":          "lead_block_rating",
    "manCoverage":        "man_cover_rating",
    "passBlockFinesse":   "pass_block_finesse_rating",
    "passBlockPower":     "pass_block_power_rating",
    "passBlock":          "pass_block_rating",
    "playAction":         "play_action_rating",
    "playRecognition":    "play_rec_rating",
    "powerMoves":         "power_moves_rating",
    "press":              "press_rating",
    "pursuit":            "pursuit_rating",
    "release":            "release_rating",
    "deepRouteRunning":   "route_run_deep_rating",
    "mediumRouteRunning": "route_run_med_rating",
    "shortRouteRunning":  "route_run_short_rating",
    "runBlockFinesse":    "run_block_finesse_rating",
    "runBlockPower":      "run_block_power_rating",
    "runBlock":           "run_block_rating",
    "runningStyle":       "running_style",
    "spectacularCatch":   "spec_catch_rating",
    "speed":              "speed_rating",
    "spinMove":           "spin_move_rating",
    "stamina":            "stamina_rating",
    "stiffArm":           "stiff_arm_rating",
    "strength":           "strength_rating",
    "tackle":             "tackle_rating",
    "throwAccuracyDeep":  "throw_acc_deep_rating",
    "throwAccuracyMid":   "throw_acc_mid_rating",
    "throwAccuracyShort": "throw_acc_short_rating",
    "throwOnTheRun":      "throw_on_run_rating",
    "throwPower":         "throw_power_rating",
    "throwUnderPressure": "throw_under_pressure_rating",
    "toughness":          "tough_rating",
    "trucking":           "truck_rating",
    "zoneCoverage":       "zone_cover_rating",
}


def get_build_id(session: requests.Session) -> str:
    resp = session.get(RATINGS_HOME, timeout=15)
    resp.raise_for_status()
    m = re.search(r"/_next/static/([^/]+)/_buildManifest\.js", resp.text)
    if not m:
        raise RuntimeError("Could not find Next.js build ID in ratings page HTML")
    return m.group(1)


def fetch_all_players(session: requests.Session, build_id: str) -> list[dict]:
    url_template = (
        f"{BASE_URL}/_next/data/{build_id}/games/madden-nfl/ratings.json?page={{page}}"
    )

    # Page 1 — determine total
    resp = session.get(url_template.format(page=1), timeout=15)
    resp.raise_for_status()
    data = resp.json()
    rating_details = data["pageProps"]["ratingDetails"]
    total = rating_details["totalItems"]
    pages = math.ceil(total / 100)
    print(f"Total players: {total} across {pages} pages")

    players = list(rating_details["items"])
    print(f"  Fetched page 1/{pages} ({len(players)} players so far)")

    for page in range(2, pages + 1):
        time.sleep(1)
        resp = session.get(url_template.format(page=page), timeout=15)
        resp.raise_for_status()
        items = resp.json()["pageProps"]["ratingDetails"]["items"]
        players.extend(items)
        print(f"  Fetched page {page}/{pages} ({len(players)} players so far)")

    # Deduplicate by id (guard against overlap)
    seen = set()
    unique = []
    for p in players:
        if p["id"] not in seen:
            seen.add(p["id"])
            unique.append(p)
    return unique


def flatten_player(player: dict) -> dict:
    # --- Birthdate parsing ---
    birth_day = birth_month = birth_year = ""
    raw_bd = player.get("birthdate", "")
    if raw_bd:
        parts = raw_bd.split("/")
        if len(parts) == 3:
            birth_month = parts[0]
            birth_day = parts[1]
            yy = int(parts[2])
            birth_year = 2000 + yy if yy <= 30 else 1900 + yy

    # --- Team short: last word of team label ---
    team_label = (player.get("team") or {}).get("label", "")
    team_short = team_label.split()[-1] if team_label else ""

    # --- Abilities ---
    x_factor = ""
    superstar = []
    for ab in player.get("playerAbilities") or []:
        ab_type = (ab.get("type") or {}).get("id", "")
        label = ab.get("label", "")
        if ab_type == "xFactor":
            x_factor = label
        elif ab_type == "superstarAbility":
            superstar.append(label)

    abilities = {f"ability_{i+1}": (superstar[i] if i < len(superstar) else "") for i in range(6)}

    # --- Stats ---
    stats_raw = player.get("stats") or {}
    stat_values = {}
    for ea_key, csv_col in STAT_MAP.items():
        entry = stats_raw.get(ea_key)
        stat_values[csv_col] = entry["value"] if entry else ""

    row = {
        "season":       "m27-1",
        "player_id":    player.get("id", ""),
        "first_name":   player.get("firstName", ""),
        "last_name":    player.get("lastName", ""),
        "full_name":    f"{player.get('firstName', '')} {player.get('lastName', '')}".strip(),
        "position":     (player.get("position") or {}).get("id", ""),
        "team_name":    team_label,
        "team_short":   team_short,
        "age":          player.get("age", ""),
        "height_inches": player.get("height", ""),
        "weight_lbs":   player.get("weight", ""),
        "college":      player.get("college", ""),
        "years_pro":    player.get("yearsPro", ""),
        "jersey_num":   player.get("jerseyNum", ""),
        "birth_day":    birth_day,
        "birth_month":  birth_month,
        "birth_year":   birth_year,
        "overall":      player.get("overallRating", ""),
        "archetype":    (player.get("archetype") or {}).get("label", ""),
        "iteration":    (player.get("iteration") or {}).get("label", ""),
        "handedness":   player.get("handedness", ""),
        "x_factor":     x_factor,
        **abilities,
        **stat_values,
    }
    return row


def main() -> None:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    print("Fetching build ID...")
    build_id = get_build_id(session)
    print(f"Build ID: {build_id}")

    players = fetch_all_players(session, build_id)
    print(f"\nCollected {len(players)} unique players")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for player in players:
            writer.writerow(flatten_player(player))

    print(f"Wrote {len(players)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
