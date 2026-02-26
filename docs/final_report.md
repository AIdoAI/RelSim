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
| **Consultant_Title_History** | 0 | Promotion chain records (populated via post-processing script) |
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
