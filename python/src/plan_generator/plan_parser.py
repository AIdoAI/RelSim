"""
Plan configuration parser.

Parses the plan_generation YAML section into structured dataclasses
for use by the PlanGenerator.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ArrivalConfig:
    """Configuration for project arrival patterns."""
    formula: str = "EXPO(30)"
    time_unit: str = "days"
    simulation_duration: float = 3650  # days
    start_date: str = "2020-01-01"
    random_seed: Optional[int] = 42


@dataclass
class ResourceRequirement:
    """Resource requirement for a deliverable."""
    resource_type: str = ""
    count: int = 1


@dataclass
class DeliverableTemplate:
    """Template for a single deliverable within a project."""
    name: str = ""
    sequence: int = 0
    duration_estimate: Dict[str, Any] = field(default_factory=dict)
    resource_requirements: List[ResourceRequirement] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)


@dataclass
class BillingRateConfig:
    """Configuration for billing rate generation."""
    table: str = "Project_Billing_Rate"
    per_title: bool = True
    title_rates: Dict[int, Dict[str, float]] = field(default_factory=dict)


@dataclass
class TitlePlanMappingConfig:
    """Configuration for title plan mapping generation."""
    table: str = "Deliverable_Title_Plan_Mapping"
    per_title: bool = True
    planned_hours: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeliverableConfig:
    """Configuration for deliverable generation."""
    table: str = "Deliverable"
    items: List[DeliverableTemplate] = field(default_factory=list)


@dataclass
class ProjectTemplate:
    """Template defining how a project type is structured."""
    name: str = ""
    probability: float = 1.0
    project_table: str = "Project_Plan"
    project_attributes: Dict[str, Any] = field(default_factory=dict)
    deliverables: DeliverableConfig = field(default_factory=DeliverableConfig)
    billing_rates: BillingRateConfig = field(default_factory=BillingRateConfig)
    title_plan_mapping: TitlePlanMappingConfig = field(default_factory=TitlePlanMappingConfig)


@dataclass
class PlanConfig:
    """Top-level plan generation configuration."""
    arrival: ArrivalConfig = field(default_factory=ArrivalConfig)
    templates: List[ProjectTemplate] = field(default_factory=list)


def _parse_arrival(data: dict) -> ArrivalConfig:
    """Parse arrival configuration."""
    dist = data.get('distribution', {})
    return ArrivalConfig(
        formula=dist.get('formula', 'EXPO(30)'),
        time_unit=dist.get('time_unit', 'days'),
        simulation_duration=data.get('simulation_duration', 3650),
        start_date=data.get('start_date', '2020-01-01'),
        random_seed=data.get('random_seed', 42),
    )


def _parse_resource_requirements(data: list) -> List[ResourceRequirement]:
    """Parse resource requirements list."""
    reqs = []
    for item in (data or []):
        reqs.append(ResourceRequirement(
            resource_type=item.get('resource_type', ''),
            count=item.get('count', 1),
        ))
    return reqs


def _parse_deliverable_template(data: dict) -> DeliverableTemplate:
    """Parse a single deliverable template."""
    return DeliverableTemplate(
        name=data.get('name', ''),
        sequence=data.get('sequence', 0),
        duration_estimate=data.get('duration_estimate', {}),
        resource_requirements=_parse_resource_requirements(data.get('resource_requirements')),
        depends_on=data.get('depends_on', []),
    )


def _parse_deliverables(data: dict) -> DeliverableConfig:
    """Parse deliverable configuration."""
    items = [_parse_deliverable_template(d) for d in data.get('items', [])]
    return DeliverableConfig(
        table=data.get('table', 'Deliverable'),
        items=items,
    )


def _parse_billing_rates(data: dict) -> BillingRateConfig:
    """Parse billing rate configuration."""
    raw_rates = data.get('title_rates', {})
    # Convert string keys to int
    title_rates = {int(k): v for k, v in raw_rates.items()}
    return BillingRateConfig(
        table=data.get('table', 'Project_Billing_Rate'),
        per_title=data.get('per_title', True),
        title_rates=title_rates,
    )


def _parse_title_plan_mapping(data: dict) -> TitlePlanMappingConfig:
    """Parse title plan mapping configuration."""
    return TitlePlanMappingConfig(
        table=data.get('table', 'Deliverable_Title_Plan_Mapping'),
        per_title=data.get('per_title', True),
        planned_hours=data.get('planned_hours', {}),
    )


def _parse_template(data: dict) -> ProjectTemplate:
    """Parse a single project template."""
    deliverables_data = data.get('deliverables', {})
    billing_data = data.get('billing_rates', {})
    mapping_data = data.get('title_plan_mapping', {})

    return ProjectTemplate(
        name=data.get('name', ''),
        probability=data.get('probability', 1.0),
        project_table=data.get('project_table', 'Project_Plan'),
        project_attributes=data.get('project_attributes', {}),
        deliverables=_parse_deliverables(deliverables_data),
        billing_rates=_parse_billing_rates(billing_data),
        title_plan_mapping=_parse_title_plan_mapping(mapping_data),
    )


def _parse_plan_generation(data: dict) -> PlanConfig:
    """Parse the top-level plan_generation block."""
    pg = data.get('plan_generation', data)
    arrival = _parse_arrival(pg.get('arrival', {}))
    templates = [_parse_template(t) for t in pg.get('templates', [])]
    return PlanConfig(arrival=arrival, templates=templates)


def parse_plan_config(file_path: str) -> PlanConfig:
    """Parse a plan configuration from a YAML file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Plan configuration file not found: {file_path}")

    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    logger.info(f"Parsed plan config from {file_path}")
    return _parse_plan_generation(data)


def parse_plan_config_from_string(content: str) -> PlanConfig:
    """Parse a plan configuration from a YAML string."""
    data = yaml.safe_load(content)
    logger.info("Parsed plan config from content string")
    return _parse_plan_generation(data)
