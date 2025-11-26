"""UK Budget Data - Data generation pipeline for UK Autumn Budget dashboard."""

from uk_budget_data.models import DataConfig, Reform, ReformResult
from uk_budget_data.pipeline import DataPipeline, generate_all_data
from uk_budget_data.reforms import (
    AUTUMN_BUDGET_2025_REFORMS,
    create_salary_sacrifice_cap_reform,
    get_reform,
    list_reform_ids,
)

__version__ = "0.1.0"

__all__ = [
    # Models
    "DataConfig",
    "Reform",
    "ReformResult",
    # Pipeline
    "DataPipeline",
    "generate_all_data",
    # Reforms
    "AUTUMN_BUDGET_2025_REFORMS",
    "create_salary_sacrifice_cap_reform",
    "get_reform",
    "list_reform_ids",
]
