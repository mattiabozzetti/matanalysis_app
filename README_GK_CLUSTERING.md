# GK Style Clustering

Questo pacchetto aggiunge il clustering offline dei portieri.

## Installazione

Dalla cartella:

```bash
cd "$HOME/Desktop/Football Analysis_2"
source .venv/bin/activate
pip install -r requirements-clustering.txt
```

## Run consigliato

```bash
python scripts/03_build_gk_style_clusters.py --rebuild-input --min-minutes 900 --k-min 3 --k-max 7
```

Versione più larga:

```bash
python scripts/03_build_gk_style_clusters.py --rebuild-input --min-minutes 600 --k-min 3 --k-max 7
```

## Output

```text
data/processed/gk_enriched.csv.gz
data/processed/gk_enriched_with_clusters.csv.gz
data/processed/gk_style_cluster_profiles.csv
data/processed/gk_style_cluster_metric_profiles.csv
data/processed/gk_style_cluster_diagnostics.csv
data/processed/gk_style_cluster_metric_coverage.csv
data/processed/gk_style_cluster_config.json
```

Carica qui:

```text
gk_style_cluster_profiles.csv
gk_style_cluster_metric_profiles.csv
gk_style_cluster_diagnostics.csv
```

Poi nominiamo i cluster in stile Football Manager.
