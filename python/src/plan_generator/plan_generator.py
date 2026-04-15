"""
Rule-Based Plan Generator (Step 2 of the 4-step pipeline).

Given a plan configuration (templates), this module:
1. Generates project arrival times based on the arrival distribution
2. For each project: selects a template, creates the Project_Plan row
3. Creates Deliverable rows based on the template's work breakdown
4. Creates Project_Billing_Rate rows (one per title per project)
5. Creates Deliverable_Title_Plan_Mapping rows (one per title per deliverable)

This runs AFTER Phase 1 (static table generation) and BEFORE Phase 3 (DES execution).
"""

import logging
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

from .plan_parser import PlanConfig, ProjectTemplate, DeliverableTemplate

logger = logging.getLogger(__name__)

# Lazy import — distributions are used dynamically
_distributions_imported = False
_generate_fn = None


def _ensure_distributions():
    """Lazy-import the distribution system."""
    global _distributions_imported, _generate_fn
    if not _distributions_imported:
        from ..distributions.core import generate_from_distribution
        _generate_fn = generate_from_distribution
        _distributions_imported = True


def _sample_distribution(formula: str) -> float:
    """Sample a value from a distribution formula string."""
    _ensure_distributions()
    # generate_from_distribution accepts a formula string directly
    return _generate_fn(formula)


