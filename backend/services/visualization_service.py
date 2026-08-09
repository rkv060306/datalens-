import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from backend.services.profiling_service import profiling_service
from backend.services.statistics_service import statistics_service

class VisualizationService:
    @staticmethod
    def get_auto_recommendations(df: pd.DataFrame) -> List[Dict[str, Any]]:
        recommendations = []
        profile = profiling_service.profile_dataframe(df)
        cols = profile["columnProfiles"]

        num_cols = [c for c, p in cols.items() if p["detectedType"] in ["integer", "float"]]
        cat_cols = [c for c, p in cols.items() if p["detectedType"] in ["categorical", "string"]]
        date_cols = [c for c, p in cols.items() if p["detectedType"] in ["datetime"]]

        # 1. Single Numeric Column -> Histogram
        if num_cols:
            col = num_cols[0]
            series = df[col].dropna().tolist()
            recommendations.append({
                "id": f"rec-histogram-{col}",
                "title": f"Distribution of {col}",
                "chartType": "histogram",
                "xAxis": col,
                "yAxis": "Frequency",
                "plotlyData": {
                    "data": [{
                        "x": series,
                        "type": "histogram",
                        "marker": {"color": "#6366f1", "opacity": 0.8}
                    }],
                    "layout": {
                        "title": f"Histogram Distribution: {col}",
                        "xaxis": {"title": col},
                        "yaxis": {"title": "Count"},
                        "template": "plotly_dark"
                    }
                }
            })

        # 2. Date + Numeric Column -> Line Chart
        if date_cols and num_cols:
            d_col = date_cols[0]
            v_col = num_cols[0]
            ts_df = df[[d_col, v_col]].dropna().sort_values(by=d_col).head(100)
            recommendations.append({
                "id": f"rec-line-{d_col}-{v_col}",
                "title": f"{v_col} Over Time",
                "chartType": "line",
                "xAxis": d_col,
                "yAxis": v_col,
                "plotlyData": {
                    "data": [{
                        "x": [str(x) for x in ts_df[d_col]],
                        "y": [float(y) for y in ts_df[v_col]],
                        "type": "scatter",
                        "mode": "lines+markers",
                        "line": {"color": "#10b981", "width": 3}
                    }],
                    "layout": {
                        "title": f"Time-Series Trend: {v_col} vs {d_col}",
                        "xaxis": {"title": d_col},
                        "yaxis": {"title": v_col},
                        "template": "plotly_dark"
                    }
                }
            })

        # 3. Categorical + Numeric -> Bar Chart
        if cat_cols and num_cols:
            c_col = cat_cols[0]
            v_col = num_cols[0]
            grouped = df.groupby(c_col)[v_col].mean().reset_index().head(10)
            recommendations.append({
                "id": f"rec-bar-{c_col}-{v_col}",
                "title": f"Average {v_col} by {c_col}",
                "chartType": "bar",
                "xAxis": c_col,
                "yAxis": v_col,
                "plotlyData": {
                    "data": [{
                        "x": [str(x) for x in grouped[c_col]],
                        "y": [float(y) for y in grouped[v_col]],
                        "type": "bar",
                        "marker": {"color": "#8b5cf6"}
                    }],
                    "layout": {
                        "title": f"Mean {v_col} across {c_col}",
                        "xaxis": {"title": c_col},
                        "yaxis": {"title": f"Mean {v_col}"},
                        "template": "plotly_dark"
                    }
                }
            })

        # 4. Two Numeric Columns -> Scatter Plot
        if len(num_cols) >= 2:
            x_col, y_col = num_cols[0], num_cols[1]
            sample_df = df[[x_col, y_col]].dropna().head(200)
            recommendations.append({
                "id": f"rec-scatter-{x_col}-{y_col}",
                "title": f"{y_col} vs {x_col}",
                "chartType": "scatter",
                "xAxis": x_col,
                "yAxis": y_col,
                "plotlyData": {
                    "data": [{
                        "x": [float(x) for x in sample_df[x_col]],
                        "y": [float(y) for y in sample_df[y_col]],
                        "mode": "markers",
                        "type": "scatter",
                        "marker": {"color": "#ec4899", "size": 8, "opacity": 0.7}
                    }],
                    "layout": {
                        "title": f"Scatter Relationship: {y_col} vs {x_col}",
                        "xaxis": {"title": x_col},
                        "yaxis": {"title": y_col},
                        "template": "plotly_dark"
                    }
                }
            })

        # 5. Correlation Heatmap
        if len(num_cols) >= 2:
            corr_data = statistics_service.calculate_correlation(df)
            if corr_data.get("matrix"):
                recommendations.append({
                    "id": "rec-correlation-heatmap",
                    "title": "Correlation Heatmap Matrix",
                    "chartType": "heatmap",
                    "plotlyData": {
                        "data": [{
                            "z": corr_data["matrix"],
                            "x": corr_data["columns"],
                            "y": corr_data["columns"],
                            "type": "heatmap",
                            "colorscale": "Viridis"
                        }],
                        "layout": {
                            "title": "Pearson Correlation Heatmap",
                            "template": "plotly_dark"
                        }
                    }
                })

        # 6. Single Categorical -> Pie Chart
        if cat_cols:
            c_col = cat_cols[0]
            val_counts = df[c_col].dropna().value_counts().head(8)
            recommendations.append({
                "id": f"rec-pie-{c_col}",
                "title": f"{c_col} Share Breakdown",
                "chartType": "pie",
                "xAxis": c_col,
                "plotlyData": {
                    "data": [{
                        "labels": [str(k) for k in val_counts.index],
                        "values": [int(v) for v in val_counts.values],
                        "type": "pie",
                        "hole": 0.4
                    }],
                    "layout": {
                        "title": f"Pie Breakdown: {c_col}",
                        "template": "plotly_dark"
                    }
                }
            })

        return recommendations

    @staticmethod
    def generate_custom_chart(
        df: pd.DataFrame,
        chart_type: str,
        x_axis: Optional[str] = None,
        y_axis: Optional[str] = None,
        color_col: Optional[str] = None,
        aggregation: str = "none"
    ) -> Dict[str, Any]:
        
        plot_df = df.copy()
        
        if x_axis and x_axis not in plot_df.columns:
            x_axis = None
        if y_axis and y_axis not in plot_df.columns:
            y_axis = None

        chart_type = chart_type.lower()

        # Handle Aggregations
        if aggregation in ["sum", "mean", "median", "count", "min", "max"] and x_axis and y_axis:
            try:
                if aggregation == "sum":
                    agg_df = plot_df.groupby(x_axis)[y_axis].sum().reset_index()
                elif aggregation == "mean":
                    agg_df = plot_df.groupby(x_axis)[y_axis].mean().reset_index()
                elif aggregation == "median":
                    agg_df = plot_df.groupby(x_axis)[y_axis].median().reset_index()
                elif aggregation == "count":
                    agg_df = plot_df.groupby(x_axis)[y_axis].count().reset_index()
                elif aggregation == "min":
                    agg_df = plot_df.groupby(x_axis)[y_axis].min().reset_index()
                elif aggregation == "max":
                    agg_df = plot_df.groupby(x_axis)[y_axis].max().reset_index()
                plot_df = agg_df
            except Exception:
                pass

        plot_df = plot_df.head(500)  # limit for performance

        trace = {}
        if chart_type in ["bar"]:
            trace = {
                "x": [str(x) for x in plot_df[x_axis]] if x_axis else [],
                "y": [float(y) if pd.api.types.is_numeric_dtype(plot_df[y_axis]) else str(y) for y in plot_df[y_axis]] if y_axis else [],
                "type": "bar",
                "marker": {"color": "#6366f1"}
            }
        elif chart_type in ["line", "area"]:
            trace = {
                "x": [str(x) for x in plot_df[x_axis]] if x_axis else [],
                "y": [float(y) for y in plot_df[y_axis]] if y_axis else [],
                "type": "scatter",
                "mode": "lines+markers",
                "fill": "tozeroy" if chart_type == "area" else "none",
                "line": {"color": "#10b981", "width": 3}
            }
        elif chart_type in ["scatter"]:
            trace = {
                "x": [float(x) if pd.api.types.is_numeric_dtype(plot_df[x_axis]) else str(x) for x in plot_df[x_axis]] if x_axis else [],
                "y": [float(y) if pd.api.types.is_numeric_dtype(plot_df[y_axis]) else str(y) for y in plot_df[y_axis]] if y_axis else [],
                "mode": "markers",
                "type": "scatter",
                "marker": {"color": "#ec4899", "size": 8, "opacity": 0.8}
            }
        elif chart_type in ["histogram"]:
            col = x_axis or y_axis or list(plot_df.columns)[0]
            trace = {
                "x": [float(v) if pd.api.types.is_numeric_dtype(plot_df[col]) else str(v) for v in plot_df[col].dropna()],
                "type": "histogram",
                "marker": {"color": "#8b5cf6"}
            }
        elif chart_type in ["box"]:
            col = y_axis or x_axis or list(plot_df.columns)[0]
            trace = {
                "y": [float(v) for v in plot_df[col].dropna()] if pd.api.types.is_numeric_dtype(plot_df[col]) else [],
                "type": "box",
                "marker": {"color": "#f59e0b"}
            }
        elif chart_type in ["pie", "doughnut"]:
            col = x_axis or list(plot_df.columns)[0]
            val_counts = plot_df[col].value_counts().head(10)
            trace = {
                "labels": [str(k) for k in val_counts.index],
                "values": [int(v) for v in val_counts.values],
                "type": "pie",
                "hole": 0.4 if chart_type == "doughnut" else 0.0
            }
        else: # default bar
            trace = {
                "x": [str(x) for x in plot_df[x_axis]] if x_axis else [],
                "y": [float(y) for y in plot_df[y_axis]] if y_axis else [],
                "type": "bar",
                "marker": {"color": "#6366f1"}
            }

        title_str = f"Custom {chart_type.title()} Chart"
        if x_axis and y_axis:
            title_str = f"{y_axis} vs {x_axis} ({aggregation.title()})"

        return {
            "title": title_str,
            "chartType": chart_type,
            "plotlyData": {
                "data": [trace],
                "layout": {
                    "title": title_str,
                    "xaxis": {"title": x_axis or ""},
                    "yaxis": {"title": y_axis or ""},
                    "template": "plotly_dark"
                }
            }
        }

visualization_service = VisualizationService()
