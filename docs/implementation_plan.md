# Implementation Plan - Consulting Firm Simulation

I will implement a synthetic database and simulation for a consulting firm as requested. This involves two configuration files: a database definition and a simulation definition.

## Proposed Changes

### Configuration Files

#### [NEW] [consulting_db.yaml](file:///Users/x1/Documents/GitHub/RelSim/consulting_db.yaml)
- Defines the database schema based on the "Consulting Firm" ERD.
- **Resource Table**: `Employee` (with specific roles: Tech Support, Developer, Manager).
- **Entity Table**: `Project`.
- **Supporting Tables**: `Company` (Client), `Skill`, `SkillEmployee` (Bridging).
- **Generators**: Uses Faker for names/emails, Distributions for roles/budgets.

#### [NEW] [consulting_sim.yaml](file:///Users/x1/Documents/GitHub/RelSim/consulting_sim.yaml)
- Defines the simulation flow.
- **Termination**: Time-based (e.g., 40 hours).
- **Resources**: Maps `Employee` table types to capacities (Tech Support: 2, Developer: 1, Manager: 1).
- **Flow**:
  1.  **Create**: `Project` arrivals (Interarrival: EXPO).
  2.  **Event**: `Consultation` (Requires Manager).
  3.  **Event**: `Development` (Requires Developer).
  4.  **Release**: Project completion.

## Verification Plan

### Automated Verification
- Run `python3 main.py generate consulting_db.yaml -o output -n consulting`
  - Verify `output/consulting.db` is created.
- Run `python3 main.py simulate consulting_sim.yaml consulting_db.yaml output/consulting.db`
  - Verify simulation completes without error.
