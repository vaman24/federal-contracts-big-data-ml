# Reproducibility Guide

This repository publishes reviewable evidence from the completed academic project. The full source dataset, derived Parquet layers, Spark feature vectors, and trained model directories are intentionally excluded because they are multi-gigabyte cloud artifacts.

## Recorded execution environment

- GCP Dataproc image: `2.3.34`
- Notebook kernel: PySpark
- Python version recorded in notebook metadata: `3.11.14`
- Storage: Google Cloud Storage
- Processing: Spark SQL, PySpark, and Spark ML
- Data format: Parquet

The original workload contained approximately 26.8 million federal-contract records covering fiscal years 2009-2024.

## Portfolio integrity check

The automated check uses only the Python standard library; it does not download data or start Spark.

```bash
python scripts/validate_notebooks.py
```

It verifies that:

- all five expected notebook exports are present and valid JSON;
- Python code cells parse successfully;
- committed notebook outputs contain no execution errors or Spark-monitor payloads;
- common credential formats are absent;
- the published offer and award-value result tables contain the verified selected-model rows.

The same validation runs on pushes and pull requests through GitHub Actions.

## Preparing a full cloud rerun

1. Provision a GCP project, GCS bucket, and Dataproc environment compatible with the recorded runtime.
2. Create a Python 3.11 environment for local review, if required:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and replace every placeholder with your own project, region, bucket, and GCS prefixes.
4. Upload the federal-contract Parquet source to the configured raw prefix.
5. Adapt the path-configuration cells in the exported notebooks to the new prefixes.
6. Run the notebooks in their numbered order and write each derived stage to a new GCS prefix.
7. Compare regenerated evaluation tables with the committed CSV files in `results/`.

## Temporal evaluation contract

| Split | Years | Purpose |
|---|---|---|
| Training | 2009-2022 | Fit preprocessing pipelines and regressors |
| Validation | 2023 | Select the model and configuration |
| Test | 2024 | Perform the final held-out evaluation |

The automated integrity check validates the exported evidence; it does not claim to reproduce a 26.8-million-row Spark run without the external dataset and cloud artifacts.
