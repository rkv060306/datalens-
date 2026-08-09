import re
import json
import numpy as np
import pandas as pd
import urllib.request
import urllib.error
from typing import Dict, Any, List
from backend.services.profiling_service import profiling_service
from backend.services.statistics_service import statistics_service
from backend.services.insight_service import insight_service

class ChatbotService:
    @staticmethod
    def query(
        dataset_info: Dict[str, Any], 
        df: pd.DataFrame, 
        user_message: str,
        provider: str = "builtin",
        api_key: str | None = None,
        model: str | None = None
    ) -> Dict[str, Any]:
        """
        Processes a natural language query about a dataset using either external free LLM APIs
        (Gemini, Groq, OpenRouter, HuggingFace) or the built-in fast heuristic analytics engine.
        """
        if provider and provider != "builtin" and api_key and api_key.strip():
            llm_result = ChatbotService._call_external_llm(
                provider=provider.lower(),
                api_key=api_key.strip(),
                model=model,
                dataset_info=dataset_info,
                df=df,
                user_message=user_message
            )
            if llm_result:
                return llm_result

        return ChatbotService._builtin_query(dataset_info, df, user_message)

    @staticmethod
    def _construct_dataset_context(dataset_info: Dict[str, Any], df: pd.DataFrame) -> str:
        filename = dataset_info.get("originalFilename", "dataset")
        if df is None or df.empty:
            return f"Dataset '{filename}' is empty or non-tabular."

        profile = profiling_service.profile_dataframe(df)
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

        sample_dict = df.head(5).to_dict(orient="records")
        stats_summary = {}
        for col in num_cols[:8]:
            stats_summary[col] = {
                "mean": round(float(df[col].mean()), 2) if not df[col].empty else 0,
                "min": round(float(df[col].min()), 2) if not df[col].empty else 0,
                "max": round(float(df[col].max()), 2) if not df[col].empty else 0
            }

        return (
            f"Dataset Name: {filename}\n"
            f"Rows: {profile['rows']:,}, Columns: {profile['columns']}\n"
            f"Data Quality Score: {profile['qualityScore']}/100 ({profile['qualityRating']})\n"
            f"Missing Cells: {profile['missingPercentage']}%\n"
            f"Numeric Columns: {num_cols}\n"
            f"Categorical Columns: {cat_cols}\n"
            f"Numeric Summary Stats: {json.dumps(stats_summary)}\n"
            f"First 5 Sample Rows JSON:\n{json.dumps(sample_dict, default=str)}"
        )

    @staticmethod
    def _call_external_llm(
        provider: str,
        api_key: str,
        model: str | None,
        dataset_info: Dict[str, Any],
        df: pd.DataFrame,
        user_message: str
    ) -> Dict[str, Any] | None:
        context_str = ChatbotService._construct_dataset_context(dataset_info, df)
        system_prompt = (
            "You are DataLens AI, an expert data analyst assistant embedded in an analytics platform. "
            "Use the provided dataset schema, profiling metrics, and sample rows to provide a helpful, concise, "
            "and beautifully markdown-formatted answer to the user's request. Include bullet points, bold key metrics, "
            "and code blocks where appropriate.\n\n"
            f"--- DATASET CONTEXT ---\n{context_str}\n------------------------"
        )

        reply_text = None
        try:
            if provider == "gemini":
                chosen_model = model or "gemini-1.5-flash"
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{chosen_model}:generateContent?key={api_key}"
                payload = json.dumps({
                    "contents": [{
                        "parts": [{"text": f"{system_prompt}\n\nUser Question: {user_message}"}]
                    }]
                }).encode('utf-8')
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=20) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    reply_text = res_data["candidates"][0]["content"]["parts"][0]["text"]

            elif provider == "groq":
                chosen_model = model or "llama-3.3-70b-versatile"
                url = "https://api.groq.com/openai/v1/chat/completions"
                payload = json.dumps({
                    "model": chosen_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ]
                }).encode('utf-8')
                req = urllib.request.Request(url, data=payload, headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                })
                with urllib.request.urlopen(req, timeout=20) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    reply_text = res_data["choices"][0]["message"]["content"]

            elif provider == "openrouter":
                chosen_model = model or "google/gemini-2.0-flash-exp:free"
                url = "https://openrouter.ai/api/v1/chat/completions"
                payload = json.dumps({
                    "model": chosen_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ]
                }).encode('utf-8')
                req = urllib.request.Request(url, data=payload, headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                })
                with urllib.request.urlopen(req, timeout=20) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    reply_text = res_data["choices"][0]["message"]["content"]

            elif provider == "huggingface":
                chosen_model = model or "mistralai/Mistral-7B-Instruct-v0.3"
                url = f"https://api-inference.huggingface.co/models/{chosen_model}"
                payload = json.dumps({
                    "inputs": f"<s>[INST] {system_prompt}\nUser Question: {user_message} [/INST]"
                }).encode('utf-8')
                req = urllib.request.Request(url, data=payload, headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                })
                with urllib.request.urlopen(req, timeout=20) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    if isinstance(res_data, list) and "generated_text" in res_data[0]:
                        reply_text = res_data[0]["generated_text"]
                    elif isinstance(res_data, dict) and "generated_text" in res_data:
                        reply_text = res_data["generated_text"]

            if reply_text:
                provider_name = provider.capitalize()
                return {
                    "reply": f"🤖 *Powered by {provider_name} ({model or 'default'})*\n\n{reply_text}",
                    "suggestions": [
                        "Can you summarize this dataset?",
                        "What are the main correlation insights?",
                        "What ML models do you recommend?"
                    ]
                }
        except Exception as e:
            # On error, fallback gracefully with a warning badge
            fallback = ChatbotService._builtin_query(dataset_info, df, user_message)
            fallback["reply"] = f"⚠️ *{provider.capitalize()} API call failed: {str(e)}. Reverting to DataLens Built-in Engine.*\n\n" + fallback["reply"]
            return fallback

        return None

    @staticmethod
    def _builtin_query(dataset_info: Dict[str, Any], df: pd.DataFrame, user_message: str) -> Dict[str, Any]:
        """
        Built-in fast heuristic data analytics engine.
        """
        msg = user_message.lower().strip()
        filename = dataset_info.get("originalFilename", "dataset")

        if df is None or df.empty:
            return {
                "reply": f"📁 **{filename}** is a non-tabular or empty dataset. Full automated statistical query features are optimized for CSV and Excel files.",
                "suggestions": ["Upload a CSV dataset", "View Dataset Details"]
            }

        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime', 'datetime64']).columns.tolist()

        profile = profiling_service.profile_dataframe(df)

        # 1. Dataset Overview / Summary
        if any(kw in msg for kw in ["summary", "summarize", "overview", "what is this", "about", "describe"]):
            col_list_str = ", ".join([f"`{c}`" for c in df.columns[:10]])
            if len(df.columns) > 10:
                col_list_str += f" and {len(df.columns) - 10} more"

            quality_rating = profile.get("qualityBreakdown", {}).get("status", "Good")
            missing_cells = profile.get("missingCells", 0)
            mem_size = f"{profile.get('memoryUsageMB', 0):.2f} MB"

            reply = (
                f"### 📊 Dataset Overview: **{filename}**\n\n"
                f"- **Rows**: `{profile.get('rows', 0):,}` | **Columns**: `{profile.get('columns', 0)}`\n"
                f"- **Data Quality Score**: `{profile.get('qualityScore', 0)}/100` ({quality_rating})\n"
                f"- **Missing Cells**: `{profile.get('missingPercentage', 0)}%` ({missing_cells:,} cells)\n"
                f"- **Memory Footprint**: `{mem_size}`\n"
                f"- **Column Types**: {len(num_cols)} Numeric, {len(cat_cols)} Categorical, {len(date_cols)} Datetime\n\n"
                f"**Columns**: {col_list_str}"
            )
            return {
                "reply": reply,
                "suggestions": [
                    "What are the data quality issues?",
                    "Which columns have missing values?",
                    "What are the strongest correlations?",
                    "Recommend ML models for this dataset"
                ]
            }

        # 2. Data Quality & Missing Values
        if any(kw in msg for kw in ["quality", "missing", "clean", "null", "blank", "incomplete"]):
            quality_rating = profile.get("qualityBreakdown", {}).get("status", "Good")
            missing_cols = {col: int(df[col].isna().sum()) for col in df.columns if df[col].isna().sum() > 0}
            if not missing_cols:
                reply = (
                    f"✨ **Data Quality Score**: `{profile.get('qualityScore', 0)}/100` ({quality_rating})\n\n"
                    f"Great news! **No missing values** were found in **{filename}**. The dataset is 100% complete across all `{profile.get('rows', 0):,}` rows."
                )
            else:
                missing_str = "\n".join([f"- `{col}`: **{cnt} missing** ({round(cnt/len(df)*100, 1)}%)" for col, cnt in missing_cols.items()])
                reply = (
                    f"⚠️ **Data Quality Report for {filename}**\n\n"
                    f"- **Data Quality Score**: `{profile.get('qualityScore', 0)}/100` ({quality_rating})\n"
                    f"- **Duplicate Rows**: `{profile.get('duplicateRows', 0):,}`\n\n"
                    f"**Columns with missing values:**\n{missing_str}\n\n"
                    f"💡 *Tip: You can use the **Spreadsheet Preview** page to impute missing values using Mean, Median, or Mode.*"
                )
            return {
                "reply": reply,
                "suggestions": [
                    "Summarize dataset",
                    "What are the strongest correlations?",
                    "Recommend visualizations"
                ]
            }

        # 3. Correlations & Relationships
        if any(kw in msg for kw in ["correlation", "relationship", "correlated", "associated", "pearson"]):
            if len(num_cols) < 2:
                return {
                    "reply": f"ℹ️ Correlation analysis requires at least 2 numeric columns. Current numeric columns: `{num_cols}`",
                    "suggestions": ["Summarize dataset", "What are the data quality issues?"]
                }
            corr_matrix = df[num_cols].corr()
            pairs = []
            for i in range(len(num_cols)):
                for j in range(i + 1, len(num_cols)):
                    val = corr_matrix.iloc[i, j]
                    if not np.isnan(val):
                        pairs.append((num_cols[i], num_cols[j], abs(val), val))
            pairs.sort(key=lambda x: x[2], reverse=True)

            top_pairs = pairs[:5]
            if not top_pairs:
                reply = "No significant numerical correlations were detected."
            else:
                pairs_str = "\n".join([
                    f"- `{p[0]}` & `{p[1]}`: **{p[3]:+.3f}** ({'Strong Positive' if p[3] > 0.6 else 'Strong Negative' if p[3] < -0.6 else 'Moderate'})"
                    for p in top_pairs
                ])
                reply = (
                    f"📈 **Top Pearson Correlations in {filename}:**\n\n"
                    f"{pairs_str}\n\n"
                    f"💡 *Strong correlations indicate attributes that trend together or inversely.*"
                )
            return {
                "reply": reply,
                "suggestions": [
                    "Detect outliers in data",
                    "Recommend visualizations",
                    "Recommend ML models"
                ]
            }

        # 4. Outlier Analysis
        if any(kw in msg for kw in ["outlier", "outliers", "anomaly", "anomalies", "extreme", "iqr"]):
            outlier_results = statistics_service.detect_outliers(df)
            outlier_cols = outlier_results.get("outliersPerColumn", {})
            total_outliers = sum(info["count"] for info in outlier_cols.values())

            if total_outliers == 0:
                reply = f"✅ **No extreme outliers** were detected using the 1.5x IQR rule across numeric columns in **{filename}**."
            else:
                details = "\n".join([
                    f"- `{col}`: **{info['count']} outliers** ({info['percentage']}%) — Normal Range: `{info['lowerBound']:.2f}` to `{info['upperBound']:.2f}`"
                    for col, info in outlier_cols.items() if info['count'] > 0
                ])
                reply = (
                    f"🚨 **Outlier Detection Summary (IQR Method):**\n\n"
                    f"Total outliers detected: **{total_outliers}**\n\n"
                    f"{details}\n\n"
                    f"💡 *Outliers can distort mean averages and ML regression models.*"
                )
            return {
                "reply": reply,
                "suggestions": [
                    "What are the strongest correlations?",
                    "Summarize dataset",
                    "Recommend ML models"
                ]
            }

        # 5. ML Recommendations
        if any(kw in msg for kw in ["ml", "machine learning", "model", "predict", "train", "classification", "regression"]):
            insights = insight_service.generate_insights(df)
            ml_insights = [ins for ins in insights if ins.get("type") == "ml_recommendation"]
            if ml_insights:
                ins_text = "\n".join([f"- **{ins['title']}**: {ins['description']}" for ins in ml_insights])
                reply = f"🤖 **Machine Learning Strategy for {filename}:**\n\n{ins_text}\n\nHead over to **AI Insights & ML** tab to build and evaluate models interactively!"
            else:
                rec_target = num_cols[0] if num_cols else (cat_cols[0] if cat_cols else None)
                rec_features = [c for c in num_cols + cat_cols if c != rec_target][:4]
                reply = (
                    f"🤖 **Machine Learning Recommendation for {filename}:**\n\n"
                    f"- **Suggested Target Column**: `{rec_target}`\n"
                    f"- **Suggested Feature Inputs**: `{', '.join(rec_features)}` \n"
                    f"- **Recommended Algorithm**: `RandomForest` / `Linear Regression`\n\n"
                    f"Go to **AI Insights & ML** page to train a model in 1 click."
                )
            return {
                "reply": reply,
                "suggestions": [
                    "What are the strongest correlations?",
                    "Recommend visualizations",
                    "Summarize dataset"
                ]
            }

        # 6. Visualization Recommendations
        if any(kw in msg for kw in ["chart", "visualization", "plot", "graph", "recommend"]):
            reply = (
                f"📈 **Recommended Visualization Types for {filename}:**\n\n"
            )
            if num_cols and cat_cols:
                reply += f"- 📊 **Bar Chart / Box Plot**: Pair categorical `{cat_cols[0]}` with numerical `{num_cols[0]}`.\n"
            if len(num_cols) >= 2:
                reply += f"- 🟢 **Scatter Plot**: Compare `{num_cols[0]}` vs `{num_cols[1]}` to identify trends.\n"
            if num_cols:
                reply += f"- 📉 **Histogram**: View value distribution and skewness for `{num_cols[0]}`.\n"
            if date_cols and num_cols:
                reply += f"- 📈 **Time-Series Line Chart**: Plot `{num_cols[0]}` over `{date_cols[0]}`.\n"

            reply += "\nUse the **Chart Builder** tab to customize colors, axes, and aggregations!"
            return {
                "reply": reply,
                "suggestions": [
                    "What are the strongest correlations?",
                    "Summarize dataset",
                    "Recommend ML models"
                ]
            }

        # 7. Specific Column Query
        matched_col = None
        for col in df.columns:
            if col.lower() in msg:
                matched_col = col
                break

        if matched_col:
            col_data = df[matched_col]
            missing_cnt = int(col_data.isna().sum())
            if pd.api.types.is_numeric_dtype(col_data):
                mean_v = float(col_data.mean())
                std_v = float(col_data.std()) if len(col_data) > 1 else 0.0
                min_v = float(col_data.min())
                max_v = float(col_data.max())
                median_v = float(col_data.median())
                reply = (
                    f"📌 **Column Analysis: `{matched_col}` (Numeric)**\n\n"
                    f"- **Mean**: `{mean_v:,.2f}` | **Median**: `{median_v:,.2f}`\n"
                    f"- **Range**: `{min_v:,.2f}` to `{max_v:,.2f}`\n"
                    f"- **Std Deviation**: `{std_v:,.2f}`\n"
                    f"- **Missing Values**: `{missing_cnt}` ({round(missing_cnt/len(df)*100, 1)}%)"
                )
            else:
                unique_cnt = col_data.nunique()
                top_mode = col_data.mode().iloc[0] if not col_data.mode().empty else "N/A"
                top_freq = int((col_data == top_mode).sum()) if top_mode != "N/A" else 0
                reply = (
                    f"📌 **Column Analysis: `{matched_col}` (Categorical/Text)**\n\n"
                    f"- **Unique Categories**: `{unique_cnt}`\n"
                    f"- **Most Frequent Value**: `{top_mode}` ({top_freq} occurrences)\n"
                    f"- **Missing Values**: `{missing_cnt}` ({round(missing_cnt/len(df)*100, 1)}%)"
                )
            return {
                "reply": reply,
                "suggestions": [
                    "Summarize dataset",
                    "What are the data quality issues?",
                    "Recommend visualizations"
                ]
            }

        # 8. Fallback intelligent response with key highlights
        top_num = num_cols[0] if num_cols else "N/A"
        avg_val = f"{df[top_num].mean():,.2f}" if top_num != "N/A" else "N/A"

        reply = (
            f"💡 **DataLens Assistant for {filename}**\n\n"
            f"I have analyzed **{filename}** (`{profile['rows']:,}` rows, `{profile['columns']}` columns).\n\n"
            f"- **Data Quality Score**: `{profile['qualityScore']}/100`\n"
            f"- **Numeric Highlight**: Primary metric `{top_num}` averages `{avg_val}`\n"
            f"- **Missing Values**: `{profile['missingPercentage']}%` missing cells\n\n"
            f"Ask me anything about specific columns, correlations, outliers, charts, or machine learning recommendations!"
        )

        return {
            "reply": reply,
            "suggestions": [
                "Summarize dataset",
                "What are the data quality issues?",
                "What are the strongest correlations?",
                "Recommend ML models"
            ]
        }

chatbot_service = ChatbotService()
