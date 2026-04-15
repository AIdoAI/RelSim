# RelSim — Walkthrough

## What this project does

RelSim generates a realistic synthetic relational database for a consulting firm. It simulates 10 years of operations — projects arriving, consultants being assigned, deliverables being completed — and produces a fully populated SQLite database with 13 tables ready for analysis or teaching.

---

## The 4-step pipeline

```
Step 1  Generate static tables     Region, Client, Business_Unit, Title, Consultant
Step 2  Generate project plans      Project_Plan, Deliverable, billing rates, staffing plans
Step 3  Run the simulation (DES)    Consultant_Deliverable_Mapping, Expenses, Progress
Step 4  Post-processing             Dates, financials, title history, snapshots
```

Steps 1–3 run in one command. Step 4 runs automatically as hooks at the end of Step 3.

---

## Running a simulation

### From the UI
Open the Electron app, configure the database and simulation canvases, and click Run. All 4 steps happen automatically.

### From the CLI (from the `python/` folder)

```bash
# Standard run (Steps 1 + 3 + 4)
python main.py generate-simulate consulting_db.yaml consulting_sim.yaml

# Full 4-step pipeline with rule-based plan generation
python main.py generate-plan-simulate consulting_db.yaml consulting_plan.yaml consulting_sim.yaml
```

---

## Output structure

Every run creates a new folder under `output/`:

```
output/{run-id}/
  generated_{timestamp}.db        — the SQLite database (all 13 tables)
  generated_{timestamp}/          — CSV export of every table
  snapshots/                      — point-in-time CSV snapshots
    2020-12-31/
      projects.csv
      deliverables.csv
    2021-12-31/
      ...
  logs/                           — detailed run logs
```

To export CSVs from the most recent run at any time:
```bash
python export_to_csv.py
```

---

## Snapshot settings

Controlled in `consulting_sim.yaml`:

```yaml
simulation:
  snapshot_enabled: true          # false = skip snapshots entirely
  snapshot_interval_days: 365     # 30=monthly  90=quarterly  180=biannual  365=annual
```

Each snapshot folder contains `projects.csv` (all projects with their status at that date) and `deliverables.csv` (% complete per deliverable at that date).

---

## The 13 tables

| Table | Populated by |
|---|---|
| Region | Step 1 — static generator |
| Client | Step 1 — static generator |
| Business_Unit | Step 1 — static generator |
| Title | Step 1 — static generator |
| Consultant | Step 1 — static generator |
| Consultant_Title_History | Step 4 — `generate_title_history.py` |
| Project_Plan | Step 3 — DES (dates + financials filled by Step 4) |
| Project_Billing_Rate | Step 3 — DES (TitleIDs + rates filled by Step 4) |
| Deliverable | Step 3 — DES (dates + expenses filled by Step 4) |
| Deliverable_Title_Plan_Mapping | Step 3 — DES (TitleIDs filled by Step 4) |
| Consultant_Deliverable_Mapping | Step 3 — DES |
| Actual_Project_Expense | Step 3 — DES (Date filled by Step 4) |
| Deliverable_Progress_Month | Step 4 — SnapshotManager |

---

## Adjusting the simulation

| What to change | Where |
|---|---|
| Number of consultants, clients, regions | `consulting_db.yaml` — row counts |
| Project arrival rate | `consulting_sim.yaml` — `EXPO(30)` interarrival |
| Simulation duration | `consulting_sim.yaml` — `TIME(3650)` |
| Deliverable workflow | `consulting_sim.yaml` — event_flows steps |
| Billing rate distributions | `fix_billing_rates.py` — `TITLE_RATES` dict |
| Snapshot interval | `consulting_sim.yaml` — `snapshot_interval_days` |
