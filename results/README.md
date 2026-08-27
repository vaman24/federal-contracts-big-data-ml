# Verified model results

The CSV files in this directory were transcribed from the retained outputs of the executed model notebooks:

- `offers_model_metrics.csv` - 2023 validation and 2024 test metrics for four offer-count regression models
- `award_value_model_metrics.csv` - 2023 validation metrics and the selected model's 2024 test metrics

The primary offer-count experiment selected Decision Tree using 2023 validation MAE. On 1,656,042 target-valid 2024 records, it achieved MAE 10.6024, RMSE 62.1229, R² 0.9338, and log-RMSE 0.5949.

The secondary award-value experiment produced a 2024 test R² of only 0.0016. This negative result is retained because it accurately shows that the selected feature set did not explain award-value variance sufficiently.

Cloud model directories, full predictions, feature vectors, and source datasets are intentionally excluded.
