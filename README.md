# Road Transportation Expert System

An intelligent, rule-based advisory web application demonstrating the core tenets of **Artificial Intelligence (AI)**: declarative knowledge representation, IF–THEN production rules, forward-chaining deduction, rule conflict resolution, and explainable AI (XAI).

This project runs **without any paid APIs, external cloud dependencies, or black-box machine learning models**. The reasoning logic is powered entirely by a custom, explainable Python inference engine operating over a structured JSON knowledge base and SQLite history database.

---

## 1. Project Overview & Problem Statement

Road transport networks frequently encounter multiple compounding hazards—including traffic congestion, extreme weather (rainfall, dense fog), damaged infrastructure, active construction zones, vehicle breakdowns, fuel depletion, and road collisions. 

Human commuters and dispatchers often find it challenging to synthesize multiple simultaneous road variables into prioritized, safe actions. 

This **Road Transportation Expert System** solves this challenge by:
1. Formalizing road safety heuristics and traffic management protocols into modular **IF–THEN production rules**.
2. Applying **forward-chaining deduction** across user-reported facts (working memory).
3. Enforcing safety invariants (e.g., road closures strictly prohibit entry; emergencies take precedence).
4. Generating **transparent reasoning traces** through an integrated Explanation Facility.

---

## 2. Artificial Intelligence Concepts Demonstrated

* **Knowledge Representation:** Domain knowledge is externalized into declarative JSON structures (`knowledge_base/transportation_rules.json`) rather than hardcoded in procedural route handlers.
* **IF–THEN Production Rules:** Preconditions (premises) evaluated with Boolean conjunctions (`AND`) and disjunctions (`OR`).
* **Forward-Chaining Inference:** Data-driven reasoning starting from observed facts in working memory to deduce recommendations.
* **Conflict Resolution & Prioritization:** Prioritizes recommendations by severity (`High` > `Medium` > `Low`) and deduplicates overlapping guidance.
* **Explanation Facility (Explainable AI / XAI):** Details the exact clause-by-clause condition tests that caused each rule to trigger (e.g., `weather == "Rainy" -> TRUE`).
* **Relational Audit Memory:** Longitudinal storage of assessments in SQLite for statistical aggregation and empirical analysis.

---

## 3. Technology Stack

* **AI Inference Engine:** Pure Python 3 (Forward-chaining matcher, RuleLoader, ExplanationFacility).
* **Knowledge Base:** JSON (`transportation_rules.json`) with 25 comprehensive transportation rules.
* **Web Backend:** Python 3, Flask 3.x, Jinja2 template engine.
* **Database:** SQLite 3 (Python standard library `sqlite3`), parameterized queries, JSON serialization.
* **Frontend:** HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, Google Fonts (`Inter`).
* **Data Visualization:** Chart.js 4.4 (Canvas API).
* **Testing:** Pytest 8.x test suite (28 automated test cases).
* **Production Server:** Gunicorn WSGI.

---

## 4. Project Directory Structure

```text
Road Transportation/
├── app.py                     # Flask application factory and route controller
├── config.py                  # Environment configurations (Dev, Test, Prod)
├── requirements.txt           # Python dependencies (Flask, Gunicorn, pytest)
├── Procfile                   # Process file for Render / WSGI hosts
├── render.yaml                # Render blueprint specification
├── README.md                  # Project documentation
├── .gitignore                 # Version control exclusions
│
├── expert_system/             # Core Artificial Intelligence Engine
│   ├── __init__.py
│   ├── rule_engine.py         # Forward-chaining deduction & conflict resolution
│   ├── rule_loader.py         # Safe JSON loader and rule schema validation
│   ├── explanation.py        # Explainable AI trace generator
│   └── validators.py          # Input fact verification and schema guards
│
├── knowledge_base/
│   └── transportation_rules.json  # 25 declarative production rules
│
├── database/
│   ├── __init__.py
│   ├── db.py                  # SQLite access layer & analytics calculations
│   └── schema.sql             # Relational schema for assessment history
│
├── templates/                 # Jinja2 HTML Templates
│   ├── base.html              # Shared layout with responsive sidebar
│   ├── dashboard.html         # Live metrics, charts, and recent activity
│   ├── assessment.html        # Interactive road facts input form
│   ├── results.html           # Advisory report & explanation traces
│   ├── history.html           # Historical assessments log with filters
│   ├── assessment_details.html# Deep inspection of historical records
│   ├── knowledge_base.html    # Rule catalog viewer and filter
│   ├── rule_details.html      # Individual rule IF-THEN logic inspector
│   ├── analytics.html         # Empirical analytics with 6 Chart.js charts
│   ├── about.html             # Academic project documentation & architecture
│   └── 404.html               # Custom 404 error page
│
├── static/                    # Frontend Assets
│   ├── css/
│   │   └── style.css          # Professional navy-teal design system
│   └── js/
│       ├── main.js            # UI handlers, loading spinner, mobile sidebar
│       └── analytics.js       # Dynamic Chart.js dashboard integration
│
└── tests/                     # Automated Test Suite (28 tests)
    ├── test_rule_engine.py    # Rule matching, AND/OR logic, and safety tests
    ├── test_validators.py     # Input sanitization and rule schema tests
    └── test_routes.py         # Flask HTTP routes and database tests
```

