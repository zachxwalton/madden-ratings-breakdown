"""
Fit a LassoCV regression per archetype to determine which individual stat
ratings contribute to overall rating (OVR), and by how much.

Outputs:
  analysis/output/lasso_ovr_weights.csv   — wide: one row per archetype, coef per stat
  analysis/output/lasso_ovr_rankings.csv  — long: archetype | rank | stat | coefficient
"""
import csv
import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler

INPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "scraper", "output", "madden27_ratings.csv"
)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

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


def main() -> None:
    df = pd.read_csv(INPUT_PATH)

    # Cast stat cols and target to numeric
    for col in STAT_COLS + ["overall"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop any remaining NaNs in features or target
    df = df.dropna(subset=STAT_COLS + ["overall"])

    # Exclude blank archetypes (should be 0 after infer_archetypes.py)
    df = df[df["archetype"].notna() & (df["archetype"] != "")]

    archetypes = sorted(df["archetype"].unique())
    print(f"Fitting Lasso for {len(archetypes)} archetypes across {len(df)} players\n")

    weight_rows = []   # one dict per archetype → wide CSV
    ranking_rows = []  # one dict per (archetype, stat) → long CSV

    for arch in archetypes:
        sub = df[df["archetype"] == arch]
        n = len(sub)
        X = sub[STAT_COLS].values
        y = sub["overall"].values

        scaler = StandardScaler()
        X_s = scaler.fit_transform(X)

        # Use min(5, n) folds to handle small archetypes safely
        folds = min(5, n)
        model = LassoCV(cv=folds, max_iter=20000, random_state=42, n_jobs=-1)
        model.fit(X_s, y)

        r2 = model.score(X_s, y)
        nonzero = int(np.sum(model.coef_ != 0))

        print(
            f"  {arch:<35s}  n={n:4d}  alpha={model.alpha_:.4f}  "
            f"R²={r2:.4f}  nonzero={nonzero}"
        )

        # --- Wide row ---
        coef_dict = dict(zip(STAT_COLS, model.coef_))
        weight_row = {
            "archetype": arch,
            "n_players": n,
            "alpha": round(model.alpha_, 6),
            "r2": round(r2, 6),
            "nonzero_coefs": nonzero,
            **{col: round(coef_dict[col], 6) for col in STAT_COLS},
        }
        weight_rows.append(weight_row)

        # --- Long rows (ranked by abs coefficient, zeros excluded) ---
        ranked = sorted(
            [(col, coef_dict[col]) for col in STAT_COLS if coef_dict[col] != 0],
            key=lambda x: abs(x[1]),
            reverse=True,
        )
        for rank, (stat, coef) in enumerate(ranked, start=1):
            ranking_rows.append({
                "archetype": arch,
                "rank": rank,
                "stat": stat,
                "coefficient": round(coef, 6),
                "abs_coefficient": round(abs(coef), 6),
            })

    # --- Write outputs ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    weights_path = os.path.join(OUTPUT_DIR, "lasso_ovr_weights.csv")
    weights_cols = ["archetype", "n_players", "alpha", "r2", "nonzero_coefs"] + STAT_COLS
    with open(weights_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=weights_cols)
        writer.writeheader()
        writer.writerows(weight_rows)

    rankings_path = os.path.join(OUTPUT_DIR, "lasso_ovr_rankings.csv")
    rankings_cols = ["archetype", "rank", "stat", "coefficient", "abs_coefficient"]
    with open(rankings_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rankings_cols)
        writer.writeheader()
        writer.writerows(ranking_rows)

    print(f"\nWrote {len(weight_rows)} archetypes to {weights_path}")
    print(f"Wrote {len(ranking_rows)} stat entries  to {rankings_path}")

    # --- Print top-5 stats for 3 largest archetypes ---
    top3 = sorted(weight_rows, key=lambda r: -r["n_players"])[:3]
    print("\n=== Top-5 contributing stats for 3 largest archetypes ===")
    for wr in top3:
        arch = wr["archetype"]
        top5 = sorted(
            [(col, wr[col]) for col in STAT_COLS if wr[col] != 0],
            key=lambda x: abs(x[1]),
            reverse=True,
        )[:5]
        print(f"\n  {arch} (n={wr['n_players']}, R²={wr['r2']:.4f})")
        for stat, coef in top5:
            print(f"    {stat:<40s} {coef:+.4f}")


if __name__ == "__main__":
    main()
