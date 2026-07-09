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



## Setup

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

The main helper modules are:

- `src/mammalweb_analysis/io.py` for loading exported CSV files.
- `src/mammalweb_analysis/thresholds.py` for MegaDetector threshold metrics.

