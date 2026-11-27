#!/usr/bin/env python3
"""Aggregate-only single-feature ARI checks against frozen consensus labels.

This script reads existing frozen assignment files without modifying them. It
writes only aggregate CSV, JSON, and Markdown outputs beside this script.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
N_STARTS = 300
SEED_OFFSET = 91_000


@dataclass
class FeatureSpec:
    name: str
    feature_type: str
    values: pd.Series
    theoretical_range: Optional[float] = None
    categorical: bool = False


@dataclass
class ModelSpec:
    model: str
    group: str
    k: int
    base_seed: int
    frozen_labels: pd.Series
    features: list[FeatureSpec]


def fit_kmedoids(
    distance: np.ndarray,
    k: int,
    n_init: int = N_STARTS,
    max_iter: int = 150,
    random_state: int = 0,
) -> dict[str, np.ndarray | float]:
    """Procedure copied from script 21, including deterministic tie-breaking."""
    rng = np.random.default_rng(random_state)
    n = len(distance)
    best = None
    for _ in range(n_init):
        medoids = np.sort(rng.choice(n, size=k, replace=False))
        for _ in range(max_iter):
            labels_k = np.argmin(distance[:, medoids], axis=1)
            updated = medoids.copy()
            for cluster in range(k):
                members = np.flatnonzero(labels_k == cluster)
                if len(members) == 0:
                    nearest = distance[:, medoids].min(axis=1)
                    available = np.setdiff1d(
                        np.argsort(nearest)[::-1], updated
                    )
                    updated[cluster] = available[0]
                else:
                    within = distance[np.ix_(members, members)]
                    updated[cluster] = members[np.argmin(within.sum(axis=1))]
            if np.array_equal(updated, medoids):
                break
            medoids = updated
        labels_k = np.argmin(distance[:, medoids], axis=1)
        loss = float(distance[np.arange(n), medoids[labels_k]].sum())
        candidate = (loss, tuple(medoids.tolist()), medoids.copy(), labels_k.copy())
        if best is None or candidate[:2] < best[:2]:
            best = candidate
    if best is None:
        raise RuntimeError("K-medoids did not produce a solution")
    return {"labels": best[3], "medoids": best[2], "loss": best[0]}


def single_feature_gower(feature: FeatureSpec) -> tuple[np.ndarray, np.ndarray]:
    """Build the model-specific, missing-aware Gower distance for one feature."""
    if feature.feature_type in {"nominal", "binary"}:
        series = feature.values.astype("string")
        observed = series.notna().to_numpy()
        values = series.fillna("__MISSING__").to_numpy(dtype=str)
        difference = (values[:, None] != values[None, :]).astype(float)
    else:
        numeric = pd.to_numeric(feature.values, errors="coerce")
        observed = numeric.notna().to_numpy()
        values = numeric.fillna(0).to_numpy(dtype=float)
        if feature.feature_type == "ordinal_with_unknown":
            unknown = values < 0
            both_unknown = unknown[:, None] & unknown[None, :]
            one_unknown = unknown[:, None] ^ unknown[None, :]
            difference = np.abs(values[:, None] - values[None, :])
            difference = np.where(both_unknown, 0.0, difference)
            difference = np.where(one_unknown, 1.0, difference)
        else:
            difference = np.abs(values[:, None] - values[None, :])
            if feature.theoretical_range is not None:
                difference = difference / feature.theoretical_range

    pair_observed = observed[:, None] & observed[None, :]
    distance = np.where(pair_observed, difference, 0.0)
    np.fill_diagonal(distance, 0.0)
    return distance, observed


def load_models() -> list[ModelSpec]:
    motivation = pd.read_csv(
        ROOT
        / "outputs/branch_d_motivation_consensus/motivation_consensus_assignments.csv"
    )
    economic = pd.read_csv(
        ROOT
        / "outputs/branch_d_economic_resources_clusters/economic_consensus_assignments.csv"
    )
    educational = pd.read_csv(
        ROOT
        / "outputs/branch_d_educational_cultural_capital_clusters/educational_cultural_consensus_assignments.csv"
    )
    employment = pd.read_csv(
        ROOT
        / "outputs/branch_f_employment_security_clusters/employment_security_consensus_assignments.csv"
    )

    security_code = pd.to_numeric(
        employment["job_security_12months__value"], errors="coerce"
    )
    formality_code = pd.to_numeric(
        employment["sector_formality__value"], errors="coerce"
    )

    models = [
        ModelSpec(
            model="Students: study motivation",
            group="D",
            k=3,
            base_seed=20_260_823,
            frozen_labels=motivation["consensus_profile_id"],
            features=[
                FeatureSpec(
                    "study_motivation_type",
                    "ordinal",
                    motivation["study_motivation_type__code"],
                    theoretical_range=4.0,
                ),
                FeatureSpec(
                    "autonomy_in_study",
                    "ordinal",
                    motivation["autonomy_in_study__code"],
                    theoretical_range=3.0,
                ),
                FeatureSpec(
                    "competence_in_study_field",
                    "ordinal",
                    motivation["competence_in_study_field__code"],
                    theoretical_range=3.0,
                ),
                FeatureSpec(
                    "relatedness_at_institution",
                    "ordinal",
                    motivation["relatedness_at_institution__code"],
                    theoretical_range=3.0,
                ),
            ],
        ),
        ModelSpec(
            model="Students: economic position",
            group="D",
            k=2,
            base_seed=20_260_823,
            frozen_labels=economic["economic_profile_id"],
            features=[
                FeatureSpec(
                    "household_income_position",
                    "ordinal",
                    economic["household_income_position"],
                    theoretical_range=4.0,
                ),
                FeatureSpec(
                    "household_worker_share",
                    "continuous",
                    economic["household_worker_share"],
                    theoretical_range=1.0,
                ),
                FeatureSpec(
                    "household_unemployed_share",
                    "continuous",
                    economic["household_unemployed_share"],
                    theoretical_range=1.0,
                ),
                FeatureSpec(
                    "primary_earner_responsibility",
                    "ordinal",
                    economic["primary_earner_responsibility"],
                    theoretical_range=1.0,
                ),
                FeatureSpec(
                    "primary_income_source",
                    "nominal",
                    economic["primary_income_source"],
                    categorical=True,
                ),
                FeatureSpec(
                    "education_funding_source",
                    "nominal",
                    economic["education_funding_source"],
                    categorical=True,
                ),
            ],
        ),
        ModelSpec(
            model="Students: educational trajectory",
            group="D",
            k=4,
            base_seed=20_260_824,
            frozen_labels=educational["educational_cultural_profile_id"],
            features=[
                FeatureSpec(
                    "father_education",
                    "ordinal",
                    educational["father_education"],
                    theoretical_range=6.0,
                ),
                FeatureSpec(
                    "mother_education",
                    "ordinal",
                    educational["mother_education"],
                    theoretical_range=6.0,
                ),
                FeatureSpec(
                    "expected_education",
                    "ordinal",
                    educational["expected_education"],
                    theoretical_range=6.0,
                ),
                FeatureSpec(
                    "institution_type",
                    "nominal",
                    educational["institution_type"],
                    categorical=True,
                ),
                FeatureSpec(
                    "worked_while_studying",
                    "binary",
                    educational["worked_while_studying"],
                    categorical=True,
                ),
                FeatureSpec(
                    "re_entered_education",
                    "binary",
                    educational["re_entered_education"],
                    categorical=True,
                ),
            ],
        ),
        ModelSpec(
            model="Employed: employment security and formality",
            group="F",
            k=2,
            base_seed=20_260_827,
            frozen_labels=employment["employment_security_profile_id"],
            features=[
                FeatureSpec(
                    "contract_type",
                    "nominal",
                    employment["contract_type__response"],
                    categorical=True,
                ),
                FeatureSpec(
                    "job_security_12months",
                    "ordinal_with_unknown",
                    security_code.map({1: 1.0, 2: 0.5, 3: 0.0, 4: -1.0}),
                ),
                FeatureSpec(
                    "sector_formality",
                    "ordinal",
                    formality_code.map({1: 1.0, 2: 2 / 3, 3: 1 / 3, 5: 0.0}),
                    theoretical_range=1.0,
                ),
            ],
        ),
    ]

    expected_n = {
        "Students: study motivation": 191,
        "Students: economic position": 191,
        "Students: educational trajectory": 191,
        "Employed: employment security and formality": 81,
    }
    for model in models:
        labels = pd.to_numeric(model.frozen_labels, errors="raise").astype(int)
        if len(labels) != expected_n[model.model]:
            raise AssertionError(f"Unexpected cohort size for {model.model}")
        if labels.nunique() != model.k:
            raise AssertionError(f"Unexpected frozen k for {model.model}")
        for feature in model.features:
            if len(feature.values) != len(labels):
                raise AssertionError(
                    f"Feature length mismatch: {model.model} / {feature.name}"
                )
    return models


def raw_category_ari(
    labels: np.ndarray, feature: FeatureSpec
) -> tuple[Optional[float], Optional[int]]:
    if feature.feature_type == "continuous":
        return None, None
    raw = feature.values.astype("string")
    observed = raw.notna().to_numpy()
    if observed.sum() == 0:
        return None, 0
    ari = adjusted_rand_score(labels[observed], raw[observed].astype(str).to_numpy())
    return float(ari), int(observed.sum())


def run() -> tuple[pd.DataFrame, list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []

    for model in load_models():
        labels = pd.to_numeric(model.frozen_labels, errors="raise").astype(int).to_numpy()
        model_rows = []
        for feature_index, feature in enumerate(model.features):
            seed = model.base_seed + SEED_OFFSET + feature_index
            distance, observed = single_feature_gower(feature)
            fit = fit_kmedoids(
                distance,
                model.k,
                n_init=N_STARTS,
                max_iter=150,
                random_state=seed,
            )
            ari = float(adjusted_rand_score(labels, fit["labels"]))
            category_ari, category_n = raw_category_ari(labels, feature)
            row = {
                "model": model.model,
                "group": model.group,
                "k": model.k,
                "feature": feature.name,
                "feature_type": feature.feature_type,
                "n_total": len(labels),
                "n_observed": int(observed.sum()),
                "n_starts": N_STARTS,
                "seed": seed,
                "single_feature_kmedoids_ari": ari,
                "raw_category_ari": category_ari,
                "raw_category_n": category_n,
                "kmedoids_flag_ge_0_80": bool(ari >= 0.80),
                "raw_category_flag_ge_0_80": bool(
                    category_ari is not None and category_ari >= 0.80
                ),
            }
            rows.append(row)
            model_rows.append(row)

        max_ari = max(float(row["single_feature_kmedoids_ari"]) for row in model_rows)
        max_features = [
            str(row["feature"])
            for row in model_rows
            if np.isclose(
                float(row["single_feature_kmedoids_ari"]),
                max_ari,
                rtol=0,
                atol=1e-12,
            )
        ]
        flagged = [
            str(row["feature"])
            for row in model_rows
            if bool(row["kmedoids_flag_ge_0_80"])
        ]
        raw_flagged = [
            str(row["feature"])
            for row in model_rows
            if bool(row["raw_category_flag_ge_0_80"])
        ]
        summaries.append(
            {
                "model": model.model,
                "group": model.group,
                "k": model.k,
                "n": len(labels),
                "maximum_single_feature_ari": max_ari,
                "maximum_feature": max_features,
                "maximum_below_0_90": bool(max_ari < 0.90),
                "kmedoids_features_ge_0_80": flagged,
                "raw_category_features_ge_0_80": raw_flagged,
            }
        )

    return pd.DataFrame(rows), summaries


def nullable_records(frame: pd.DataFrame) -> list[dict[str, object]]:
    records = frame.astype(object).where(pd.notna(frame), None).to_dict("records")
    return records


def write_report(results: pd.DataFrame, summaries: list[dict[str, object]]) -> None:
    lines = [
        "# Single-feature ARI check",
        "",
        "Aggregate-only results against frozen final consensus labels. Each",
        "single-feature partition uses the model's documented feature encoding,",
        "missing-aware one-feature Gower distance, 300 K-medoids starts, and seed",
        "`model base seed + 91000 + feature index`, matching the procedure in",
        "`21_branch_f_household_economic_resources_clustering.py`.",
        "",
        "Raw-category ARI is reported for ordinal, nominal, and binary survey",
        "features and uses the observed subset; missing values remain unavailable.",
    ]

    for summary in summaries:
        model = str(summary["model"])
        subset = results.loc[results["model"].eq(model)]
        lines.extend(
            [
                "",
                f"## {model}",
                "",
                f"n = {summary['n']}; k = {summary['k']}.",
                "",
                "| Feature | Type | Observed n | Seed | K-medoids ARI | Raw-category ARI | Flag |",
                "|---|---|---:|---:|---:|---:|---|",
            ]
        )
        for row in subset.itertuples(index=False):
            raw_text = (
                "–"
                if pd.isna(row.raw_category_ari)
                else f"{row.raw_category_ari:.6f} (n={int(row.raw_category_n)})"
            )
            flags = []
            if row.kmedoids_flag_ge_0_80:
                flags.append("**K-medoids ≥ 0.80**")
            if row.raw_category_flag_ge_0_80:
                flags.append("**raw category ≥ 0.80**")
            flag = "; ".join(flags) if flags else "–"
            lines.append(
                f"| `{row.feature}` | {row.feature_type} | {row.n_observed} | "
                f"{row.seed} | {row.single_feature_kmedoids_ari:.6f} | "
                f"{raw_text} | {flag} |"
            )
        max_features = ", ".join(
            f"`{feature}`" for feature in summary["maximum_feature"]
        )
        flagged = summary["kmedoids_features_ge_0_80"]
        flagged_text = (
            ", ".join(f"`{feature}`" for feature in flagged) if flagged else "none"
        )
        raw_flagged = summary["raw_category_features_ge_0_80"]
        raw_flagged_text = (
            ", ".join(f"`{feature}`" for feature in raw_flagged)
            if raw_flagged
            else "none"
        )
        lines.extend(
            [
                "",
                f"Maximum ARI: **{summary['maximum_single_feature_ari']:.6f}** "
                f"from {max_features}.",
                f"Maximum < 0.90: **{summary['maximum_below_0_90']}**.",
                f"K-medoids features with ARI ≥ 0.80: **{flagged_text}**.",
                f"Raw-category features with ARI ≥ 0.80: **{raw_flagged_text}**.",
            ]
        )

    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    results, summaries = run()
    results.to_csv(OUT / "single_feature_ari.csv", index=False)
    payload = {
        "method": {
            "n_starts": N_STARTS,
            "max_iter": 150,
            "seed_rule": "model base seed + 91000 + zero-based feature index",
            "comparison": "adjusted Rand index versus frozen consensus labels",
            "raw_category_missing_policy": "observed subset only",
        },
        "results": nullable_records(results),
        "model_summaries": summaries,
    }
    (OUT / "summary.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    write_report(results, summaries)
    print(json.dumps({"model_summaries": summaries}, indent=2))


if __name__ == "__main__":
    main()
