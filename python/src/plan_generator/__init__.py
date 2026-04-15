"""
Plan Generator package.

Provides rule-based plan generation (Step 2 of the 4-step pipeline).
Generates plan tables (Project_Plan, Deliverable, Project_Billing_Rate,
Deliverable_Title_Plan_Mapping) from template definitions before the DES runs.
"""

from .plan_generator import PlanGenerator
from .plan_parser import parse_plan_config, parse_plan_config_from_string

__all__ = ['PlanGenerator', 'parse_plan_config', 'parse_plan_config_from_string']
