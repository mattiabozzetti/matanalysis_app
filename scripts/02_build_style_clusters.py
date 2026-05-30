from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.role_utils import add_role_bucket  # noqa: E402
from src.style_clustering_config import DEFAULT_K_BY_ROLE, STYLE_CLUSTER_METRICS  # noqa: E402


def build_players_enriched_from_excel(
    excel_path: Path,
    output_path: Path,
    *,
    sheet_name: str = "Main statistics",
) -> pd.DataFrame:
    if not excel_path.exists():
        raise FileNotFoundError(
            f"Missing {excel_path}. Put 'Players Dataset.xlsx' in the project root "
            "or pass --players-excel with the correct path."
        )

    print(f"Reading Excel: {excel_path}")
    players = pd.read_excel(excel_path, sheet_name=sheet_name)

    # Minimal derived columns used elsewhere in the app.
    if {"Goals", "Assists"}.issubset(players.columns):
        players["Goals + Assists"] = (
            pd.to_numeric(players["Goals"], errors="coerce")
            + pd.to_numeric(players["Assists"], errors="coerce")
        )

    if {"xG (expected goals)", "xA"}.issubset(players.columns):
        players["xG + xA"] = (
            pd.to_numeric(players["xG (expected goals)"], errors="coerce")
            + pd.to_numeric(players["xA"], errors="coerce")
        )

    players = add_role_bucket(players)

    if "Position" in players.columns:
        players = players.loc[players["Position"].astype(str).ne("GK")].copy()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    players.to_csv(output_path, index=False, compression="gzip")
    print(f"Saved processed input: {output_path}")
    print("Role bucket counts:")
    print(players["Role bucket"].value_counts(dropna=False).to_string())

    return players


def load_or_build_players(args: argparse.Namespace) -> pd.DataFrame:
    input_path = ROOT / args.input
    if input_path.exists() and not args.rebuild_input:
        print(f"Reading processed input: {input_path}")
        players = pd.read_csv(input_path, compression="gzip", low_memory=False)
        players = add_role_bucket(players)
        if "Position" in players.columns:
            players = players.loc[players["Position"].astype(str).ne("GK")].copy()
        return players

    excel_path = ROOT / args.players_excel
    return build_players_enriched_from_excel(
        excel_path,
        input_path,
        sheet_name=args.players_sheet,
    )


def _coerce_numeric(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = frame.copy()
    for col in columns:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def _winsorize(frame: pd.DataFrame, lower_q: float, upper_q: float) -> pd.DataFrame:
    out = frame.copy()
    for col in out.columns:
        values = pd.to_numeric(out[col], errors="coerce")
        lo = values.quantile(lower_q)
        hi = values.quantile(upper_q)
        if pd.notna(lo) and pd.notna(hi) and lo < hi:
            out[col] = values.clip(lo, hi)
    return out


def _metric_coverage(frame: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    rows = []
    for metric in metrics:
        if metric not in frame.columns:
            rows.append({"metric": metric, "exists": False, "coverage": 0.0})
        else:
            coverage = pd.to_numeric(frame[metric], errors="coerce").notna().mean()
            rows.append({"metric": metric, "exists": True, "coverage": float(coverage)})
    return pd.DataFrame(rows)


def _build_preprocessor() -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", RobustScaler(quantile_range=(10.0, 90.0))),
        ]
    )


