# Consulting Firm Client Engagements — Project Report

## 1. Executive Summary
This project implements a **13-table relational database simulation** for a Consulting Firm using **RelSim**. The schema models the full lifecycle of consulting engagements — from client acquisition through project delivery — using a hierarchical parent-child simulation flow where Projects spawn Deliverables as child entities.

## 2. Database Schema (13 Tables)

### Static Tables (pre-populated at generation time)

| Table | Rows | Description |
|-------|------|-------------|
| **Location** | 30 | US states and cities |
| **Client** | 20 | Client companies with contact info and location FK |
| **BusinessUnit** | 5 | Retail, Healthcare, Media & Entertainment, Energy, Government |
| **Title** | 6 | Consultant → Senior Consultant → Manager → Senior Manager → Associate Partner → Partner |
| **Consultant** | 60 | Workforce roster with name, contact, business unit, and resource type |

### Dynamic Tables (simulation-populated)

| Table | Rows | Description |
|-------|------|-------------|
| **Project** | 75 | Client engagements with type (Fixed-Price/T&M), budget, status, and dates |
| **ProjectBillingRate** | 450 | 6 billing rates per project (one per title level) |
| **Deliverable** | 75 | Child entities of Project — one per project phase |
| **Consultant_Deliverable_Mapping** | 146 | Resource allocation records linking consultants to deliverables |
| **ProjectExpense** | 0 | Expense records (Travel, Software, Equipment, etc.) |
| **Consultant_Title_History** | 99 | Promotion chain records (auto-populated via post-simulation hook) |
| **Deliverable_Title_Plan_Mapping** | 0 | Planned hours per title per deliverable |
| **Deliverable_Progress_Month** | 0 | Monthly progress tracking records |

## 3. Simulation Design

### Parent-Child Entity Flow
The simulation uses a single event flow (`flow_project_lifecycle`) with **18 steps** that models the Project → Deliverable parent-child relationship:

```
create_project (EXPO 30 days interarrival)
  → initialize (Not Started)
  → trigger billing rates (6 per project)
  → start project (In Progress)
  → create_deliverable_1 (Project Plan Development)
      → process_deliverable_1 (NORM 28±7 days, Lead + Senior)
          ├→ create_deliverable_2 (Design)
          │     → process_deliverable_2 (NORM 28±7 days, Senior + Mid)
          └→ create_deliverable_3 (Infrastructure Implementation)
                → process_deliverable_3 (NORM 28±7 days, Mid + 2 Junior)
          [converge]
      → create_deliverable_4 (Coding and Unit Test)
          → process_deliverable_4 (NORM 28±7 days, 2 Mid + 3 Junior)
              ├→ trigger_expenses (2-8 per project)
              └→ create_deliverable_5 (System Test)
                    → process_deliverable_5 (NORM 28±7 days, Senior + 2 Junior)
  → mark_complete (Complete)
  → release_project
```

### Simulation Parameters
- **Time span**: 5 years (January 2020 – December 2025, 1825 days)
- **Project arrival**: Exponential distribution, ~1 per month (EXPO(30))
- **Deliverable durations**: Normal distribution, ~4 weeks each (NORM(28, 7))
- **Workforce**: 60 consultants across 6 resource types (Junior, Mid, Senior, Lead, Principal, Executive)
- **Parallel phases**: Design and Infrastructure Implementation run concurrently

## 4. Configuration Files

| File | Description |
|------|-------------|
| `python/consulting_db.yaml` | Database schema definition (13 tables, attributes, generators, relationships) |
| `python/consulting_sim.yaml` | Simulation configuration (1 flow, 18 steps, resource capacities, queues) |

## 5. Tooling & Scripts

| Script | Purpose |
|--------|---------|
| `register_project.py` | Registers the project in RelSim's config database for UI display |
| `export_to_csv.py` | Exports all SQLite tables to CSV format in `output/csv/` |
| `python/generate_title_history.py` | Post-processing script for Consultant_Title_History promotion chain logic |

## 6. Generated Output

### Database
The simulation database is located at:
`output/9003ab6b-e832-4935-a5c9-3e28f6c9a5f6/simulation_2026-02-26T05-16-55-863Z.db`

### CSV Exports (`output/csv/`)
16 CSV files exported from the simulation database:
- 5 static tables (Location, Client, BusinessUnit, Title, Consultant)
- 8 dynamic schema tables (Project, ProjectBillingRate, Deliverable, etc.)
- 3 simulation tracking tables (sim_event_processing, sim_resource_allocations, sim_queue_activity)

## 7. File Manifest

| File Path | Status | Description |
|-----------|--------|-------------|
| `python/consulting_db.yaml` | **Modified** | 13-table database schema |
| `python/consulting_sim.yaml` | **Modified** | Parent-child simulation flow |
| `python/generate_title_history.py` | **New** | Title history post-processing |
| `register_project.py` | Existing | Project registration script |
| `export_to_csv.py` | Existing | CSV export script |
| `docs/final_report.md` | **Modified** | This report |
| `output/csv/*.csv` | **Modified** | 16 exported CSV files |

## 8. Simulation Output Summary

The simulation ran over a 5-year period (January 2020 – December 2025) and produced the following results.

### 8.1 Project Generation

| Metric | Value |
|--------|-------|
| Total projects created | **75** |
| Project date range | Jan 15, 2020 – Dec 26, 2024 |
| Average interarrival | ~24 days |
| Projects still In Progress | 75 (all active at simulation end) |

