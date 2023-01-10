import logging
from functools import wraps
from typing import Any, Callable

from django.core.exceptions import ValidationError

from apps.wells.models import WellPlannerWizardStep

logger = logging.getLogger(__name__)


def require_well_step(
    *, allowed_steps: list[WellPlannerWizardStep], error: str, get_well: Callable | None = None
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if get_well:
                well_planner = get_well(*args, **kwargs)
            else:
                well_planner = kwargs['well_planner']
            if well_planner.current_step not in allowed_steps:
                logger.info(
                    f"Unable to call {func.__name__}. " f"Current step must be one of '{', '.join(allowed_steps)}'."
                )
                raise ValidationError(error)

            return func(*args, **kwargs)

        return wrapper

    return decorator
