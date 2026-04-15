# RelSim — Script Reference

Each script has one job. They run in the order shown below.

---

## Config files

### `consulting_db.yaml`
Defines the **13-table schema** for the consulting firm database — table names, column names, types, and row counts for the static tables (Region, Client, Business_Unit, Title, Consultant). Simulation-populated tables are listed here too so SQLite creates them empty before the DES runs.

### `consulting_sim.yaml`
Defines the **discrete-event simulation** — how projects arrive (EXPO(30) days), the 5-deliverable workflow each project goes through, resource requirements per deliverable phase, simulation duration (3650 days from 2020-01-01), and snapshot settings.

### `consulting_plan.yaml`
Defines the **rule-based plan generator** (Step 2 in the 4-step pipeline). Specifies project templates: how many deliverables, what types, planned billing rates per title, and staffing plan. Used only with the `generate-plan-simulate` command.

---

## Post-processing scripts
These run automatically after every simulation via hooks in `runner.py`. They fill fields the DES cannot set declaratively.

### `generate_title_history.py`
Fills `Consultant_Title_History`. For each consultant, generates 1–3 rows representing their career progression — title, salary (by seniority band), start/end dates, and whether they are still active.

### `fix_billing_rates.py`
Fills `Project_Billing_Rate.TitleID` and `BillingRate`, and `Deliverable_Title_Plan_Mapping.TitleID`. The DES creates these rows during simulation but leaves TitleID NULL. This script assigns TitleIDs cyclically (101–106) and draws rates from title-specific normal distributions.

### `calculate_financials.py`
Fills all remaining date and financial fields:
- `Deliverable` — ActualStartDate, ActualEndDate, PlannedStartDate, PlannedEndDate (from Consultant_Deliverable_Mapping), PlannedExpense (UNIF 2000–15000), DeliverableFixedPrice (split from project Fixed_Price_Amount for Fixed-Price contracts)
- `Project_Plan` — PlannedStartDate, PlannedEndDate, PlannedHours, EstimatedBudget
- `Actual_Project_Expense.Date` — copied from created_at

Must run after `fix_billing_rates.py` because EstimatedBudget joins on TitleID.

---

## Utility scripts

### `export_to_csv.py`
Exports every table from the most recent simulation DB to a matching CSV folder. Run this after any simulation to get flat files for analysis. Automatically finds the newest `.db` file in `output/`.

### `main.py`
The CLI entry point. Key commands:
- `generate-simulate` — generate static tables + run DES (used by the UI)
- `generate-plan-simulate` — full 4-step pipeline including rule-based plan generation
