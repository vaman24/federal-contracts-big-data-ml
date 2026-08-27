# Source-module publication checklist

Reusable PySpark code should be extracted here from the completed cloud notebooks. The modules have not yet been published in this repository.

Planned modules:

- `config.py` — environment-driven GCS and dataset paths
- `validation.py` — schema and data-quality checks
- `cleaning.py` — identifiers, categories, dates, money, and target cleaning
- `features.py` — derived columns and Spark ML feature pipeline
- `train.py` — baseline and regression training
- `evaluate.py` — MAE, RMSE, residual, and feature-importance reporting

Do not hard-code cloud credentials or personal paths.
