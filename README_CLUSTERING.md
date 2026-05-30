# Style Clustering — pacchetto completo

Questo pacchetto è pensato per funzionare anche in una cartella che contiene solo:

```text
Players Dataset.xlsx
Team Dataset.xlsx
GK Dataset.xlsx
scripts/
src/
requirements-clustering.txt
```

Lo script crea automaticamente `data/processed/players_enriched.csv.gz` partendo da `Players Dataset.xlsx`, se il file non esiste già.

## Installazione

Dalla cartella:

```bash
cd "$HOME/Desktop/Football Analysis_2"
source .venv/bin/activate
pip install -r requirements-clustering.txt
```

## Run consigliato

```bash
python scripts/02_build_style_clusters.py --rebuild-input --min-minutes 600 --k-min 3 --k-max 8
```

Versione più restrittiva:

```bash
python scripts/02_build_style_clusters.py --rebuild-input --min-minutes 900 --k-min 3 --k-max 8
```

## Output

```text
data/processed/players_enriched.csv.gz
data/processed/players_enriched_with_clusters.csv.gz
data/processed/style_cluster_profiles.csv
data/processed/style_cluster_metric_profiles.csv
data/processed/style_cluster_diagnostics.csv
data/processed/style_cluster_metric_coverage.csv
data/processed/style_cluster_config.json
```

Carica poi qui:

```text
style_cluster_profiles.csv
style_cluster_metric_profiles.csv
style_cluster_diagnostics.csv
```
