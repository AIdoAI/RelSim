# Consulting Firm Simulation Project Report

## 1. Executive Summary
This project implemented a discrete event simulation for a Consulting Firm using **RelSim**. The simulation models the lifecycle of consulting projects, from inception through consultation and development to release, utilizing a realistic workforce of Managers, Developers, and Tech Support staff.

## 2. Implemented Configuration
The core of the simulation is defined in two YAML configuration files:

### 2.1 Database Schema (`python/consulting_db.yaml`)
Defines the structure of the synthetic database.
*   **Resources (`Employee`)**: 15 employees with roles (Manager, Developer, Tech Support) and attributes like salary and skills.
*   **Clients (`Company`)**: 5 client companies from various industries.
*   **Entities (`Project`)**: dynamic entities created during simulation with attributes like budget, status, and deadlines.
*   **Relationships**: Connects Employees to Skills (`SkillEmployee`) and Projects to Companies.

### 2.2 Simulation Logic (`python/consulting_sim.yaml`)
Defines the operational flow and logic.
*   **Timeframe**: 100 hours of operation.
*   **Workforce**:
    *   2 Tech Support
    *   1 Developer
    *   1 Manager
*   **Project Lifecycle Flow**:
    1.  **Project Creation**: Projects arrive exponentially (avg every 2 hours).
    2.  **Initial Consultation**: Requires a `Manager` (1 hour).
    3.  **Development Phase**: Requires a `Developer` (4 hours).
    4.  **QA/Support Review**: Requires `Tech Support` (2 hours).
    5.  **Completion**: Status updated to "Completed" and project released.

## 3. Tooling & Scripts
Custom Python scripts were developed to enhance the RelSim workflow:

*   **`register_project.py`**:
    *   **Purpose**: Integrates the manually generated simulation with the RelSim Electron UI.
    *   **Function**: Registers the project in the internal `configs.db` and structures the output directories correctly.
*   **`export_to_csv.py`**:
    *   **Purpose**: Provides data accessibility.
    *   **Function**: Exports all SQLite database tables to CSV format in `output/csv/`.

## 4. Generated Output
*   **Database**: `output/consulting.db` (SQLite database containing all simulation data).
*   **CSV Exports**: Located in `output/csv/`, including:
    *   `Project.csv`: List of all 60+ generated projects.
    *   `Employee.csv`: The staff roster.
    *   `sim_event_processing.csv`: Log of every simulation event and state change.

## 5. File Manifest
The following files were added or modified in the repository:

| File Path | Description |
|-----------|-------------|
| `python/consulting_db.yaml` | **[NEW]** Database schema definition. |
| `python/consulting_sim.yaml` | **[NEW]** Simulation rules and flow. |
| `register_project.py` | **[NEW]** Script to register project in UI. |
| `export_to_csv.py` | **[NEW]** Script to export data to CSV. |
| `docs/walkthrough.md` | **[NEW]** Step-by-step usage guide. |
| `docs/implementation_plan.md` | **[NEW]** Original technical plan. |
| `docs/task.md` | **[NEW]** Project task tracking. |
