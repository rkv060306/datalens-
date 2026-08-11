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
        size_col: Optional[str] = None,
        aggregation: str = "none",
        palette: str = "indigo",
        show_labels: bool = False,
        smooth_lines: bool = False,
        orientation: str = "v"
    ) -> Dict[str, Any]:
        
        plot_df = df.copy()
        
        palettes = {
            "indigo": ["#6366f1", "#8b5cf6", "#a855f7", "#d946ef", "#ec4899", "#f43f5e"],
            "emerald": ["#10b981", "#059669", "#047857", "#34d399", "#6ee7b7", "#a7f3d0"],
            "neon": ["#00f2fe", "#4facfe", "#f093fb", "#f5576c", "#5ee7df", "#b490ca"],
            "sunset": ["#ff7e5f", "#feb47b", "#ff6b6b", "#f8a5c2", "#e15f41", "#cf6a87"],
            "viridis": ["#440154", "#3b528b", "#21908c", "#5dc963", "#fde725", "#35b779"],
            "coral": ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeead", "#d4a5a5"]
        }
        color_list = palettes.get((palette or "indigo").lower(), palettes["indigo"])

        if x_axis and x_axis not in plot_df.columns:
            x_axis = None
        if y_axis and y_axis not in plot_df.columns:
            y_axis = None
        if color_col and color_col not in plot_df.columns:
            color_col = None
        if size_col and size_col not in plot_df.columns:
            size_col = None

        chart_type = (chart_type or "bar").lower()

        # Handle Aggregations
        group_cols = [c for c in [x_axis, color_col] if c is not None]
        if aggregation in ["sum", "mean", "median", "count", "min", "max"] and group_cols and y_axis:
            try:
                target_cols = [c for c in [y_axis, size_col] if c is not None and c not in group_cols and c in plot_df.columns]
                if target_cols:
                    if aggregation == "sum":
                        agg_df = plot_df.groupby(group_cols)[target_cols].sum().reset_index()
                    elif aggregation == "mean":
                        agg_df = plot_df.groupby(group_cols)[target_cols].mean().reset_index()
                    elif aggregation == "median":
                        agg_df = plot_df.groupby(group_cols)[target_cols].median().reset_index()
                    elif aggregation == "count":
                        agg_df = plot_df.groupby(group_cols)[target_cols].count().reset_index()
                    elif aggregation == "min":
                        agg_df = plot_df.groupby(group_cols)[target_cols].min().reset_index()
                    elif aggregation == "max":
                        agg_df = plot_df.groupby(group_cols)[target_cols].max().reset_index()
                    plot_df = agg_df
            except Exception:
                pass

        plot_df = plot_df.head(500)

        traces = []
        barmode = "group"

        # 1. BAR & HORIZONTAL & STACKED
        if chart_type in ["bar", "horizontal_bar", "bar_h", "stacked_bar"]:
            is_horiz = chart_type in ["horizontal_bar", "bar_h"] or orientation == "h"
            if chart_type == "stacked_bar":
                barmode = "stack"

            if color_col and color_col in plot_df.columns:
                groups = plot_df[color_col].unique()
                for idx, grp in enumerate(groups[:8]):
                    sub_df = plot_df[plot_df[color_col] == grp]
                    c = color_list[idx % len(color_list)]
                    x_vals = [str(x) for x in sub_df[x_axis]] if x_axis else []
                    y_vals = [float(y) if pd.api.types.is_numeric_dtype(sub_df[y_axis]) else str(y) for y in sub_df[y_axis]] if y_axis else []
                    
                    trace = {
                        "name": str(grp),
                        "type": "bar",
                        "marker": {"color": c}
                    }
                    if show_labels and y_axis:
                        trace["text"] = [str(round(v, 2)) if isinstance(v, (int, float)) else str(v) for v in y_vals]
                        trace["textposition"] = "auto"

                    if is_horiz:
                        trace["x"] = y_vals
                        trace["y"] = x_vals
                        trace["orientation"] = "h"
                    else:
                        trace["x"] = x_vals
                        trace["y"] = y_vals

                    traces.append(trace)
            else:
                x_vals = [str(x) for x in plot_df[x_axis]] if x_axis else []
                y_vals = [float(y) if pd.api.types.is_numeric_dtype(plot_df[y_axis]) else str(y) for y in plot_df[y_axis]] if y_axis else []
                trace = {
                    "type": "bar",
                    "marker": {"color": color_list[0]}
                }
                if show_labels and y_axis:
                    trace["text"] = [str(round(v, 2)) if isinstance(v, (int, float)) else str(v) for v in y_vals]
                    trace["textposition"] = "auto"

                if is_horiz:
                    trace["x"] = y_vals
                    trace["y"] = x_vals
                    trace["orientation"] = "h"
                else:
                    trace["x"] = x_vals
                    trace["y"] = y_vals
                traces.append(trace)

        # 2. LINE & AREA
        elif chart_type in ["line", "area"]:
            line_shape = "spline" if smooth_lines else "linear"
            fill_mode = "tozeroy" if chart_type == "area" else "none"

            if color_col and color_col in plot_df.columns:
                groups = plot_df[color_col].unique()
                for idx, grp in enumerate(groups[:8]):
                    sub_df = plot_df[plot_df[color_col] == grp]
                    c = color_list[idx % len(color_list)]
                    trace = {
                        "name": str(grp),
                        "x": [str(x) for x in sub_df[x_axis]] if x_axis else [],
                        "y": [float(y) if pd.api.types.is_numeric_dtype(sub_df[y_axis]) else str(y) for y in sub_df[y_axis]] if y_axis else [],
                        "type": "scatter",
                        "mode": "lines+markers",
                        "fill": fill_mode,
                        "line": {"color": c, "width": 3, "shape": line_shape}
                    }
                    if show_labels and y_axis:
                        trace["text"] = [str(round(v, 2)) if isinstance(v, (int, float)) else str(v) for v in sub_df[y_axis]]
                        trace["mode"] = "lines+markers+text"
                        trace["textposition"] = "top center"
                    traces.append(trace)
            else:
                y_vals = [float(y) if pd.api.types.is_numeric_dtype(plot_df[y_axis]) else str(y) for y in plot_df[y_axis]] if y_axis else []
                trace = {
                    "x": [str(x) for x in plot_df[x_axis]] if x_axis else [],
                    "y": y_vals,
                    "type": "scatter",
                    "mode": "lines+markers",
                    "fill": fill_mode,
                    "line": {"color": color_list[0], "width": 3, "shape": line_shape}
                }
                if show_labels and y_axis:
                    trace["text"] = [str(round(v, 2)) if isinstance(v, (int, float)) else str(v) for v in y_vals]
                    trace["mode"] = "lines+markers+text"
                    trace["textposition"] = "top center"
                traces.append(trace)

        # 3. SCATTER & BUBBLE
        elif chart_type in ["scatter", "bubble"]:
            sizes = None
            if size_col and size_col in plot_df.columns and pd.api.types.is_numeric_dtype(plot_df[size_col]):
                s_vals = plot_df[size_col].fillna(0)
                max_val = s_vals.max() or 1
                min_val = s_vals.min()
                sizes = [float(8 + 28 * ((v - min_val) / (max_val - min_val + 1e-9))) for v in s_vals]

            if color_col and color_col in plot_df.columns:
                groups = plot_df[color_col].unique()
                for idx, grp in enumerate(groups[:10]):
                    sub_df = plot_df[plot_df[color_col] == grp]
                    c = color_list[idx % len(color_list)]
                    sub_sizes = [sizes[i] for i in sub_df.index if i in range(len(sizes))] if sizes else 10
                    traces.append({
                        "name": str(grp),
                        "x": [float(x) if pd.api.types.is_numeric_dtype(sub_df[x_axis]) else str(x) for x in sub_df[x_axis]] if x_axis else [],
                        "y": [float(y) if pd.api.types.is_numeric_dtype(sub_df[y_axis]) else str(y) for y in sub_df[y_axis]] if y_axis else [],
                        "mode": "markers",
                        "type": "scatter",
                        "marker": {"color": c, "size": sub_sizes, "opacity": 0.75}
                    })
            else:
                traces.append({
                    "x": [float(x) if pd.api.types.is_numeric_dtype(plot_df[x_axis]) else str(x) for x in plot_df[x_axis]] if x_axis else [],
                    "y": [float(y) if pd.api.types.is_numeric_dtype(plot_df[y_axis]) else str(y) for y in plot_df[y_axis]] if y_axis else [],
                    "mode": "markers",
                    "type": "scatter",
                    "marker": {
                        "color": color_list[0],
                        "size": sizes if sizes else 10,
                        "opacity": 0.75
                    }
                })

        # 4. HISTOGRAM
        elif chart_type in ["histogram"]:
            col = x_axis or y_axis or list(plot_df.columns)[0]
            if color_col and color_col in plot_df.columns:
                groups = plot_df[color_col].unique()
                for idx, grp in enumerate(groups[:6]):
                    sub_df = plot_df[plot_df[color_col] == grp]
                    c = color_list[idx % len(color_list)]
                    traces.append({
                        "name": str(grp),
                        "x": [float(v) if pd.api.types.is_numeric_dtype(sub_df[col]) else str(v) for v in sub_df[col].dropna()],
                        "type": "histogram",
                        "opacity": 0.6,
                        "marker": {"color": c}
                    })
                barmode = "overlay"
            else:
                traces.append({
                    "x": [float(v) if pd.api.types.is_numeric_dtype(plot_df[col]) else str(v) for v in plot_df[col].dropna()],
                    "type": "histogram",
                    "marker": {"color": color_list[0]}
                })

        # 5. BOX & VIOLIN
        elif chart_type in ["box", "violin"]:
            y_col = y_axis or list(plot_df.columns)[0]
            x_col = x_axis or color_col

            if x_col and x_col in plot_df.columns:
                groups = plot_df[x_col].unique()
                for idx, grp in enumerate(groups[:10]):
                    sub_df = plot_df[plot_df[x_col] == grp]
                    c = color_list[idx % len(color_list)]
                    tr = {
                        "name": str(grp),
                        "y": [float(v) for v in sub_df[y_col].dropna()] if pd.api.types.is_numeric_dtype(sub_df[y_col]) else [],
                        "type": "box" if chart_type == "box" else "violin",
                        "marker": {"color": c}
                    }
                    if chart_type == "violin":
                        tr["box"] = {"visible": True}
                        tr["meanline"] = {"visible": True}
                    traces.append(tr)
            else:
                tr = {
                    "y": [float(v) for v in plot_df[y_col].dropna()] if pd.api.types.is_numeric_dtype(plot_df[y_col]) else [],
                    "type": "box" if chart_type == "box" else "violin",
                    "marker": {"color": color_list[0]}
                }
                if chart_type == "violin":
                    tr["box"] = {"visible": True}
                    tr["meanline"] = {"visible": True}
                traces.append(tr)

        # 6. PIE & DONUT
        elif chart_type in ["pie", "doughnut", "donut"]:
            col = x_axis or color_col or list(plot_df.columns)[0]
            if y_axis and pd.api.types.is_numeric_dtype(plot_df[y_axis]):
                val_grouped = plot_df.groupby(col)[y_axis].sum().head(10)
                labels = [str(k) for k in val_grouped.index]
                values = [float(v) for v in val_grouped.values]
            else:
                val_counts = plot_df[col].value_counts().head(10)
                labels = [str(k) for k in val_counts.index]
                values = [int(v) for v in val_counts.values]

            traces.append({
                "labels": labels,
                "values": values,
                "type": "pie",
                "hole": 0.45 if chart_type in ["doughnut", "donut"] else 0.0,
                "marker": {"colors": color_list}
            })

        # 7. HEATMAP
        elif chart_type in ["heatmap"]:
            if x_axis and y_axis:
                try:
                    ct = pd.crosstab(plot_df[y_axis], plot_df[x_axis])
                    traces.append({
                        "z": ct.values.tolist(),
                        "x": [str(c) for c in ct.columns],
                        "y": [str(r) for r in ct.index],
                        "type": "heatmap",
                        "colorscale": "Viridis" if palette == "viridis" else "Plasma"
                    })
                except Exception:
                    pass
            if not traces:
                corr_data = statistics_service.calculate_correlation(plot_df)
                if corr_data.get("matrix"):
                    traces.append({
                        "z": corr_data["matrix"],
                        "x": corr_data["columns"],
                        "y": corr_data["columns"],
                        "type": "heatmap",
                        "colorscale": "Viridis"
                    })

        # 8. RADAR / SPIDER
        elif chart_type in ["radar"]:
            if x_axis and y_axis:
                grouped = plot_df.groupby(x_axis)[y_axis].mean().head(10)
                r_vals = [float(v) for v in grouped.values]
                theta_vals = [str(k) for k in grouped.index]
                if r_vals:
                    r_vals.append(r_vals[0])
                    theta_vals.append(theta_vals[0])
                traces.append({
                    "type": "scatterpolar",
                    "r": r_vals,
                    "theta": theta_vals,
                    "fill": "toself",
                    "line": {"color": color_list[0]}
                })

        # 9. TREEMAP
        elif chart_type in ["treemap"]:
            col = x_axis or color_col or list(plot_df.columns)[0]
            val_counts = plot_df[col].value_counts().head(15)
            traces.append({
                "type": "treemap",
                "labels": [str(k) for k in val_counts.index],
                "parents": [""] * len(val_counts),
                "values": [int(v) for v in val_counts.values],
                "textinfo": "label+value+percent entry",
                "marker": {"colors": color_list}
            })

        # 10. WATERFALL
        elif chart_type in ["waterfall"]:
            if x_axis and y_axis:
                sub_df = plot_df.head(12)
                traces.append({
                    "type": "waterfall",
                    "orientation": "v",
                    "x": [str(x) for x in sub_df[x_axis]],
                    "y": [float(y) if pd.api.types.is_numeric_dtype(sub_df[y_axis]) else 1 for y in sub_df[y_axis]],
                    "connector": {"line": {"color": "rgb(63, 63, 63)"}}
                })

        # 11. 3D SCATTER
        elif chart_type in ["scatter3d"]:
            z_axis = size_col or (list(plot_df.columns)[2] if len(plot_df.columns) > 2 else y_axis)
            traces.append({
                "x": [float(x) if pd.api.types.is_numeric_dtype(plot_df[x_axis]) else str(x) for x in plot_df[x_axis]] if x_axis else [],
                "y": [float(y) if pd.api.types.is_numeric_dtype(plot_df[y_axis]) else str(y) for y in plot_df[y_axis]] if y_axis else [],
                "z": [float(z) if pd.api.types.is_numeric_dtype(plot_df[z_axis]) else 0 for z in plot_df[z_axis]] if z_axis else [],
                "mode": "markers",
                "type": "scatter3d",
                "marker": {"color": color_list[0], "size": 6, "opacity": 0.8}
            })

        # DEFAULT FALLBACK (BAR)
        if not traces:
            traces.append({
                "x": [str(x) for x in plot_df[x_axis]] if x_axis else [],
                "y": [float(y) if pd.api.types.is_numeric_dtype(plot_df[y_axis]) else str(y) for y in plot_df[y_axis]] if y_axis else [],
                "type": "bar",
                "marker": {"color": color_list[0]}
            })

        title_str = f"Custom {chart_type.replace('_', ' ').title()} Chart"
        if x_axis and y_axis:
            title_str = f"{y_axis} vs {x_axis} ({aggregation.title()})"

        layout = {
            "title": title_str,
            "xaxis": {"title": x_axis or ""},
            "yaxis": {"title": y_axis or ""},
            "barmode": barmode,
            "template": "plotly_dark",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "margin": {"t": 50, "b": 50, "l": 50, "r": 50}
        }

        return {
            "title": title_str,
            "chartType": chart_type,
            "plotlyData": {
                "data": traces,
                "layout": layout
            }
        }

visualization_service = VisualizationService()
