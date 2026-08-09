import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score

from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier

class MLService:
    @staticmethod
    def train_model(
        df: pd.DataFrame,
        target_col: str,
        feature_cols: List[str],
        model_type: str = "linear_regression",
        n_clusters: int = 3
    ) -> Dict[str, Any]:
        
        # Check basic suitability
        if target_col not in df.columns and model_type != "clustering":
            return {
                "isSuitable": False,
                "message": f"Target column '{target_col}' not found in dataset.",
                "modelType": model_type
            }

        valid_features = [c for c in feature_cols if c in df.columns and c != target_col]
        if not valid_features:
            return {
                "isSuitable": False,
                "message": "At least 1 valid feature column must be selected.",
                "modelType": model_type
            }

        cols_to_use = valid_features + ([target_col] if target_col in df.columns else [])
        ml_df = df[cols_to_use].dropna()

        if len(ml_df) < 10:
            return {
                "isSuitable": False,
                "message": f"Insufficient rows for machine learning ({len(ml_df)} rows after removing nulls). At least 10 rows required.",
                "modelType": model_type
            }

        # Fast dummy encoding
        X = pd.get_dummies(ml_df[valid_features], drop_first=True)

        if model_type == "clustering":
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            kmeans = KMeans(n_clusters=min(n_clusters, len(ml_df)), random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X_scaled)
            
            sample_res = ml_df.head(10).copy()
            sample_res["Cluster"] = clusters[:10]

            return {
                "isSuitable": True,
                "message": f"K-Means Clustering executed successfully into {n_clusters} clusters.",
                "modelType": "K-Means Clustering",
                "metrics": {
                    "inertia": round(float(kmeans.inertia_), 2),
                    "clustersCount": n_clusters,
                    "totalSamples": len(ml_df)
                },
                "featureImportance": {},
                "predictionsSample": sample_res.to_dict(orient="records")
            }

        y = ml_df[target_col]
        is_classification = (y.dtype == 'object' or str(y.dtype) == 'category' or y.nunique() <= 5)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

        if model_type in ["gradient_boosting", "hist_gb"]:
            if is_classification:
                model = HistGradientBoostingClassifier(random_state=42, max_iter=100)
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                acc = float(accuracy_score(y_test, preds))
                sample_df = pd.DataFrame({"Actual": y_test.iloc[:10], "Predicted": preds[:10]})
                return {
                    "isSuitable": True,
                    "message": "High-Speed HistGradientBoosting Classifier trained successfully.",
                    "modelType": "Gradient Boosting Classifier",
                    "targetColumn": target_col,
                    "metrics": {"Accuracy": round(acc * 100, 2)},
                    "featureImportance": {},
                    "predictionsSample": sample_df.to_dict(orient="records")
                }
            else:
                model = HistGradientBoostingRegressor(random_state=42, max_iter=100)
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                mse = float(mean_squared_error(y_test, preds))
                r2 = float(r2_score(y_test, preds))
                sample_df = pd.DataFrame({"Actual": y_test.iloc[:10], "Predicted": np.round(preds[:10], 2)})
                return {
                    "isSuitable": True,
                    "message": "High-Speed HistGradientBoosting Regressor trained successfully.",
                    "modelType": "Gradient Boosting Regressor",
                    "targetColumn": target_col,
                    "metrics": {
                        "R2_Score": round(r2, 4),
                        "MSE": round(mse, 4),
                        "RMSE": round(np.sqrt(mse), 4)
                    },
                    "featureImportance": {},
                    "predictionsSample": sample_df.to_dict(orient="records")
                }

        elif model_type == "linear_regression":
            if is_classification:
                return {
                    "isSuitable": False,
                    "message": f"Target column '{target_col}' is categorical. Linear regression requires continuous numeric targets.",
                    "modelType": model_type
                }
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            model = LinearRegression()
            model.fit(X_train_scaled, y_train)
            preds = model.predict(X_test_scaled)

            mse = float(mean_squared_error(y_test, preds))
            r2 = float(r2_score(y_test, preds))

            coef_map = {col_name: round(float(coef), 4) for col_name, coef in zip(X.columns, model.coef_)}
            sample_df = pd.DataFrame({"Actual": y_test.iloc[:10], "Predicted": np.round(preds[:10], 2)})

            return {
                "isSuitable": True,
                "message": "Linear Regression model trained with StandardScaler normalization.",
                "modelType": "Linear Regression",
                "targetColumn": target_col,
                "metrics": {
                    "R2_Score": round(r2, 4),
                    "MSE": round(mse, 4),
                    "RMSE": round(np.sqrt(mse), 4)
                },
                "featureImportance": coef_map,
                "predictionsSample": sample_df.to_dict(orient="records")
            }

        elif model_type == "random_forest":
            if is_classification:
                model = RandomForestClassifier(n_estimators=100, max_depth=12, n_jobs=-1, random_state=42)
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                acc = float(accuracy_score(y_test, preds))

                imp_map = {col: round(float(imp), 4) for col, imp in zip(X.columns, model.feature_importances_)}
                sample_df = pd.DataFrame({"Actual": y_test.iloc[:10], "Predicted": preds[:10]})

                return {
                    "isSuitable": True,
                    "message": "Multi-threaded Random Forest Classifier trained (100 Trees).",
                    "modelType": "Random Forest Classifier",
                    "targetColumn": target_col,
                    "metrics": {"Accuracy": round(acc * 100, 2)},
                    "featureImportance": imp_map,
                    "predictionsSample": sample_df.to_dict(orient="records")
                }
            else:
                model = RandomForestRegressor(n_estimators=100, max_depth=12, n_jobs=-1, random_state=42)
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                mse = float(mean_squared_error(y_test, preds))
                r2 = float(r2_score(y_test, preds))

                imp_map = {col: round(float(imp), 4) for col, imp in zip(X.columns, model.feature_importances_)}
                sample_df = pd.DataFrame({"Actual": y_test.iloc[:10], "Predicted": np.round(preds[:10], 2)})

                return {
                    "isSuitable": True,
                    "message": "Multi-threaded Random Forest Regressor trained (100 Trees).",
                    "modelType": "Random Forest Regressor",
                    "targetColumn": target_col,
                    "metrics": {
                        "R2_Score": round(r2, 4),
                        "MSE": round(mse, 4),
                        "RMSE": round(np.sqrt(mse), 4)
                    },
                    "featureImportance": imp_map,
                    "predictionsSample": sample_df.to_dict(orient="records")
                }

        return {
            "isSuitable": False,
            "message": f"Unsupported ML model type: {model_type}",
            "modelType": model_type
        }

ml_service = MLService()