class PlanGenerator:
    """
    Template-driven plan generator.

    Populates plan tables (Project_Plan, Deliverable, Project_Billing_Rate,
    Deliverable_Title_Plan_Mapping) from declarative template definitions.
    """

    def __init__(self, config: PlanConfig, db_path: Union[str, Path]):
        self.config = config
        self.db_path = str(db_path)
        self._rng = random.Random(config.arrival.random_seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self) -> Dict[str, int]:
        """
        Run the full plan generation pipeline.

        Returns:
            Dict mapping table name → number of rows inserted.
        """
        logger.info("Starting plan generation (Step 2)")
        stats: Dict[str, int] = {}

        # 1. Determine project arrival times
        arrival_times = self._generate_arrival_times()
        logger.info(f"Generated {len(arrival_times)} project arrival times "
                    f"over {self.config.arrival.simulation_duration} days")

        # 2. Read lookup data (Titles, Clients, Business Units) from the DB
        lookup = self._load_lookup_data()

        # 3. Generate plans for each project
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        cur = conn.cursor()

        try:
            projects_created = 0
            deliverables_created = 0
            billing_rows = 0
            mapping_rows = 0

            for arrival_day in arrival_times:
                # Select template (weighted by probability)
                template = self._select_template()

                # Create project row
                project_id = self._create_project(
                    cur, template, arrival_day, lookup
                )
                if project_id is None:
                    continue
                projects_created += 1

                # Create deliverable rows
                deliv_ids = self._create_deliverables(
                    cur, template, project_id, arrival_day
                )
                deliverables_created += len(deliv_ids)

                # Create billing rate rows
                br_count = self._create_billing_rates(
                    cur, template, project_id, lookup['title_ids']
                )
                billing_rows += br_count

                # Create title plan mapping rows
                tm_count = self._create_title_plan_mappings(
                    cur, template, deliv_ids, lookup['title_ids']
                )
                mapping_rows += tm_count

            conn.commit()

            stats = {
                template.project_table: projects_created,
                template.deliverables.table: deliverables_created,
                template.billing_rates.table: billing_rows,
                template.title_plan_mapping.table: mapping_rows,
            } if self.config.templates else {}

            logger.info(f"Plan generation complete: {stats}")

        except Exception as e:
            conn.rollback()
            logger.error(f"Plan generation failed: {e}", exc_info=True)
            raise
        finally:
            conn.close()

        return stats

    # ------------------------------------------------------------------
    # Arrival time generation
    # ------------------------------------------------------------------

    def _generate_arrival_times(self) -> List[float]:
        """Generate project arrival times using the configured distribution."""
        _ensure_distributions()
        times: List[float] = []
        clock = 0.0
        duration = self.config.arrival.simulation_duration

        # Convert time_unit to days if needed
        time_unit = self.config.arrival.time_unit
        unit_factor = {'minutes': 1 / 1440, 'hours': 1 / 24,
                       'days': 1.0, 'weeks': 7.0}.get(time_unit, 1.0)

        while clock < duration:
            interarrival = _sample_distribution(self.config.arrival.formula)
            interarrival_days = interarrival * unit_factor
            clock += interarrival_days
            if clock < duration:
                times.append(clock)

        return times

    # ------------------------------------------------------------------
    # Template selection
    # ------------------------------------------------------------------

    def _select_template(self) -> ProjectTemplate:
        """Select a template weighted by probability."""
        if len(self.config.templates) == 1:
            return self.config.templates[0]

        probs = [t.probability for t in self.config.templates]
        total = sum(probs)
        r = self._rng.random() * total
        cumulative = 0.0
        for t in self.config.templates:
            cumulative += t.probability
            if r <= cumulative:
                return t
        return self.config.templates[-1]

    # ------------------------------------------------------------------
    # Lookup data
    # ------------------------------------------------------------------

    def _load_lookup_data(self) -> Dict[str, Any]:
        """Load reference data (titles, clients, business units) from the DB."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        lookup: Dict[str, Any] = {}

        try:
            cur.execute("SELECT TitleID FROM Title ORDER BY TitleID")
            lookup['title_ids'] = [int(r[0]) for r in cur.fetchall()]
            if not lookup['title_ids']:
                lookup['title_ids'] = [101, 102, 103, 104, 105, 106]

            cur.execute("SELECT ClientID FROM Client")
            lookup['client_ids'] = [r[0] for r in cur.fetchall()]

            cur.execute("SELECT BusinessUnitID FROM Business_Unit")
            lookup['bu_ids'] = [r[0] for r in cur.fetchall()]
        finally:
            conn.close()

        return lookup

    # ------------------------------------------------------------------
    # Project creation
    # ------------------------------------------------------------------

    def _create_project(self, cur: sqlite3.Cursor, template: ProjectTemplate,
                        arrival_day: float,
                        lookup: Dict[str, Any]) -> Optional[int]:
        """Create a single Project_Plan row and return its ID."""
        start_date = datetime.strptime(self.config.arrival.start_date, "%Y-%m-%d")
        project_date = start_date + timedelta(days=arrival_day)

        attrs = template.project_attributes
        values: Dict[str, Any] = {}

        # Resolve each attribute
        for attr_name, attr_def in attrs.items():
            if isinstance(attr_def, str):
                values[attr_name] = attr_def
            elif isinstance(attr_def, dict):
                if 'formula' in attr_def:
                    values[attr_name] = _sample_distribution(attr_def['formula'])
                elif 'faker' in attr_def:
                    values[attr_name] = self._fake_value(attr_def['faker'])
                elif 'foreign_key' in attr_def:
                    fk = attr_def['foreign_key']
                    fk_table = fk.get('table', '')
                    if fk_table == 'Client':
                        values[attr_name] = self._rng.choice(lookup['client_ids'])
                    elif fk_table == 'Business_Unit':
                        values[attr_name] = self._rng.choice(lookup['bu_ids'])
                    else:
                        values[attr_name] = None
            else:
                values[attr_name] = attr_def

        values['PlannedStartDate'] = project_date.strftime('%Y-%m-%d')
        values['created_at'] = project_date.isoformat()

        # Build INSERT
        columns = list(values.keys())
        placeholders = ', '.join(['?'] * len(columns))
        col_str = ', '.join([f'[{c}]' for c in columns])

        cur.execute(
            f"INSERT INTO [{template.project_table}] ({col_str}) VALUES ({placeholders})",
            list(values.values())
        )
        return cur.lastrowid

    # ------------------------------------------------------------------
    # Deliverable creation
    # ------------------------------------------------------------------

    def _create_deliverables(self, cur: sqlite3.Cursor,
                             template: ProjectTemplate,
                             project_id: int,
                             arrival_day: float) -> List[int]:
        """Create Deliverable rows for a project and return their IDs."""
        start_date = datetime.strptime(self.config.arrival.start_date, "%Y-%m-%d")
        project_date = start_date + timedelta(days=arrival_day)

        deliv_table = template.deliverables.table
        deliv_ids: List[int] = []

        for dt in template.deliverables.items:
            values: Dict[str, Any] = {
                'ProjectID': project_id,
                'DeliverableName': dt.name,
                'PlannedStartDate': project_date.strftime('%Y-%m-%d'),
                'created_at': project_date.isoformat(),
            }

            # Calculate planned end date from duration estimate
            if dt.duration_estimate and 'formula' in dt.duration_estimate:
                duration_days = _sample_distribution(dt.duration_estimate['formula'])
                tu = dt.duration_estimate.get('time_unit', 'days')
                factor = {'minutes': 1 / 1440, 'hours': 1 / 24,
                          'days': 1.0, 'weeks': 7.0}.get(tu, 1.0)
                duration_days *= factor
                end_date = project_date + timedelta(days=max(1, duration_days))
                values['PlannedEndDate'] = end_date.strftime('%Y-%m-%d')

            columns = list(values.keys())
            placeholders = ', '.join(['?'] * len(columns))
            col_str = ', '.join([f'[{c}]' for c in columns])

            cur.execute(
                f"INSERT INTO [{deliv_table}] ({col_str}) VALUES ({placeholders})",
                list(values.values())
            )
            deliv_ids.append(cur.lastrowid)

        return deliv_ids

    # ------------------------------------------------------------------
    # Billing rate creation
    # ------------------------------------------------------------------

    def _create_billing_rates(self, cur: sqlite3.Cursor,
                              template: ProjectTemplate,
                              project_id: int,
                              title_ids: List[int]) -> int:
        """Create billing rate rows (one per title per project)."""
        br_config = template.billing_rates
        count = 0

        for tid in title_ids:
            rate_params = br_config.title_rates.get(tid, {'mean': 275, 'std': 50})
            mean = rate_params.get('mean', 275)
            std = rate_params.get('std', 50)
            rate = round(max(50.0, self._rng.gauss(mean, std)), 2)

            cur.execute(
                f"INSERT INTO [{br_config.table}] (ProjectID, TitleID, BillingRate) "
                f"VALUES (?, ?, ?)",
                (project_id, tid, rate)
            )
            count += 1

        return count

    # ------------------------------------------------------------------
    # Title plan mapping creation
    # ------------------------------------------------------------------

    def _create_title_plan_mappings(self, cur: sqlite3.Cursor,
                                    template: ProjectTemplate,
                                    deliv_ids: List[int],
                                    title_ids: List[int]) -> int:
        """Create title plan mapping rows (one per title per deliverable)."""
        tpm_config = template.title_plan_mapping
        hours_formula = tpm_config.planned_hours.get('formula', 'UNIF(30, 120)')
        count = 0

        for did in deliv_ids:
            for tid in title_ids:
                planned_hours = round(_sample_distribution(hours_formula), 2)
                cur.execute(
                    f"INSERT INTO [{tpm_config.table}] (DeliverableID, TitleID, PlannedHours) "
                    f"VALUES (?, ?, ?)",
                    (did, tid, planned_hours)
                )
                count += 1

        return count

    # ------------------------------------------------------------------
    # Faker helper
    # ------------------------------------------------------------------

    def _fake_value(self, method: str) -> str:
        """Generate a fake value using the faker method string."""
        try:
            from ..generator.data.faker_js.faker_bridge import FakerBridge
            faker = FakerBridge()
            return faker.generate(method)
        except Exception:
            # Fallback if faker bridge not available
            return f"Generated-{self._rng.randint(1000, 9999)}"
