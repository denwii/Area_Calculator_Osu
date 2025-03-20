import time
from typing import Annotated, NoReturn
import numpy as np
from pynput.mouse import Listener
import typer

SAMPLE_RATE = 0.01
GRACE_PERIOD = 5
input_x = np.array([], dtype=np.uint16)
input_y = np.array([], dtype=np.uint16)


def on_move(x: int, y: int) -> NoReturn:
    """Records cursor movements"""
    global input_x, input_y
    input_x = np.append(input_x, x)
    input_y = np.append(input_y, y)


def record_movements(duration: int) -> NoReturn:
    """Records cursor movements for the given duration"""
    with Listener(on_move=on_move):
        time.sleep(GRACE_PERIOD)
        print(f"Recording started for {duration} seconds...")
        # Sampling every 10ms
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < SAMPLE_RATE:
            time.sleep(time.perf_counter() - start_time)


def find_peak_near_extremes(values, min_val, max_val, threshold_percentage=5):
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
    tablet_width_mm: int,
    tablet_height_mm: int,
    innergameplay_width_px: int,
    innergameplay_height_px: int,
):
    """Analyzes the movement data and finds dimensions & peak points"""

    # Remove soft outliers (0.01 - 99.99 percentiles)
    x_1, x_9 = np.percentile(input_x, [0.01, 99.99])
    y_1, y_9 = np.percentile(input_y, [0.01, 99.99])

    width_px_filtered = x_9 - x_1
    height_px_filtered = y_9 - y_1

    # Convert to mm
    width_mmC_filtered = (width_px_filtered * tablet_width_mm) / innergameplay_width_px
    height_mmC_filtered = (height_px_filtered * tablet_height_mm) / innergameplay_height_px

    # Find peak usage near the filtered extremes
    x_min_peak, x_max_peak = find_peak_near_extremes(input_x, x_1, x_9)
    y_min_peak, y_max_peak = find_peak_near_extremes(input_y, y_1, y_9)

    x_distance_px = x_max_peak - x_min_peak
    y_distance_px = y_max_peak - y_min_peak
    x_distance_mm = (x_distance_px * tablet_width_mm) / innergameplay_width_px
    y_distance_mm = (y_distance_px * tablet_height_mm) / innergameplay_height_px

    typer.echo("\n==== RESULTS ====")
    # typer.echo(
    #     "Max used area (removed soft outliers):"
    #     f" {width_mmC_filtered:.2f} x {height_mmC_filtered:.2f} mm"
    # )
    typer.echo(
        "Area calculated with most used points near extremes (removed soft outliers):"
        f" {x_distance_mm:.2f} x {y_distance_mm:.2f} mm"
    )


def main(
    screen_width_px: Annotated[
        int, typer.Option(prompt="Enter your screen width in pixels", min=800)
    ],
    screen_height_px: Annotated[
        int, typer.Option(prompt="Enter your screen height in pixels", min=600)
    ],
    tablet_width_mm: Annotated[
        int,
        typer.Option(prompt="Enter your full active tablet area width in mm", min=1),
    ],
    tablet_height_mm: Annotated[
        int,
        typer.Option(prompt="Enter your full active tablet area height in mm", min=1),
    ],
    duration: Annotated[
        int, typer.Option(prompt="Enter map duration in seconds", min=10)
    ],
):
    innergameplay_height_px = int((864 / 1080) * screen_height_px)
    innergameplay_width_px = int((1152 / 1920) * screen_width_px)
    typer.confirm("Press Enter to start recording", default=True)

    record_movements(duration)
    analyze_data(
        tablet_width_mm=tablet_width_mm,
        tablet_height_mm=tablet_height_mm,
        innergameplay_width_px=innergameplay_width_px,
        innergameplay_height_px=innergameplay_height_px,
    )

    again = typer.confirm("Want to record again?", default=True)
    if again:
        return main(
            screen_width_px,
            screen_height_px,
            tablet_width_mm,
            tablet_height_mm,
            duration,
        )
    typer.echo("Thank you for using the Area Calculator!")
    raise typer.Exit()


if __name__ == "__main__":
    typer.run(main)
