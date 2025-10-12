from enum import Enum
from typing import Any


# mu/loc of the normal continuous random variable
LOC: int | float = 1.5

# maximum number of characters of the process name
# to display on a figure
NAME_DISPLAY_LIMIT: int = 40

# maximum number of processes to plot on a figure
MAX_P: int = 10

# matplotlib settings
MPL_RUNTIME_CONFIG: dict[str, Any] = {
    "axes.spines.right": False,
    "axes.spines.top": False,
    "font.family": "Arial",
    "mathtext.fontset": "custom"
}

# matplotlib figure dpi
DPI_BULK: int = 400
DPI_SINGLE: int = 600


class SigmaSupremum(Enum):
    """
    The unreachable upper bound of the sigma interval that corresponds
    to the quality class.

    E.g., the RED class never reaches sigma=2.1 supremum which is the
    exact lower bound of the next, YELLOW, class and the YELLOW never
    reaches 4.1 which is the lower bound of the GREEN class.
    """

    RED: float = 2.1
    YELLOW: float = 4.1
    GREEN: float = float("inf")
