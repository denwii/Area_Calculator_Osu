import time
from typing import Annotated
import numpy as np
from pynput.mouse import Listener
import typer
from rich.progress import track
from rich import print as rprint

SAMPLE_RATE = 0.01
GRACE_PERIOD = 5


def record_movements(
    duration: int,
) -> tuple[np.ndarray[np.uint16], np.ndarray[np.uint16]]:
    """Records cursor movements for the given duration"""
    for _ in track(
        range(GRACE_PERIOD * 100),
        description=f"Waiting for {GRACE_PERIOD} seconds before recording...",
    ):
        time.sleep(0.01)

    x_input = np.array([], dtype=np.uint16)
    y_input = np.array([], dtype=np.uint16)

    def on_move(x: int, y: int) -> None:
        """Records cursor movements"""
        nonlocal x_input, y_input
        x_input = np.append(x_input, x)
        y_input = np.append(y_input, y)

    with Listener(on_move=on_move):
        print(f"Recording started for {duration} seconds...")
        # Sampling every 10ms
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < duration:
            time.sleep(SAMPLE_RATE)

    return x_input, y_input


def find_peak_near_extremes(
    values: np.ndarray[np.uint16],
    min_val: np.uint16,
    max_val: np.uint16,
    threshold_percentage: int = 5,
) -> tuple[int, int]:
    """Finds the most used point near the detected min/max values"""
    threshold_range = (max_val - min_val) * (threshold_percentage / 100)
    near_min = values[values <= min_val + threshold_range]
    near_max = values[values >= max_val - threshold_range]

    # Remove negative values
    near_min = near_min[near_min >= 0]
    near_max = near_max[near_max >= 0]

    if len(near_min) > 0:
        min_peak = np.bincount(near_min.astype(int)).argmax()
    else:
        min_peak = int(min_val)

    if len(near_max) > 0:
        max_peak = np.bincount(near_max.astype(int)).argmax()
    else:
        max_peak = int(max_val)

    return min_peak, max_peak


def analyze_data(
    x_input: np.ndarray[np.uint16],
    y_input: np.ndarray[np.uint16],
    tablet_width_mm: int,
    tablet_height_mm: int,
    innergameplay_width_px: int,
    innergameplay_height_px: int,
):
    """Analyzes the movement data and finds dimensions & peak points"""
    # Get's the values in +- 3 standard deviations from the mean
    x_mean = np.mean(x_input)
    x_std_deviation = np.std(x_input)
    y_mean = np.mean(y_input)
    y_std_deviation = np.std(y_input)

    x_filtered = x_input[
        (x_input > x_mean - 3 * x_std_deviation)
        & (x_input < x_mean + 3 * x_std_deviation)
    ]
    y_filtered = y_input[
        (y_input > y_mean - 3 * y_std_deviation)
        & (y_input < y_mean + 3 * y_std_deviation)
    ]
    x_max = np.max(x_filtered)
    x_min = np.min(x_filtered)

    y_max = np.max(y_filtered)
    y_min = np.min(y_filtered)

    # Find peak usage near the filtered extremes
    x_min_peak, x_max_peak = find_peak_near_extremes(
        values=x_filtered, min_val=x_min, max_val=x_max
    )
    y_min_peak, y_max_peak = find_peak_near_extremes(
        values=y_filtered, min_val=y_min, max_val=y_max
    )

    x_distance_px = x_max_peak - x_min_peak
    y_distance_px = y_max_peak - y_min_peak
    x_distance_mm = (x_distance_px * tablet_width_mm) / innergameplay_width_px
    y_distance_mm = (y_distance_px * tablet_height_mm) / innergameplay_height_px

    rprint("\n==== RESULTS ====")
    rprint(
        "Area calculated with most used points near extremes (removed soft outliers):"
        f" [green]{x_distance_mm:.2f} x {y_distance_mm:.2f} mm [/green]"
    )
    rprint("===================")


def main(
    screen_width_px: Annotated[
        int, typer.Option(prompt="Enter your screen width in pixels", min=800)
    ],
    screen_height_px: Annotated[
        int, typer.Option(prompt="Enter your screen height in pixels", min=600)
    ],
    tablet_width_mm: Annotated[
        float,
        typer.Option(prompt="Enter your full active tablet area width in mm", min=1),
    ],
    tablet_height_mm: Annotated[
        float,
        typer.Option(prompt="Enter your full active tablet area height in mm", min=1),
    ],
    duration: Annotated[
        int, typer.Option(prompt="Enter map duration in seconds", min=10)
    ],
):
    innergameplay_height_px = int((864 / 1080) * screen_height_px)
    innergameplay_width_px = int((1152 / 1920) * screen_width_px)
    typer.confirm(
        "Press Enter to start recording",
        default=True,
        show_default=False,
        prompt_suffix=" ",
    )

    x_input, y_input = record_movements(duration)
    analyze_data(
        x_input=x_input,
        y_input=y_input,
        tablet_width_mm=tablet_width_mm,
        tablet_height_mm=tablet_height_mm,
        innergameplay_width_px=innergameplay_width_px,
        innergameplay_height_px=innergameplay_height_px,
    )

    again = typer.confirm("Want to record again?", default=True, prompt_suffix=" ")
    if again:
        return main(
            screen_width_px,
            screen_height_px,
            tablet_width_mm,
            tablet_height_mm,
            duration,
        )
    rprint("===================")
    rprint("Thank you for using the Area Calculator!")
    rprint(
        "If you find any issues, feel free to report it on"
        " [link=https://github.com/denwii/Area_Calculator_Osu]GitHub[/link]!"
    )
    raise typer.Exit()


if __name__ == "__main__":
    typer.run(main)