def _choose_k(
    x_scaled: np.ndarray,
    role: str,
    *,
    k_min: int,
    k_max: int,
    random_state: int,
    sample_size: int,
) -> tuple[int, pd.DataFrame]:
    n = x_scaled.shape[0]
    if n < max(k_min * 3, 30):
        k = max(2, min(DEFAULT_K_BY_ROLE.get(role, 4), max(2, n // 10)))
        return k, pd.DataFrame([{"role_bucket": role, "k": k, "silhouette": np.nan, "note": "low_n_default"}])

    rng = np.random.default_rng(random_state)
    if n > sample_size:
        idx = rng.choice(n, size=sample_size, replace=False)
        x_eval = x_scaled[idx]
    else:
        x_eval = x_scaled

    rows = []
    best_k = DEFAULT_K_BY_ROLE.get(role, 5)
    best_score = -np.inf

    for k in range(k_min, min(k_max, n - 1) + 1):
        model = MiniBatchKMeans(
            n_clusters=k,
            random_state=random_state,
            n_init=20,
            batch_size=4096,
            reassignment_ratio=0.01,
        )
        labels = model.fit_predict(x_scaled)

        counts = pd.Series(labels).value_counts(normalize=True)
        min_share = float(counts.min())
        penalty = 0.03 if min_share < 0.025 else 0.0

        if x_eval.shape[0] > 2:
            eval_model = MiniBatchKMeans(
                n_clusters=k,
                random_state=random_state,
                n_init=10,
                batch_size=4096,
            )
            eval_labels = eval_model.fit_predict(x_eval)
            sil = silhouette_score(x_eval, eval_labels)
        else:
            sil = np.nan

        adjusted = float(sil) - penalty if pd.notna(sil) else -np.inf
        rows.append(
            {
                "role_bucket": role,
                "k": k,
                "silhouette": None if pd.isna(sil) else float(sil),
                "min_cluster_share": min_share,
                "adjusted_score": adjusted,
                "note": "tiny_cluster_penalty" if penalty else "",
            }
        )

        if adjusted > best_score:
            best_score = adjusted
            best_k = k

    return int(best_k), pd.DataFrame(rows)


def _cluster_role(
    role_df: pd.DataFrame,
    role: str,
    metrics: list[str],
    *,
    k: int,
    random_state: int,
    lower_q: float,
    upper_q: float,
) -> dict[str, Any]:
    x_raw = role_df[metrics].apply(pd.to_numeric, errors="coerce")
    x_winsor = _winsorize(x_raw, lower_q, upper_q)

    preprocessor = _build_preprocessor()
    x_scaled = preprocessor.fit_transform(x_winsor)

    model = MiniBatchKMeans(
        n_clusters=k,
        random_state=random_state,
        n_init=50,
        batch_size=4096,
        reassignment_ratio=0.01,
    )
    raw_labels = model.fit_predict(x_scaled)

    counts = pd.Series(raw_labels).value_counts().sort_values(ascending=False)
    ordered_labels = counts.index.tolist()
    label_map = {old_label: f"{role}_C{i+1:02d}" for i, old_label in enumerate(ordered_labels)}
    cluster_ids = pd.Series(raw_labels, index=role_df.index).map(label_map)

    centroid_lookup = {label_map[i]: model.cluster_centers_[i] for i in range(k)}
    distances = []
    for row, cluster_id in zip(x_scaled, cluster_ids):
        distances.append(float(np.linalg.norm(row - centroid_lookup[cluster_id])))
    distance_s = pd.Series(distances, index=role_df.index)

    confidence = pd.Series(index=role_df.index, dtype=float)
    for cluster_id, idx in cluster_ids.groupby(cluster_ids).groups.items():
        dist_cluster = distance_s.loc[idx]
        pct = dist_cluster.rank(pct=True, method="average") * 100
        confidence.loc[idx] = (100 - pct).clip(0, 100)

    if x_scaled.shape[1] >= 2 and x_scaled.shape[0] >= 3:
        coords = PCA(n_components=2, random_state=random_state).fit_transform(x_scaled)
    else:
        coords = np.full((x_scaled.shape[0], 2), np.nan)

    return {
        "cluster_ids": cluster_ids,
        "distance": distance_s,
        "confidence": confidence,
        "coords": coords,
    }


def _representative_players(
    role_df: pd.DataFrame,
    cluster_ids: pd.Series,
    distances: pd.Series,
    cluster_id: str,
    n: int = 8,
) -> str:
    idx = cluster_ids[cluster_ids.eq(cluster_id)].index
    subset = role_df.loc[idx].copy()
    subset["_distance"] = distances.loc[idx]
    subset = subset.sort_values("_distance", ascending=True).head(n)

    names = []
    for _, row in subset.iterrows():
        player = str(row.get("Player", "Unknown"))
        team = str(row.get("Team", ""))
        league = str(row.get("League", ""))
        names.append(f"{player} ({team}, {league})")
    return " | ".join(names)


def _profile_clusters(
    role_df: pd.DataFrame,
    role: str,
    metrics: list[str],
    cluster_ids: pd.Series,
    distances: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    role_numeric = role_df[metrics].apply(pd.to_numeric, errors="coerce")
    role_median = role_numeric.median()
    role_sd = role_numeric.std(ddof=0).replace(0, np.nan)

    cluster_rows = []
    metric_rows = []

    for cluster_id in sorted(cluster_ids.dropna().unique()):
        idx = cluster_ids[cluster_ids.eq(cluster_id)].index
        cluster = role_df.loc[idx]
        numeric = role_numeric.loc[idx]

        diffs = numeric.median() - role_median
        z = (diffs / role_sd).replace([np.inf, -np.inf], np.nan)

        high = z.dropna().sort_values(ascending=False).head(5)
        low = z.dropna().sort_values(ascending=True).head(5)
        high_text = ", ".join([f"+{m}" for m in high.index])
        low_text = ", ".join([f"-{m}" for m in low.index])

        cluster_rows.append(
            {
                "role_bucket": role,
                "style_cluster_id": cluster_id,
                "style_cluster_name": f"Unlabeled {cluster_id}",
                "n_players": int(len(cluster)),
                "median_age": float(pd.to_numeric(cluster.get("Age"), errors="coerce").median()) if "Age" in cluster else np.nan,
                "median_minutes": float(pd.to_numeric(cluster.get("Minutes played"), errors="coerce").median()) if "Minutes played" in cluster else np.nan,
                "top_leagues": ", ".join(cluster.get("League", pd.Series(dtype=str)).astype(str).value_counts().head(5).index.tolist()),
                "representative_players": _representative_players(role_df, cluster_ids, distances, cluster_id),
                "distinctive_high": high_text,
                "distinctive_low": low_text,
            }
        )

        for metric in metrics:
            cm = numeric[metric].median()
            rm = role_median.get(metric, np.nan)
            metric_rows.append(
                {
                    "role_bucket": role,
                    "style_cluster_id": cluster_id,
                    "metric": metric,
                    "cluster_median": None if pd.isna(cm) else float(cm),
                    "role_median": None if pd.isna(rm) else float(rm),
                    "difference": None if pd.isna(cm) or pd.isna(rm) else float(cm - rm),
                    "z_difference": None if pd.isna(z.get(metric, np.nan)) else float(z[metric]),
                    "coverage": float(numeric[metric].notna().mean()),
                }
            )

    return pd.DataFrame(cluster_rows), pd.DataFrame(metric_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build offline role-specific playing-style clusters.")
    parser.add_argument("--input", default="data/processed/players_enriched.csv.gz")
    parser.add_argument("--players-excel", default="Players Dataset.xlsx")
    parser.add_argument("--players-sheet", default="Main statistics")
    parser.add_argument("--rebuild-input", action="store_true", help="Rebuild players_enriched.csv.gz from Players Dataset.xlsx.")
    parser.add_argument("--output-dir", default="data/processed")
    parser.add_argument("--min-minutes", type=int, default=600)
    parser.add_argument("--min-role-n", type=int, default=120)
    parser.add_argument("--min-metric-coverage", type=float, default=0.55)
    parser.add_argument("--k-min", type=int, default=3)
    parser.add_argument("--k-max", type=int, default=8)
    parser.add_argument("--fixed-k", action="store_true", help="Use DEFAULT_K_BY_ROLE instead of choosing k by silhouette.")
    parser.add_argument("--sample-size", type=int, default=5000)
    parser.add_argument("--lower-q", type=float, default=0.01)
    parser.add_argument("--upper-q", type=float, default=0.99)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    players = load_or_build_players(args)
    players = add_role_bucket(players)
    players = players.loc[players["Role bucket"].isin(STYLE_CLUSTER_METRICS.keys())].copy()

    if "Minutes played" not in players.columns:
        raise ValueError("Missing required column: Minutes played")

    players["Minutes played"] = pd.to_numeric(players["Minutes played"], errors="coerce")
    eligible = players.loc[players["Minutes played"].fillna(0) >= args.min_minutes].copy()

    out_players = players.copy()
    out_players["style_cluster_id"] = pd.NA
    out_players["style_cluster_name"] = pd.NA
    out_players["style_cluster_role"] = pd.NA
    out_players["style_cluster_distance"] = np.nan
    out_players["style_cluster_confidence"] = np.nan
    out_players["style_cluster_x"] = np.nan
    out_players["style_cluster_y"] = np.nan
    out_players["style_cluster_min_minutes"] = args.min_minutes

    all_cluster_profiles = []
    all_metric_profiles = []
    all_diagnostics = []
    all_coverage = []

    for role, configured_metrics in STYLE_CLUSTER_METRICS.items():
        role_df = eligible.loc[eligible["Role bucket"].eq(role)].copy()

        if len(role_df) < args.min_role_n:
            all_diagnostics.append(pd.DataFrame([{
                "role_bucket": role,
                "status": "skipped_low_n",
                "n_players": int(len(role_df)),
            }]))
            continue

        coverage = _metric_coverage(role_df, configured_metrics)
        coverage["role_bucket"] = role
        all_coverage.append(coverage)

        metrics = (
            coverage.loc[coverage["exists"] & (coverage["coverage"] >= args.min_metric_coverage), "metric"]
            .astype(str)
            .tolist()
        )

        if len(metrics) < 4:
            all_diagnostics.append(pd.DataFrame([{
                "role_bucket": role,
                "status": "skipped_too_few_metrics",
                "n_players": int(len(role_df)),
                "n_metrics": len(metrics),
            }]))
            continue

        role_df = _coerce_numeric(role_df, metrics)
        x_raw = role_df[metrics]
        x_winsor = _winsorize(x_raw, args.lower_q, args.upper_q)
        preprocessor = _build_preprocessor()
        x_scaled = preprocessor.fit_transform(x_winsor)

        if args.fixed_k:
            k = DEFAULT_K_BY_ROLE.get(role, 5)
            k_diag = pd.DataFrame([{
                "role_bucket": role,
                "k": k,
                "silhouette": np.nan,
                "note": "fixed_k",
            }])
        else:
            k, k_diag = _choose_k(
                x_scaled,
                role,
                k_min=args.k_min,
                k_max=args.k_max,
                random_state=args.random_state,
                sample_size=args.sample_size,
            )

        result = _cluster_role(
            role_df,
            role,
            metrics,
            k=k,
            random_state=args.random_state,
            lower_q=args.lower_q,
            upper_q=args.upper_q,
        )

        cluster_ids = result["cluster_ids"]
        distances = result["distance"]
        confidence = result["confidence"]
        coords = result["coords"]

        out_players.loc[role_df.index, "style_cluster_id"] = cluster_ids
        out_players.loc[role_df.index, "style_cluster_name"] = cluster_ids.map(lambda x: f"Unlabeled {x}")
        out_players.loc[role_df.index, "style_cluster_role"] = role
        out_players.loc[role_df.index, "style_cluster_distance"] = distances
        out_players.loc[role_df.index, "style_cluster_confidence"] = confidence
        out_players.loc[role_df.index, "style_cluster_x"] = coords[:, 0]
        out_players.loc[role_df.index, "style_cluster_y"] = coords[:, 1]

        cluster_profile, metric_profile = _profile_clusters(
            role_df,
            role,
            metrics,
            cluster_ids,
            distances,
        )

        all_cluster_profiles.append(cluster_profile)
        all_metric_profiles.append(metric_profile)

        k_diag["selected_k"] = k
        k_diag["status"] = "clustered"
        k_diag["n_players"] = int(len(role_df))
        k_diag["n_metrics"] = int(len(metrics))
        all_diagnostics.append(k_diag)

        print(f"{role}: n={len(role_df)} metrics={len(metrics)} k={k}")

    cluster_profiles = pd.concat(all_cluster_profiles, ignore_index=True) if all_cluster_profiles else pd.DataFrame()
    metric_profiles = pd.concat(all_metric_profiles, ignore_index=True) if all_metric_profiles else pd.DataFrame()
    diagnostics = pd.concat(all_diagnostics, ignore_index=True) if all_diagnostics else pd.DataFrame()
    coverage_df = pd.concat(all_coverage, ignore_index=True) if all_coverage else pd.DataFrame()

    players_out = output_dir / "players_enriched_with_clusters.csv.gz"
    clusters_out = output_dir / "style_cluster_profiles.csv"
    metrics_out = output_dir / "style_cluster_metric_profiles.csv"
    diagnostics_out = output_dir / "style_cluster_diagnostics.csv"
    coverage_out = output_dir / "style_cluster_metric_coverage.csv"
    config_out = output_dir / "style_cluster_config.json"

    out_players.to_csv(players_out, index=False, compression="gzip")
    cluster_profiles.to_csv(clusters_out, index=False)
    metric_profiles.to_csv(metrics_out, index=False)
    diagnostics.to_csv(diagnostics_out, index=False)
    coverage_df.to_csv(coverage_out, index=False)

    config = {
        "input": args.input,
        "players_excel": args.players_excel,
        "min_minutes": args.min_minutes,
        "min_role_n": args.min_role_n,
        "min_metric_coverage": args.min_metric_coverage,
        "k_min": args.k_min,
        "k_max": args.k_max,
        "fixed_k": args.fixed_k,
        "random_state": args.random_state,
        "metrics_by_role": STYLE_CLUSTER_METRICS,
        "outputs": {
            "players": str(players_out.relative_to(ROOT)),
            "cluster_profiles": str(clusters_out.relative_to(ROOT)),
            "metric_profiles": str(metrics_out.relative_to(ROOT)),
            "diagnostics": str(diagnostics_out.relative_to(ROOT)),
            "metric_coverage": str(coverage_out.relative_to(ROOT)),
        },
    }
    config_out.write_text(json.dumps(config, indent=2, ensure_ascii=False))

    print("\nSaved:")
    for path in [players_out, clusters_out, metrics_out, diagnostics_out, coverage_out, config_out]:
        print(f"- {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
