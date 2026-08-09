 DataLens — Universal Online Data Analytics Platform

DataLens is a full-stack, open-source online data analytics platform. It allows users to upload structured datasets (CSV, Excel) and media files (Images, Videos), and automatically profiles, cleans, analyzes, visualizes, and generates calculated statistical insights and downloadable PDF reports — **100% free with zero mandatory registration or login required**.

---

## 🌟 Key Features

1. **Universal Multi-Format Support**:
   - Tabular Datasets: CSV, XLSX, XLS across Sales, Finance, Education, Healthcare, HR, IoT, E-commerce, Marketing.
   - Media Data: Image files (EXIF metadata, aspect ratio, color histograms, contrast, OCR text detection) and Video files (FPS, duration, resolution, frame brightness variance).

2. **Friction-Free & Open-Source**:
   - Zero login/register required. Users land on the platform and get instant interactive dashboards.
   - Full optional JWT authentication & bcrypt password hashing for persistent user accounts.

3. **Automated Data Profiling & Quality Scoring**:
   - Automated row/column counting, memory footprint calculation, missing cell percentage, duplicate detection.
   - **Data Quality Score (0–100)** with detailed mathematical factor breakdowns.

4. **Data Cleaning Suite**:
   - Impute missing values using Mean, Median, Mode, or custom values.
   - Purge duplicate rows, normalize category string casing, and override column data types.
   - Preserves original raw uploads by generating cleaned dataset copies.

5. **Interactive Visualization Engine & Custom Builder**:
   - Auto-recommends Plotly.js charts (Histograms, Scatter plots, Bar charts, Time-series Line charts, Box plots, Pie charts, Area charts).
   - Custom Plotly Chart Builder with interactive X/Y axis selection and aggregations (Sum, Mean, Median, Count, Min, Max).

6. **Rule-Based AI Insights & Advanced Analytics**:
   - Automated detection of high correlation pairs, distribution anomalies, dominant categories, time-series growth/decline, and outlier risks.
   - **Scikit-Learn ML Module**: Train Linear Regression, Random Forest Classifier/Regressor, and K-Means Clustering models with R² scores, MSE, accuracy, and feature importances.

7. **Automated PDF Report Generation**:
   - Executive PDF report compilation via ReportLab with tables, quality gauges, and insight lists. Single-click PDF download.

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, Vanilla CSS3 (Custom CSS variables, Glassmorphism design system), Vanilla JavaScript (Modular ES6 API client & views).
- **Interactive Visualization**: Plotly.js, Chart.js.
- **Backend**: Python 3.11, FastAPI, Pandas, NumPy, Scikit-learn, OpenCV (`cv2`), Pillow, ReportLab.
- **Database**: MongoDB (via `motor`/`pymongo`) with transparent JSON file store fallback.
- **Authentication**: JWT tokens with `bcrypt` password hashing.

---

## 📁 Project Architecture

```text
DataLens/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── auth.py
│   │   ├── datasets.py
│   │   ├── analytics.py
│   │   ├── visualization.py
│   │   └── reports.py
│   ├── services/
│   │   ├── db_service.py
│   │   ├── file_service.py
│   │   ├── profiling_service.py
│   │   ├── cleaning_service.py
│   │   ├── statistics_service.py
│   │   ├── insight_service.py
│   │   ├── visualization_service.py
│   │   ├── ml_service.py
│   │   ├── media_service.py
│   │   └── report_service.py
│   ├── models/
│   │   ├── user.py
│   │   ├── dataset.py
│   │   └── analysis.py
│   └── utils/
│       ├── auth.py
│       └── validators.py
├── frontend/
│   ├── index.html
│   ├── upload.html
│   ├── dashboard.html
│   ├── dataset.html
│   ├── visualization.html
│   ├── insights.html
│   ├── reports.html
│   ├── history.html
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   ├── css/
│   └── js/
├── samples/
├── uploads/
├── generated_reports/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start & Installation

1. **Clone & Setup Environment**:
   ```bash
   git clone https://github.com/datalens/datalens.git
   cd datalens
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Platform Server**:
   ```bash
   python -m uvicorn backend.main:app --port 8000 --reload
   ```

4. **Access Platform**:
   Open browser at: `http://localhost:8000/`

---

## 📊 Sample Datasets Included

Located in `samples/` for zero-setup 1-click testing:
- `sales.csv`: E-Commerce transactions & profit margins.
- `students.csv`: Educational attendance & exam performance.
- `ecommerce.csv`: Retail orders, payment methods, delivery times.
- `employees.csv`: HR department salaries & performance ratings.
- `iot_sensor_data.csv`: Sensor readings, temperature, vibration.