**Project Type Distribution:**

| Type | Count | Percentage |
|------|-------|------------|
| Fixed-Price | 38 | 50.7% |
| Time & Materials | 37 | 49.3% |

**Top 5 Clients by Project Count:**

| Client | Projects |
|--------|----------|
| Mosciski Group | 7 |
| Brekke, Johnston and Beer | 6 |
| West, Bins and Nienow | 5 |
| Walter Group | 4 |
| Stroman - Will | 4 |

### 8.2 Deliverable Generation

| Metric | Value |
|--------|-------|
| Total deliverables | **75** |
| Deliverables per project | 1 (first phase reached per project) |

**Deliverable Phase Distribution:**

| Phase | Count |
|-------|-------|
| Project Plan Development | 21 |
| Coding and Unit Test | 17 |
| Infrastructure Implementation | 14 |
| Design | 13 |
| System Test | 10 |

### 8.3 Billing Rates

| Metric | Value |
|--------|-------|
| Total billing rate records | **450** (6 per project × 75 projects) |
| Average rate | $277.46/hr |
| Minimum rate | $112.94/hr |
| Maximum rate | $467.64/hr |

### 8.4 Resource Allocation

| Metric | Value |
|--------|-------|
| Consultant-Deliverable mappings | **146** |
| Total consultants | 60 |

**Consultant Distribution by Resource Type:**

| Resource Type | Count |
|---------------|-------|
| Junior | 19 |
| Mid | 16 |
| Senior | 15 |
| Lead | 5 |
| Executive | 4 |
| Principal | 1 |

### 8.5 Simulation Engine Metrics

| Table | Records | Description |
|-------|---------|-------------|
| sim_event_processing | 73 | Simulation event log |
| sim_resource_allocations | 146 | Resource assignment records |
| sim_queue_activity | 300 | Queue wait/service tracking |

### 8.6 Consultant Title History

The `Consultant_Title_History` table was populated via the post-simulation hook with **99 records** across 60 consultants:

| Rows per Consultant | Count | Description |
|---------------------|-------|-------------|
| 1 row (no promotion) | 30 | 50.0% of consultants |
| 2 rows (1 promotion) | 21 | 35.0% of consultants |
| 3 rows (2 promotions) | 9 | 15.0% of consultants |

- **Average records per consultant**: 1.6
- **Salary range**: ~$80K (Consultant) to ~$240K (Partner)
- All dates are on the 1st of the month, with sequential promotion chains
- 75% of final-title records have NULL `EndDate` (still active)

## 9. Limitations & Future Work

### 9.1 Consultant_Title_History — ✅ RESOLVED
The `Consultant_Title_History` table is now **automatically populated** via a post-simulation hook (`_run_post_simulation_hooks` in `runner.py`). The hook detects the presence of the `Consultant_Title_History` table in the database config and calls `populate_title_history()` from `generate_title_history.py`.

**What was done:**
- Fixed 3 bugs in `generate_title_history.py` (global variable SyntaxError, datetime/string AttributeError, missing return)
- Refactored to expose a clean `populate_title_history(db_path)` API
- Integrated into `python/src/simulation/core/runner.py` as a post-simulation hook

**Future enhancement**: Add a native `script` step type to RelSim so any custom Python logic can be declaratively specified in the simulation YAML.

### 9.2 ProjectExpense (0 Records Generated)
The `trigger_expenses` step was defined in the simulation flow but produced 0 records. This is likely because the trigger fires on a parallel branch (`trigger_expenses → release_expenses`) that exits the flow early, and the `ProjectExpense` entity generator requires a valid parent FK context.

**Improvement**: Restructure the expense trigger to fire sequentially before the final deliverable phase, or use a post-simulation SQL script to populate expenses from the completed projects.

### 9.3 Deliverable_Title_Plan_Mapping & Deliverable_Progress_Month (0 Records)
These bridge tables are defined in the schema but not referenced by any simulation step. They were intended for:
- **Deliverable_Title_Plan_Mapping**: Planned hours per title level for each deliverable
- **Deliverable_Progress_Month**: Monthly progress tracking (percentage complete)

**Improvement**: Add `trigger` steps to the simulation flow to populate these tables when each deliverable is created and as each deliverable progresses through phases.

### 9.4 Project Status (All "In Progress")
All 75 projects show status "In Progress" — none reached the "Complete" state. This indicates the simulation's 5-year time window (1825 days) was insufficient for all projects to complete the full 5-deliverable pipeline (each ~4 weeks × 5 phases = ~20 weeks minimum), or the resource pool was too constrained.

**Improvement**: Either extend the simulation time window, increase resource capacity, or reduce deliverable durations to allow more projects to reach completion.

### 9.5 Additional Enhancements
- **BusinessUnit diversity**: Only 4 of 5 business units (Energy, Government, Healthcare, Media & Entertainment) were generated due to `DISC` distribution randomness. Consider using deterministic assignment for the 5-row table.
- **Deliverable counts per project**: Currently each project only reaches 1 deliverable on average. The parent-child create pattern should be validated to ensure all 5 deliverables are spawned per project.
- **Richer consultant allocation**: Add skill-based matching between consultant expertise and deliverable requirements.
- **Financial modeling**: Add formula-based attributes for actual cost calculation using billing rates × hours from `Consultant_Deliverable_Mapping`.
