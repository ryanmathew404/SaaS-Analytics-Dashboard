# SaaS Product Analytics Dashboard

**Analyzed user behavior, retention patterns, and acquisition channel performance across a SaaS product dataset to identify churn drivers, high-value customer segments, and conversion funnel drop-off points.**

Built with SQL (SQLite), Python, and an interactive HTML/JS dashboard.

---

## Project Overview

This project replicates the kind of product analytics work done by business analysts and growth analysts at tech companies — answering the questions that actually matter for a SaaS product team:

- Where are users dropping off in the conversion funnel?
- Which features correlate with retention vs. churn?
- Which customer segments have the highest lifetime value?
- How does engagement differ across acquisition channels?

### Dataset

- **5,000 users**, **135,000+ product events**, **5,000 subscription records**
- Modeled on anonymized SaaS / e-commerce subscription patterns (similar to datasets available on Kaggle under subscription and e-commerce categories)
- Covers 18 months of product activity: Jan 2023 – Jun 2024
- Tables: `users`, `subscriptions`, `events`, `funnel_stages`

---

## Key Findings

### Funnel Analysis
| Stage | Users | Drop-off |
|---|---|---|
| Signed Up | 5,000 | — |
| Activated (7-day) | 2,048 | **–59%** ← biggest drop |
| Used Power Feature | 3,921 | — |
| Converted to Paid | 2,277 | 45.5% of signups |
| Retained 90 days | 2,000 | 40.0% of signups |

**→ Improving 7-day activation is the highest-leverage growth lever in the funnel.**

### Churn & Retention
| Plan | Churn Rate (lifetime) |
|---|---|
| Free | 96.3% |
| Starter | 87.2% |
| Growth | 68.0% |
| Enterprise | **43.7%** |

**→ Power feature adoption is the strongest predictor of retention:**
users who adopted 2+ power features (API Access, Automation Rules, Integrations, Team Invite) churned at **68.7%** vs **99.7%** for low-engagement users — a 31 percentage point difference.

### Customer Lifetime Value
| Channel | Avg LTV | Notes |
|---|---|---|
| Referral | **$419** | Highest LTV + highest conversion |
| Organic Search | $368 | Highest volume (1,459 users) |
| Direct | $366 | — |
| Paid Search | $351 | — |
| Social | $348 | — |
| Email Campaign | $327 | Lowest LTV + highest churn |

**→ Referral is the most efficient acquisition channel on every metric.**

### Plan LTV Breakdown
| Plan | Avg LTV | Avg Tenure |
|---|---|---|
| Enterprise | **$2,643** | 7.6 months |
| Growth | $570 | 5.8 months |
| Starter | $113 | 3.9 months |

**→ Enterprise LTV is 4.6× higher than Growth — upsell path is the clearest revenue lever.**

---

## Project Structure

```
saas-analytics/
├── data/
│   ├── saas_analytics.db      # SQLite database
│   ├── users.csv
│   ├── subscriptions.csv
│   ├── events.csv
│   └── funnel_stages.csv
├── sql/
│   ├── 01_funnel_analysis.sql
│   ├── 02_churn_retention.sql
│   ├── 03_ltv_segmentation.sql
│   └── 04_engagement_by_channel.sql
├── dashboard/
│   ├── index.html             # Interactive analytics dashboard
│   └── data.json              # Pre-computed query results
├── generate_dataset.py        # Dataset generation script
├── run_analysis.py            # Runs all SQL queries, outputs data.json
└── README.md
```

---

## How to Run

**1. Generate the dataset**
```bash
python generate_dataset.py
```

**2. Run the SQL analysis**
```bash
python run_analysis.py
```

**3. Open the dashboard**

Open `dashboard/index.html` in any browser. No server required — the dashboard is fully self-contained.

**4. Explore the SQL directly**
```bash
sqlite3 data/saas_analytics.db
sqlite> .read sql/01_funnel_analysis.sql
sqlite> .read sql/02_churn_retention.sql
sqlite> .read sql/03_ltv_segmentation.sql
sqlite> .read sql/04_engagement_by_channel.sql
```

---

## Dashboard Sections

| Tab | What it shows |
|---|---|
| **Overview** | KPI summary, funnel snapshot, churn by plan, LTV by channel |
| **Funnel Analysis** | Full funnel, stage-by-stage drop-off, channel-level funnel performance |
| **Churn & Retention** | Churn by plan/channel, feature engagement vs churn correlation |
| **LTV & Revenue** | LTV by plan and channel, MRR trend over time |
| **Engagement** | Avg events per user, feature adoption, channel performance scorecard |

---

## Skills Demonstrated

- **SQL** — window functions, CTEs, aggregations, multi-table joins across 4 tables
- **Funnel analysis** — stage-by-stage conversion tracking, drop-off identification
- **Churn modeling** — cohort-level churn, feature engagement correlation with retention
- **Customer segmentation** — LTV by acquisition channel, plan tier analysis
- **Data storytelling** — turning query output into actionable business insights
- **Dashboard design** — single-file interactive HTML/JS dashboard with Chart.js

---

## Tech Stack

- **Python 3** — dataset generation, analysis runner
- **SQLite** — SQL layer (all analysis queries run as plain SQL)
- **Chart.js** — dashboard visualizations
- **HTML/CSS/JS** — fully self-contained interactive dashboard

---
