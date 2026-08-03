"""
Infer missing archetypes for the 576 players where EA returned null.

Strategy: per position, train a LogisticRegression on the filled players
using all stat rating columns, then predict the blank players' archetypes.
Writes the updated CSV to scraper/output/madden27_ratings.csv in-place.
"""
import csv
import os

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

INPUT_PATH = os.path.join(os.path.dirname(__file__), "output", "madden27_ratings.csv")

STAT_COLS = [
    "accel_rating", "agility_rating", "awareness_rating", "bcv_rating",
    "block_shed_rating", "break_sack_rating", "break_tackle_rating",
    "carry_rating", "catch_rating", "change_of_direction_rating", "cit_rating",
    "finesse_moves_rating", "hit_power_rating", "impact_block_rating",
    "injury_rating", "juke_move_rating", "jump_rating", "kick_acc_rating",
    "kick_power_rating", "kick_ret_rating", "lead_block_rating",
    "man_cover_rating", "pass_block_finesse_rating", "pass_block_power_rating",
    "pass_block_rating", "play_action_rating", "play_rec_rating",
    "power_moves_rating", "press_rating", "pursuit_rating", "release_rating",
    "route_run_deep_rating", "route_run_med_rating", "route_run_short_rating",
    "run_block_finesse_rating", "run_block_power_rating", "run_block_rating",
    "spec_catch_rating", "speed_rating", "spin_move_rating", "stamina_rating",
    "stiff_arm_rating", "strength_rating", "tackle_rating",
    "throw_acc_deep_rating", "throw_acc_mid_rating", "throw_acc_short_rating",
    "throw_on_run_rating", "throw_power_rating", "throw_under_pressure_rating",
    "tough_rating", "truck_rating", "zone_cover_rating",
]


def featurize(row: dict) -> list[float]:
    return [float(row[c]) for c in STAT_COLS]


def infer_archetypes(rows: list[dict]) -> list[dict]:
    # Group by position
    positions_with_blanks = set(r["position"] for r in rows if not r["archetype"])

    for pos in sorted(positions_with_blanks):
        filled = [r for r in rows if r["position"] == pos and r["archetype"]]
        blank  = [r for r in rows if r["position"] == pos and not r["archetype"]]

        if not filled:
            print(f"  {pos}: no filled players to train on — skipping {len(blank)} blanks")
            continue

        archetypes = sorted(set(r["archetype"] for r in filled))
        X_train = [featurize(r) for r in filled]
        y_train = [r["archetype"] for r in filled]

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)

        # C=1.0, max_iter=1000; multi_class handled automatically
        clf = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
        clf.fit(X_train_s, y_train)

        # Accuracy on training set (proxy — real data is small)
        train_acc = clf.score(X_train_s, y_train)

        X_blank = scaler.transform([featurize(r) for r in blank])
        predictions = clf.predict(X_blank)

        arch_counts = {a: 0 for a in archetypes}
        for r, pred in zip(blank, predictions):
            r["archetype"] = pred
            arch_counts[pred] += 1

        print(
            f"  {pos}: trained on {len(filled)} players "
            f"(train acc={train_acc:.2%}), "
            f"inferred {len(blank)} blanks => "
            + ", ".join(f"{a}: {arch_counts[a]}" for a in archetypes)
        )

    return rows


def main() -> None:
    with open(INPUT_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    blank_before = sum(1 for r in rows if not r["archetype"])
    print(f"Players with blank archetype before: {blank_before}")

    rows = infer_archetypes(rows)

    blank_after = sum(1 for r in rows if not r["archetype"])
    print(f"Players with blank archetype after:  {blank_after}")

    with open(INPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {INPUT_PATH}")


if __name__ == "__main__":
    main()
