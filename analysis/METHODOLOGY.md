# Lasso OVR Methodology

## Goal

Determine which individual stat ratings contribute to a player's Overall Rating (OVR) in Madden NFL 27, and by how much — broken down by archetype. EA's OVR formula is archetype-specific (a Power Rusher DT values `block_shed` differently than a Field General QB values `throw_under_pressure`), so a separate model is fitted for each of the 37 archetypes.

---

## Why Lasso

EA's OVR formula is a **fixed linear weighted sum** of a subset of stats. Lasso regression is well-suited because:

- It performs automatic **feature selection** by shrinking irrelevant coefficients exactly to zero, recovering only the stats EA actually weights for that archetype.
- It is **interpretable** — the non-zero coefficients directly represent each stat's marginal contribution to OVR.
- It avoids overfitting via regularization, which matters for smaller archetype groups (n < 30).

An ordinary least-squares fit would also achieve near-perfect R² here (the underlying formula is deterministic and linear), but Lasso's sparsity makes the results far more readable.

---

## Data

**Source:** `scraper/output/madden27_ratings.csv` — 2,365 Madden 27 players scraped from EA's official ratings site.

**Target (y):** `overall` — each player's integer OVR rating (60–99).

**Features (X):** 53 numeric stat columns (e.g. `speed_rating`, `awareness_rating`, `throw_power_rating`). The categorical `running_style` column is excluded.

**Archetype inference:** 576 players had `null` archetype in EA's data. These were assigned using a per-position `LogisticRegression` classifier trained on the 1,789 players with known archetypes (train accuracy 96–100% per position). See `scraper/infer_archetypes.py`.

---

## Procedure

For each of the 37 archetypes independently:

### 1. Subset
Filter all players belonging to that archetype. Sample sizes range from 2 (`Receiving Back - HB`) to 197 (`Deep Threat - WR`).

### 2. Standardize features
Apply `StandardScaler` (zero mean, unit variance) to X:

$$X_s = \frac{X - \mu}{\sigma}$$

This is **critical** — raw stat values all lie in roughly the same 10–99 range but have different variances. Standardizing ensures Lasso penalizes all features on the same scale, and makes coefficients **directly comparable** across stats within an archetype: a coefficient of 2.0 means a 1-standard-deviation increase in that stat is associated with +2.0 OVR points.

### 3. Fit LassoCV
Fit `sklearn.linear_model.LassoCV` on the standardized features:

$$\hat{\beta} = \arg\min_\beta \left\| y - X_s\beta \right\|^2 + \alpha \|\beta\|_1$$

- **Alpha (regularization strength)** is chosen automatically via `cv=min(5, n)` cross-validation over a grid of values.
- `max_iter=20000` to ensure convergence.
- `random_state=42` for reproducibility.

### 4. Extract coefficients
`model.coef_` gives the fitted $\hat{\beta}$ vector on the standardized scale. Coefficients zeroed by Lasso indicate stats EA does not weight for that archetype.

---

## Interpreting Coefficients

| Coefficient | Meaning |
|-------------|---------|
| `0.0` | Lasso set this to zero — stat has no effect on OVR for this archetype |
| `+1.5` | A 1-std-dev increase in this stat → +1.5 OVR points (all else equal) |
| Larger value | Higher importance to OVR for this archetype |

Coefficients are on the **standardized** (not raw) scale. A coefficient of 2.6 for `man_cover_rating` on `Manto Man - CB` means improving that stat by one standard deviation (~10 rating points across CBs) adds approximately 2.6 OVR.

Negative coefficients from Lasso are floored to 0 in the heatmap visualization, as EA's formula does not penalize stats — small negative values are Lasso regularization artifacts from correlated features.

---

## Results Summary

| Metric | Value |
|--------|-------|
| Archetypes fitted | 37 |
| R² ≥ 0.99 | 34 of 37 |
| R² ≥ 0.94 | 36 of 37 |
| `Receiving Back - HB` | R²=0.0 (n=2, excluded from analysis) |

R² values near 1.0 confirm that EA's OVR formula is indeed a near-perfect linear weighted sum of stats — exactly what Lasso recovers.

---

## Outputs

| File | Description |
|------|-------------|
| `analysis/output/lasso_ovr_weights.csv` | Wide format — one row per archetype, one column per stat with its Lasso coefficient |
| `analysis/output/lasso_ovr_rankings.csv` | Long format — stats ranked by absolute coefficient within each archetype |
| `analysis/output/lasso_heatmap.png` | Heatmap visualization — archetypes × stats, coloured by coefficient magnitude |

---

## Limitations

- **Archetype sample sizes vary widely.** Archetypes with fewer than ~15 players (e.g. `Improviser - QB`, n=10) have perfectly fitted models (R²=1.0) but may be overfit — the recovered formula is exact but may not generalize.
- **Inferred archetypes introduce noise.** The 576 players assigned archetypes via classifier are treated identically to EA-labelled players. Misclassifications would add noise to those archetype models.
- **Correlated features.** Stats like `pass_block_rating`, `pass_block_power_rating`, and `pass_block_finesse_rating` are highly correlated. Lasso may assign the full weight to one and zero the others arbitrarily. The total combined weight is reliable; the split between correlated stats is not.
- **Coefficients are not raw OVR point changes.** A coefficient of 1.5 means +1.5 OVR per standard deviation, not per raw rating point. To convert: divide by the within-archetype standard deviation of that stat.
