import time
import array
from statistics import median
from typing import Annotated
from pynput.mouse import Listener
import typer

SAMPLE_RATE = 0.01
GRACE_PERIOD = 5
inputs_x = array.array('f')
inputs_y = array.array('f')

screen_width_px: int = 1920
screen_height_px: int = 1080


def on_move(x: int, y: int) -> None:
    """Records cursor movements"""
    global inputs_x, inputs_y, screen_width_px, screen_height_px
    inputs_x.append(x - (screen_width_px / 2))
    inputs_y.append(y - (screen_height_px / 2))


def record_movements(duration: int) -> None:
    """Records cursor movements for the given duration"""
    with Listener(on_move=on_move):
        time.sleep(GRACE_PERIOD)
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
        min_peak = inputs_x.bincount(near_min.astype(int)).argmax()
    else:
        min_peak = int(min_val)

    if len(near_max) > 0:
        max_peak = inputs_y.bincount(near_max.astype(int)).argmax()
    else:
        max_peak = int(max_val)

    return min_peak, max_peak


def analyze_data(
    current_area_size: float,
    playfield_size_px: int,
    inputs: array
):
    """Analyzes the movement data and finds dimensions & peak points"""

    playfield_inputs = array.array('f')

    for input in inputs:
        if input < playfield_size_px * 0.6:
            playfield_inputs.append(input)

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
    
    corrected_area: float = current_area_size * played_area / (playfield_size_px)
    
    return corrected_area


def main(
    screen_height_px: Annotated[
        int, typer.Option(prompt="Enter your screen height in pixels", min=600)
    ],
    tablet_width_mm: Annotated[
        float,
        typer.Option(prompt="Enter your full active tablet area width in mm", min=1.0),
    ],
    tablet_height_mm: Annotated[
        float,
        typer.Option(prompt="Enter your full active tablet area height in mm", min=1.0),
    ],
    duration: Annotated[
        int, typer.Option(prompt="Enter map duration in seconds", min=10)
    ],
):
    playfield_height_px = screen_height_px * 0.8
    playfield_width_px = playfield_height_px / 3 * 4
    typer.confirm("Press Enter to start recording", default=True)

    record_movements(duration)

    x_distance_mm = analyze_data(tablet_width_mm, playfield_width_px, inputs_x)

    y_distance_mm = analyze_data(tablet_height_mm, playfield_height_px, inputs_y)

    typer.echo("\n==== RESULTS ====")
    # typer.echo(
    #     "Max used area (removed soft outliers):"
    #     f" {width_mmC_filtered:.2f} x {height_mmC_filtered:.2f} mm"
    # )
    typer.echo(
        "Area calculated with most used points near extremes (removed soft outliers):"
        f" {x_distance_mm:.2f} x {y_distance_mm:.2f} mm"
    )

    again = typer.confirm("Want to record again?", default=True)
    if again:
        return main(
            screen_height_px,
            tablet_width_mm,
            tablet_height_mm,
            duration,
        )
    typer.echo("Thank you for using the Area Calculator!")
    raise typer.Exit()


if __name__ == "__main__":
    typer.run(main)
