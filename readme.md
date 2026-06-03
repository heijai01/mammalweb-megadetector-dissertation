# MammalWeb Threshold Analysis

Master's dissertation project investigating MegaDetector confidence thresholds for filtering human images in MammalWeb datasets.

Focus areas:
- Threshold analysis
- Precision and recall
- Privacy/safeguarding implications
- False positive and false negative trade-offs

## Current workflow

Direct Python access to the remote MammalWeb database may be blocked by network or security restrictions. For now, this repository uses a simpler manual-export workflow:

```text
phpMyAdmin -> SQL query -> export CSV -> local pandas analysis -> threshold evaluation and visualisation
```

## Using CSV exports safely

1. In phpMyAdmin, run a focused SQL query that returns only the columns needed for analysis.
2. Export the result as a CSV file.
3. Place the CSV file in `data/raw/` on your local machine.
4. Use the notebook `notebooks/01_database_export_exploration.ipynb` to load, inspect, and analyse the export.
5. Save cleaned or derived CSV files to `data/processed/` if needed.

Do not commit real exported data if it may contain sensitive information, human image metadata, locations, filenames, or other identifiable details. The `.gitignore` file keeps `data/raw/*` and `data/processed/*` ignored, except for `.gitkeep` placeholders.

## Setup

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

The main helper modules are:

- `src/mammalweb_analysis/io.py` for loading exported CSV files.
- `src/mammalweb_analysis/thresholds.py` for MegaDetector threshold metrics.

## Suggested CSV columns

The exact database schema may vary, so adapt the names in the notebook. Useful exports for threshold analysis usually include:

- an image or record identifier
- MegaDetector human confidence score
- ground-truth human label or review outcome
- optional animal/wildlife label
- optional human-risk category, if available

Keep exports small and purposeful while developing the workflow.