---

# 🎓 PLACEMENT INTERVIEW PREPARATION

### 1-Minute Pitch (Elevator Pitch)
> "DataLens is a full-stack open-source universal online data analytics platform built with FastAPI, Pandas, NumPy, Scikit-learn, and Vanilla JavaScript with Plotly.js. Unlike single-domain tools, DataLens dynamically ingests CSV, Excel, Image, and Video data without hardcoded column assumptions. It automatically computes data quality scores, detects data types, handles missing value imputations, recommends interactive Plotly visualizations, calculates Pearson correlations and IQR outliers, trains Scikit-learn machine learning models, and exports PDF reports — all with zero forced user login."

### Technical Architecture Explanation
- **Why FastAPI?**: High-performance async Python framework based on OpenAPI standards with automatic Pydantic input validation.
- **Why Pandas & NumPy?**: Vectorized C-accelerated array and DataFrame calculations for high-throughput statistical computing.
- **Dual Storage Engine**: Asynchronous MongoDB via `motor` with a transparent JSON file storage fallback so the application works anywhere out-of-the-box.
- **Universal Visualization Logic**: Infers data types (Numeric, Categorical, Datetime) and automatically maps combinations into optimal chart types.

### 25 Technical Interview Q&As

#### Web Development & Frontend
1. **Q: Why use Vanilla JS instead of heavy frameworks like React for DataLens?**
   - *A*: Eliminates build-step overhead, reduces bundle size, and allows direct DOM manipulation and fast Plotly.js chart canvas rendering.
2. **Q: How does client-side session management work without mandatory login?**
   - *A*: DataLens automatically issues a transparent JWT guest token (`/api/auth/guest-token`) stored in `localStorage`, maintaining seamless user isolation without typing credentials.
3. **Q: What are CSS custom properties (variables) used for in DataLens?**
   - *A*: Enables a unified design system (`--bg-dark`, `--accent-primary`) supporting dark mode and glassmorphism.
4. **Q: How is responsive layout achieved across devices?**
   - *A*: CSS Grid, Flexbox, and fluid media query breakpoints in `responsive.css`.

#### Backend & API Design
5. **Q: How does FastAPI handle file uploads efficiently?**
   - *A*: Uses `UploadFile` backed by a temporary file stream on disk, avoiding loading giant files directly into RAM.
6. **Q: How are routes modularized in FastAPI?**
   - *A*: Using `APIRouter` in `backend/api/` split by concern (`auth`, `datasets`, `analytics`, `visualization`, `reports`).
7. **Q: How does CORS middleware protect the API?**
   - *A*: Restricts cross-origin HTTP requests using FastAPI's `CORSMiddleware`.

#### Data Analytics & Processing
8. **Q: How is the Data Quality Score calculated?**
   - *A*: Penalizes 100 points based on missing value percentage, duplicate row count, empty columns, and statistical outlier ratios.
9. **Q: How does automatic data type inference work?**
   - *A*: Evaluates dtypes, sample values, string-to-date parsing, and unique-to-total value ratios.
10. **Q: How does data cleaning preserve original data?**
    - *A*: Executes transformations on a copy and outputs a newly timestamped file (`cleaned_<uuid>_<file>.csv`).

#### Statistics & Mathematics
11. **Q: How is Pearson correlation calculated?**
    - *A*: $r = \frac{\sum (x - \bar{x})(y - \bar{y})}{\sqrt{\sum (x - \bar{x})^2 \sum (y - \bar{y})^2}}$. Measures linear relationship from -1.0 to +1.0.
12. **Q: How are outliers detected using IQR?**
    - *A*: $IQR = Q3 - Q1$. Outliers fall below $Q1 - 1.5 \times IQR$ or above $Q3 + 1.5 \times IQR$.
13. **Q: What is Z-Score outlier detection?**
    - *A*: $Z = \frac{X - \mu}{\sigma}$. Values with $|Z| > 3.0$ are flagged as outliers.

#### Machine Learning & Security
14. **Q: How does Scikit-Learn integration work in DataLens?**
    - *A*: Dynamically checks dataset suitability, applies `get_dummies` encoding, splits train/test data (75/25), and returns R², MSE, Accuracy, and Feature Importances.
15. **Q: How is JWT authentication secured?**
    - *A*: Signed using HS256 algorithm with expiration timestamps and `bcrypt` password hashing.
