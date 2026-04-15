"""
Snapshot Manager for DES

At simulation end, writes one subfolder per snapshot date under:
  {run_dir}/snapshots/{YYYY-MM-DD}/
    projects.csv    — state of all Project_Plan rows at that date
    deliverables.csv — each deliverable's % complete at that date

Also writes the same deliverable progress rows into the
Deliverable_Progress_Month DB table (used by the main export).

YAML settings (simulation: section):
  snapshot_enabled: true        # set false to skip entirely
  snapshot_interval_days: 365   # 30=monthly, 90=quarterly, 180=biannual, 365=annual
"""

import logging
import os
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class SnapshotManager:
    def __init__(self, env, engine, config):
        self.env = env
        self.engine = engine
        self.config = config

        # --- start date ---
        try:
            if hasattr(config, 'simulation') and hasattr(config.simulation, 'start_date'):
                start_date_str = config.simulation.start_date
            elif hasattr(config, 'start_date'):
                start_date_str = config.start_date
            else:
                start_date_str = '2020-01-01'
            self.start_date = datetime.strptime(str(start_date_str), '%Y-%m-%d')
        except Exception as e:
            logger.warning(f"SnapshotManager: failed to parse start_date: {e}")
            self.start_date = datetime(2020, 1, 1)

        # --- settings from config ---
        self.enabled = bool(getattr(config, 'snapshot_enabled', True))
        self.interval_days = int(getattr(config, 'snapshot_interval_days', 30))

        # --- output folder: {run_dir}/snapshots/ ---
        # engine.url.database gives the absolute path to the .db file;
        # its parent is the run directory (e.g. output/{run_id}/)
        try:
            db_path = engine.url.database
            self.snapshots_dir = Path(db_path).parent / 'snapshots'
        except Exception:
            self.snapshots_dir = Path('snapshots')

        if self.enabled:
            logger.info(
                f"SnapshotManager: enabled=True  interval={self.interval_days}d  "
                f"folder={self.snapshots_dir}"
            )
        else:
            logger.info("SnapshotManager: disabled — no snapshots will be written")

    # ------------------------------------------------------------------
    # SimPy process (no-op: all work deferred to flush for performance)
    # ------------------------------------------------------------------

    def run_periodic_snapshots(self):
        """No-op during execution — generation deferred to flush."""
        yield self.env.timeout(0)

    # ------------------------------------------------------------------
    # Called once at simulation end
    # ------------------------------------------------------------------

    def flush_to_database(self):
        """Generate all snapshots and write to both DB rows and CSV files."""
        if not self.enabled:
            logger.info("SnapshotManager: skipping (disabled)")
            return
        try:
            logger.debug(f"SnapshotManager: generating snapshots (interval={self.interval_days}d)…")
            self._generate_deliverable_snapshots()
            self._generate_project_snapshots()
        except Exception as e:
            logger.error(f"SnapshotManager: failed — {e}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _snapshot_dates(self):
        """Return list of (sim_day, datetime) tuples at each interval boundary."""
        end_time = int(self.env.now / (24 * 60))   # SimPy minutes → days
        dates = []
        for sim_day in range(self.interval_days, end_time + self.interval_days, self.interval_days):
            dates.append((sim_day, self.start_date + timedelta(days=sim_day)))
        return dates

    def _ensure_snapshot_folder(self, date_str: str) -> Path:
        """Create and return the folder for a single snapshot date."""
        folder = self.snapshots_dir / date_str
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    # ------------------------------------------------------------------
    # Deliverable progress snapshots
    # ------------------------------------------------------------------

    def _generate_deliverable_snapshots(self):
        query = """
            SELECT d.DeliverableID, d.ProjectID, d.DeliverableName,
                   cdm.start_date AS ActualStartDate,
                   cdm.end_date   AS ActualEndDate
            FROM Deliverable d
            JOIN Consultant_Deliverable_Mapping cdm
                ON d.DeliverableID = cdm.DeliverableID
            WHERE cdm.start_date IS NOT NULL
        """
        try:
            df = pd.read_sql_query(query, self.engine)
            if df.empty:
                logger.warning("SnapshotManager: no Consultant_Deliverable_Mapping rows — skipping deliverable snapshots")
                return

            df['start_dt'] = pd.to_datetime(df['ActualStartDate'])
            df['end_dt']   = pd.to_datetime(df['ActualEndDate'], errors='coerce')

            # One row per deliverable: earliest start, latest end
            agg = (df.groupby(['DeliverableID', 'ProjectID', 'DeliverableName'])
                     .agg(start_dt=('start_dt', 'min'), end_dt=('end_dt', 'max'))
                     .reset_index())

            db_rows = []      # rows for Deliverable_Progress_Month table

            for sim_day, current_dt in self._snapshot_dates():
                date_str = current_dt.strftime('%Y-%m-%d')
                snapshot_rows = []

                for _, row in agg.iterrows():
                    start = row['start_dt']
                    end   = row['end_dt']

                    if pd.isna(start) or start > current_dt:
                        continue

                    total_days  = max(1, (end - start).days if not pd.isna(end) else self.interval_days)
                    days_elapsed = max(0, (current_dt - start).days)
                    pct = min(100.0, round((days_elapsed / total_days) * 100, 2))
                    if not pd.isna(end) and current_dt >= end:
                        pct = 100.0

                    snapshot_rows.append({
                        'DeliverableID':     row['DeliverableID'],
                        'ProjectID':         row['ProjectID'],
                        'DeliverableName':   row['DeliverableName'],
                        'SnapshotDate':      date_str,
                        'PercentageComplete': pct,
                    })
                    db_rows.append({
                        'DeliverableID':     row['DeliverableID'],
                        'Report_Month':      date_str,
                        'PercentageComplete': pct,
                    })

                # Write CSV for this snapshot date
                if snapshot_rows:
                    folder = self._ensure_snapshot_folder(date_str)
                    csv_path = folder / 'deliverables.csv'
                    pd.DataFrame(snapshot_rows).to_csv(csv_path, index=False)
                    logger.debug(f"SnapshotManager: wrote {len(snapshot_rows)} rows → {csv_path}")

            # Write all progress rows to DB table
            if db_rows:
                progress_df = pd.DataFrame(db_rows)[['DeliverableID', 'Report_Month', 'PercentageComplete']]
                progress_df.to_sql('Deliverable_Progress_Month', self.engine, if_exists='append', index=False)
                logger.info(
                    f"SnapshotManager: wrote {len(db_rows)} Deliverable_Progress_Month rows  "
                    f"({len(self._snapshot_dates())} snapshots, interval={self.interval_days}d)"
                )

        except Exception as e:
            logger.error(f"SnapshotManager: deliverable snapshot error — {e}")

    # ------------------------------------------------------------------
    # Project snapshots
    # ------------------------------------------------------------------

    def _generate_project_snapshots(self):
        query = """
            SELECT p.ProjectID, p.ClientID, p.BusinessUnitID,
                   p.ProjectName, p.ProjectType, p.ProjectStatus,
                   p.PlannedStartDate, p.PlannedEndDate,
                   p.PlannedHours, p.EstimatedBudget,
                   p.Fixed_Price_Amount, p.PlannedExpense,
                   p.created_at
            FROM Project_Plan p
        """
        try:
            df = pd.read_sql_query(query, self.engine)
            if df.empty:
                return

            df['created_dt'] = pd.to_datetime(df['created_at'], errors='coerce')
            df['planned_start_dt'] = pd.to_datetime(df['PlannedStartDate'], errors='coerce')
            df['planned_end_dt']   = pd.to_datetime(df['PlannedEndDate'],   errors='coerce')

            for sim_day, current_dt in self._snapshot_dates():
                date_str = current_dt.strftime('%Y-%m-%d')

                # Only include projects that existed at this snapshot date
                active = df[df['created_dt'] <= current_dt].copy()
                if active.empty:
                    continue

                # Derive inferred status at snapshot time
                def infer_status(row):
                    if pd.notna(row['planned_end_dt']) and current_dt >= row['planned_end_dt']:
                        return 'Complete'
                    if pd.notna(row['planned_start_dt']) and current_dt >= row['planned_start_dt']:
                        return 'In Progress'
                    return 'Not Started'

                active['StatusAtSnapshot'] = active.apply(infer_status, axis=1)
                active['SnapshotDate'] = date_str

                # Select output columns
                out = active[[
                    'SnapshotDate', 'ProjectID', 'ClientID', 'BusinessUnitID',
                    'ProjectName', 'ProjectType', 'StatusAtSnapshot',
                    'PlannedStartDate', 'PlannedEndDate',
                    'PlannedHours', 'EstimatedBudget', 'Fixed_Price_Amount'
                ]]

                folder = self._ensure_snapshot_folder(date_str)
                csv_path = folder / 'projects.csv'
                out.to_csv(csv_path, index=False)
                logger.debug(f"SnapshotManager: wrote {len(out)} project rows → {csv_path}")

            logger.info(
                f"SnapshotManager: wrote project CSVs for {len(self._snapshot_dates())} snapshots"
            )

        except Exception as e:
            logger.error(f"SnapshotManager: project snapshot error — {e}")