---

## 5. Local Installation & Execution (Windows)

### Prerequisites
* Python 3.10+ (Available as `python` or `py`)
* Git

### Step 1: Clone or Navigate to the Project Folder
```powershell
cd "c:\Users\Sanskar Dumbre\OneDrive\Desktop\Road Transportation"
```

### Step 2: Create and Activate a Virtual Environment
**Windows PowerShell:**
```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If script execution is disabled in PowerShell, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

**Windows Command Prompt (cmd):**
```cmd
py -m venv venv
venv\Scripts\activate.bat
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Automated Test Suite
Verify that all 28 automated tests pass:
```powershell
pytest -v
```

### Step 5: Start the Flask Application
```powershell
python app.py
```
Open your browser and navigate to: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 6. Deployment Guide: Render vs Vercel

### Recommendation: **Deploy on Render**

| Feature | **Render (Recommended)** | **Vercel** |
| :--- | :--- | :--- |
| **Backend Model** | Persistent Web Service (Flask + Gunicorn) | Serverless Functions (AWS Lambda-based) |
| **SQLite Compatibility** | **Yes** — writes to disk persist while container runs | **No** — filesystem is read-only/ephemeral; SQLite resets on cold starts |
| **Setup Complexity** | **Zero-config** — detects `requirements.txt` & `Procfile` | Requires custom `vercel.json` and serverless adapter |
| **Free Tier** | Free Web Services with automatic HTTPS | Free tier, but limited for stateful Python backends |

### How to Deploy to Render (Step-by-Step):

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Road Transportation Expert System"
   git branch -M main
   git remote add origin https://github.com/<your-username>/road-transportation-expert-system.git
   git push -u origin main
   ```

2. **Create Web Service on Render:**
   * Go to [Render Dashboard](https://dashboard.render.com/) and click **New + > Web Service**.
   * Connect your GitHub repository.
   * Render will automatically detect Python. Fill in the following:
     * **Name:** `road-transportation-expert-system`
     * **Environment:** `Python 3`
     * **Region:** Any (e.g., Singapore or Frankfurt)
     * **Build Command:** `pip install -r requirements.txt`
     * **Start Command:** `gunicorn app:app`
     * **Instance Type:** `Free`
   * Click **Create Web Service**.

3. **Your application will be live in 2 minutes** at `https://road-transportation-expert-system.onrender.com`!

---

## 7. Example Rule & Forward-Chaining Walkthrough

### Example Rule (`R014`):
```json
{
  "id": "R014",
  "name": "Slippery Road in Wet Weather (Hydroplaning Hazard)",
  "category": "Road Safety",
  "conditions": {
    "road_condition": "Slippery",
    "weather": "Rainy"
  },
  "operator": "AND",
  "recommendation": "Severe traction loss alert: Wet, slippery road surfaces create acute hydroplaning conditions. Moderate speed below 40 km/h, avoid cruise control, and apply brakes with progressive smoothness.",
  "explanation": "Water accumulation over slick road surfaces causes loss of tire contact with the asphalt.",
  "priority": "High",
  "enabled": true
}
```

### Forward-Chaining Trace:
1. **User Facts Ingested:** `road_condition = "Slippery"`, `weather = "Rainy"`, `traffic = "Heavy"`.
2. **Precondition Evaluation:**
   * `road_condition == "Slippery"` &rarr; **TRUE**
   * `weather == "Rainy"` &rarr; **TRUE**
3. **Conjunctive Operator Evaluation:** `TRUE AND TRUE` &rarr; **TRUE**.
4. **Action Fired:** Rule `R014` activates with **High Priority**. The Explanation Facility registers the premise evaluation trace and appends the recommendation to the advisory report.

---

## 8. Limitations & Future Enhancements

* **Self-Reported Facts:** Assessment relies on user-selected inputs rather than direct live GPS/telematics feeds.
* **Binary Logic:** Evaluates Boolean preconditions. Future versions could integrate **Certainty Factors** (MYCIN architecture) or Fuzzy Logic for graded weather intensity.
* **GIS Mapping:** Future integration with OpenStreetMap / Leaflet to plot hazard zones geographically.

---

## 9. Academic Integrity & Safety Disclaimer

This system is an academic software project demonstrating Artificial Intelligence rule-based systems. It is not an authorized replacement for official road transport authorities, police advisories, or professional emergency responders. In real emergencies, always dial **112** (or your local emergency helpline).
