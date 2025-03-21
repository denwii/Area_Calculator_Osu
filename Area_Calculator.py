import time
import array
import tkinter
from statistics import median
from typing import Annotated
from pynput.mouse import Listener
import typer

SAMPLE_RATE = 0.01
GRACE_PERIOD = 5
inputs_x = array.array('f')
inputs_y = array.array('f')


def on_move(x: int, y: int) -> None:
    """Records cursor movements"""
    global inputs_x, inputs_y, screen_width_px, screen_height_px
    inputs_x.append(x)
    inputs_y.append(y)


def record_movements(duration: int) -> None:
    """Records cursor movements for the given duration"""
    with Listener(on_move=on_move):
        time.sleep(GRACE_PERIOD)
        print(f"Recording started for {duration} seconds...")
        # Sampling every 10ms
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < duration:
            time.sleep(SAMPLE_RATE)


def analyze_data(
    current_area_size: float,
    playfield_size_px: int,
    screen_size_px: int,
    inputs: array
):
    """Analyzes the movement data and finds dimensions & peak points"""

    playfield_inputs = array.array('f')

    for input in inputs:
        # 120% of the half playfield size -> 1.2 * 0.5 = 0.6
        if input - (screen_size_px / 2) < playfield_size_px * 0.6:
            playfield_inputs.append(input - (screen_size_px / 2))

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


def main(
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
    screen_width_px: int = tkinter.Tk().winfo_screenwidth()
    screen_height_px: int = tkinter.Tk().winfo_screenheight()

    print(screen_width_px, screen_height_px)
    
    playfield_height_px = screen_height_px * 0.8
    playfield_width_px = playfield_height_px / 3 * 4
    typer.confirm("Press Enter to start recording", default=True)

    record_movements(duration)

    x_distance_mm = analyze_data(tablet_width_mm, playfield_width_px, screen_width_px, inputs_x)

    y_distance_mm = analyze_data(tablet_height_mm, playfield_height_px, screen_height_px, inputs_y)

    typer.echo("\n==== RESULTS ====")
    typer.echo(
        "Area calculated with most used points near extremes (removed soft outliers):"
        f" {x_distance_mm:.2f} x {y_distance_mm:.2f} mm"
    )

    again = typer.confirm("Want to record again?", default=True)
    if again:
        return main(
            tablet_width_mm,
            tablet_height_mm,
            duration,
        )
    typer.echo("Thank you for using the Area Calculator!")
    raise typer.Exit()


if __name__ == "__main__":
    typer.run(main)
