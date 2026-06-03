# MammalWeb Threshold Analysis

Master's dissertation project investigating MegaDetector confidence thresholds for filtering human images in MammalWeb datasets.

Focus areas:
- Threshold analysis
- Precision and recall
- Privacy/safeguarding implications
- False positive and false negative trade-offs

## Safe database configuration

The MammalWeb database appears to be accessed through phpMyAdmin, so this workflow assumes a MySQL/MariaDB database using SQLAlchemy with the `pymysql` driver.

1. Install the Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Copy the example environment file locally:

   ```bash
   cp .env.example .env
   ```

3. Add the real database connection URL to `.env` only:

   ```text
   MAMMALWEB_DATABASE_URL=mysql+pymysql://username:password@host:3306/database_name
   ```

Do not commit `.env`, database passwords, exported tables, or sensitive image metadata. The `.gitignore` file is set up to ignore `.env` and local data/output folders. The query utilities in `src/mammalweb_db/queries.py` are intended for read-only `SELECT` queries during exploratory analysis.
