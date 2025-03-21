import time
import array
from typing import Annotated
from statistics import median
import numpy as np
from pynput.mouse import Listener
import typer
from rich.progress import track
from rich import print as rprint

SAMPLE_RATE = 0.01
GRACE_PERIOD = 5

input_x = np.array([], dtype=np.uint16)
input_y = np.array([], dtype=np.uint16)


def on_move(x: int, y: int) -> None:
    """Records cursor movements"""
    global input_x, input_y
    input_x = np.append(input_x, x)
    input_y = np.append(input_y, y)


def record_movements(duration: int) -> None:
    """Records cursor movements for the given duration"""
    for _ in track(
        range(GRACE_PERIOD * 100),
        description=f"Waiting for {GRACE_PERIOD} seconds before recording...",
    ):
        time.sleep(0.01)

    with Listener(on_move=on_move):
        print(f"Recording started for {duration} seconds...")
        # Sampling every 10ms
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < duration:
            time.sleep(SAMPLE_RATE)


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


def dark98_analyze_data(current_area_size: float, playfield_size_px: int, screen_size_px: int, inputs: array):
    """Analyzes the movement data and finds dimensions & peak points"""

    playfield_inputs = array.array('f')

    for input in inputs:
        # 120% of the half playfield size -> 1.2 * 0.5 = 0.6
        # if input - (screen_size_px / 2) < playfield_size_px * 0.6:
        playfield_inputs.append(input - (screen_size_px / 2))
        # else:
        #   playfield_inputs.append(playfield_size_px * 0.6)

    max_input = max(playfield_inputs)
    min_input = min(playfield_inputs)

    inputs9 = array.array('f')
    inputs1 = array.array('f')
    
    for input in playfield_inputs:
        if input > max_input * 0.9:
            inputs9.append(input)

        if input < min_input * 0.9:
            inputs1.append(input * -1)

    median_9: float = median(inputs9)
    median_1: float = median(inputs1)

    played_area = median_9 + median_1

    if played_area - (playfield_size_px) < 0.1 and played_area - (playfield_size_px) > -0.1:
        return current_area_size
    
    corrected_area: float = current_area_size * (played_area / playfield_size_px)
    
    return corrected_area

def legacy_analyze_data(
    tablet_width_mm: float,
    tablet_height_mm: float,
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
    rprint("===================")


def main(
    screen_width_px: Annotated[
        int, typer.Option(prompt="Enter your screen width in pixels", min=600)
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
    typer.confirm("Press Enter to start recording", default=True)

    record_movements(duration)
    legacy_analyze_data(
        tablet_width_mm=tablet_width_mm,
        tablet_height_mm=tablet_height_mm,
        innergameplay_width_px=innergameplay_width_px,
        innergameplay_height_px=innergameplay_height_px,
    )

    x_distance_mm: float = dark98_analyze_data(tablet_width_mm, innergameplay_width_px, screen_width_px, np.array(input_x.tolist()))
    y_distance_mm: float = dark98_analyze_data(tablet_height_mm, innergameplay_height_px, screen_height_px, np.array(input_y.tolist()))
    typer.echo(
        "Dark98 Calculation:\nArea calculated:"
        f" {x_distance_mm:.2f} x {y_distance_mm:.2f} mm\n"
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
