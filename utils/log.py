import traceback
import os

from datetime import datetime
from typing import Literal, Optional

from rich.align import Align
from rich.console import Console
from rich.panel import Panel

"""Colors used"""
class colors:
    # Purple themed
    light_purple = "#E6E6FA"
    medium_purple = "#9370DB"
    dark_purple = "#4B0082"
    pastel_purple = "#D8BFD8"
    soft_purple = "#B19CD9"
    deep_purple = "#800080"
    plum = "#DDA0DD"
    lilac = "#C8A2C8"
    eggplant = "#614051"
    black = "#000000"

    # Red themed
    light_red = "#D87272"
    medium_red = "#C44949"
    dark_red = "#3F0202"

    # Green themed
    light_green = "#72D877"
    medium_green = "#4EB32F"
    dark_green = "#073F02"

"""Fetch console + Width"""
console = Console()
console_width = console.size.width    


def printBox(
    text: str,
    color: Optional[Literal[
        'light_purple', 'medium_purple', 'dark_purple', 'pastel_purple', 'soft_purple',
        'deep_purple', 'plum', 'lilac', 'eggplant', 'black',
        'light_red', 'medium_red', 'dark_red',
        'light_green', 'medium_green', 'dark_green'
    ]] = None,
    title: Optional[str] = None,
    center: Optional[bool] = True
):
    """
    Prints a panel box to the console using Rich.

    Args:
        text: The main content to display inside the box.
        color: The color name to style the panel. Defaults to a light purple if None.
        title: Optional title text displayed at the top of the panel.
        center: Whether to center the text.
    """

    if color and not hasattr(colors, color):
        # Invalid colour used
        raise ValueError(f"Invalid color: {color}")

    color = colors.light_purple if not color else colors.__dict__[color.lower()]
    test_panel = Panel(
        text if not center else text.center(console_width - 4), style=color, title=title
    )

    console.print(test_panel)


def customPrint(
    text: str,
    color: Optional[Literal[
        'light_purple', 'medium_purple', 'dark_purple', 'pastel_purple', 'soft_purple',
        'deep_purple', 'plum', 'lilac', 'eggplant', 'black',
        'light_red', 'medium_red', 'dark_red',
        'light_green', 'medium_green', 'dark_green'
    ]] = None
):
    """
    Prints a string to the console using Rich with time and file name.

    Args:
        text: The main content to display inside the box.
        color: The color of the text to print.
    """

    if color and not hasattr(colors, color):
        # Invalid colour used
        raise ValueError(f"Invalid color: {color}")

    color = colors.light_purple if not color else colors.__dict__[color.lower()]
    current_time = datetime.now().strftime("%H:%M:%S")

    frame_info = traceback.extract_stack()[-2]
    filename = os.path.basename(frame_info.filename)
    lineno = frame_info.lineno

    content_to_print = f"[#676585]❲{current_time}❳[/#676585] {text} | [#676585]❲{filename}:{lineno}❳[/#676585]"
    console.print(
        content_to_print,
        style=color,
        markup=True
    )


if __name__ == "__main__":
    # Debug.
    customPrint("TEST", "medium_purple")
