"""
Residual post-processing for the consulting firm simulation.

Most derivations (Plan vs Actual dates, aggregates, CDM.Month, Expense.Date,
ordered-list FK assignment, billing rate distributions) are now handled
inline by the DES via YAML-declared `ordered_list` / `ordered_formulas`
generators and `assignment_type: sql` steps in consulting_sim.yaml.

This script only handles what can't yet be expressed declaratively:

1. Static table `created_at` — Region, Business_Unit, Title, Client.
   These rows exist before the simulation starts, so there is no
   entity context for an inline SQL assign.

2. Deliverable.DeliverableFixedPrice — a parent-to-child proportional
   split preserving the parent total. Needs a `parent_split` YAML
   primitive (not yet implemented).

3. Edge-case backfill — a few NULL values remain for projects that
   didn't reach mark_complete before the simulation ended.

Usage:
  python calculate_financials.py <path_to_db>
"""

import sys
import sqlite3
import random
from datetime import datetime, timedelta

# Anchor for pre-simulation history. Must match consulting_sim.yaml.
SIMULATION_START_DATE = "2020-01-01"
FIRM_AGE_YEARS = 5


def populate_static_created_at(cur) -> None:
    """Region, Business_Unit, Title get firm founding date; Client gets a
    uniform random date between founding and simulation start."""
    sim_start = datetime.strptime(SIMULATION_START_DATE, "%Y-%m-%d")
    firm_founding = sim_start - timedelta(days=365 * FIRM_AGE_YEARS)
    founding_str = firm_founding.strftime("%Y-%m-%d")

    for tbl in ("Region", "Business_Unit", "Title"):
        cur.execute(
            f"UPDATE {tbl} SET created_at = ? WHERE created_at IS NULL",
            (founding_str,),
        )
        if cur.rowcount > 0:
            print(f"Set {tbl}.created_at for {cur.rowcount} rows.")

    cur.execute("SELECT ClientID FROM Client WHERE created_at IS NULL")
    client_ids = [row[0] for row in cur.fetchall()]
    if client_ids:
        founding_ts = firm_founding.timestamp()
        sim_start_ts = sim_start.timestamp()
        for cid in client_ids:
            ts = random.uniform(founding_ts, sim_start_ts)
            date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            cur.execute(
                "UPDATE Client SET created_at = ? WHERE ClientID = ?",
                (date_str, cid),
            )
        print(f"Set Client.created_at for {len(client_ids)} rows.")


def populate_deliverable_fixed_price(cur) -> None:
    """For Fixed-Price projects, split the project Fixed_Price_Amount
    across its deliverables with random weights that sum to the total."""
    cur.execute("""
        SELECT p.ProjectID, p.Fixed_Price_Amount
        FROM Project_Plan p
        WHERE p.ProjectType = 'Fixed-Price'
          AND p.Fixed_Price_Amount IS NOT NULL
    """)
    fixed_price_projects = cur.fetchall()
    deliv_count = 0
    for project_id, fixed_price_amount in fixed_price_projects:
        cur.execute("""
            SELECT DeliverableID FROM Deliverable
            WHERE ProjectID = ? AND DeliverableFixedPrice IS NULL
            ORDER BY DeliverableID
        """, (project_id,))
        delivs = [row[0] for row in cur.fetchall()]
        if not delivs:
            continue
        weights = [random.uniform(0.8, 1.2) for _ in delivs]
        total_weight = sum(weights)
        shares = [round(fixed_price_amount * w / total_weight, 2) for w in weights]
        shares[-1] = round(fixed_price_amount - sum(shares[:-1]), 2)
        for did, share in zip(delivs, shares):
            cur.execute(
                "UPDATE Deliverable SET DeliverableFixedPrice = ? WHERE DeliverableID = ?",
                (share, did),
            )
        deliv_count += len(delivs)
    if deliv_count > 0:
        print(f"Set DeliverableFixedPrice for {deliv_count} deliverables "
              f"({len(fixed_price_projects)} Fixed-Price projects).")


def backfill_edge_case_projects(cur) -> None:
    """Projects that didn't reach mark_complete before sim end have
    missing Plan/Actual fields. Fill them in using the same logic as
    the YAML SQL assigns (idempotent — only touches NULLs)."""
    cur.execute("""
        UPDATE Project_Plan
        SET PlannedStartDate = DATE(created_at)
        WHERE PlannedStartDate IS NULL AND created_at IS NOT NULL
    """)
    if cur.rowcount > 0:
        print(f"Backfilled Project_Plan.PlannedStartDate for {cur.rowcount} rows.")

    cur.execute("""
        UPDATE Deliverable
        SET PlannedStartDate = DATE(created_at)
        WHERE PlannedStartDate IS NULL AND created_at IS NOT NULL
    """)
    if cur.rowcount > 0:
        print(f"Backfilled Deliverable.PlannedStartDate for {cur.rowcount} rows.")


def calculate_financials(db_path: str) -> None:
    """Run residual post-processing that can't yet be expressed in YAML."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    populate_static_created_at(cur)
    populate_deliverable_fixed_price(cur)
    backfill_edge_case_projects(cur)

    conn.commit()

    # Short summary
    cur.execute("""
        SELECT COUNT(*),
               SUM(CASE WHEN PlannedStartDate IS NOT NULL THEN 1 ELSE 0 END),
               SUM(CASE WHEN ActualStartDate  IS NOT NULL THEN 1 ELSE 0 END),
               SUM(CASE WHEN EstimatedBudget  > 0         THEN 1 ELSE 0 END)
        FROM Project_Plan
    """)
    r = cur.fetchone()
    print(f"\nProject_Plan ({r[0]} projects): "
          f"PlannedStart={r[1]}  ActualStart={r[2]}  EstimatedBudget={r[3]}")

    conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <path_to_db>")
        sys.exit(1)
    calculate_financials(sys.argv[1])
