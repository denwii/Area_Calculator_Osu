import time
import array
import pyautogui
from statistics import median

SAMPLE_RATE = 0.01
GRACE_PERIOD = 5.0

def calculate_size(current_area_size: float, normalized_playfield_size: float, inputs: array) -> float:

    playfield_inputs = array.array('f')

    # Remove everything outside the playfield
    for input in inputs:
        if input < normalized_playfield_size * 1.03125:
            playfield_inputs.append(input)

    max_input = max(playfield_inputs)
    min_input = min(playfield_inputs)

    inputs9 = array.array('f')
    inputs1 = array.array('f')

    for input in playfield_inputs:
        if input > max_input * 0.9:
            inputs9.append(input)

        if input > min_input / 0.9:
            inputs1.append(input)

    del max_input, min_input, playfield_inputs

    median_9: float = median(inputs9)
    median_1: float = median(inputs1)

    played_area = median_9.__abs__() + median_1.__abs__()

    if played_area - (normalized_playfield_size * 2) < 0.1 and played_area - (normalized_playfield_size * 2) > -0.1:
        return current_area_size
    
    corrected_area: float = current_area_size * played_area / (normalized_playfield_size * 2)
    
    return corrected_area


def main():
    is_running = True

    normalized_inputs_x = array.array('f')
    normalized_inputs_y = array.array('f')

    screen_size_x, screen_size_y = pyautogui.size()

    playfield_size_y = screen_size_y * 0.8
    playfield_size_x = playfield_size_y / 3 * 4

    print("\nRemember to remove all the filters\n")
    time.sleep(GRACE_PERIOD)

    tablet_size_x = float(input("Enter the width of the tablet in mm (. for decimals): "))

    time.sleep(GRACE_PERIOD / 5)

    tablet_size_y = float(input("Enter the height of the tablet in mm (. for decimals): "))

    time.sleep(GRACE_PERIOD / 5)

    while(is_running):
        duration = int(input("Enter the duration: "))

        input("Press Enter Key to start recording\n")

        #Starting to store the cursor Position
        if duration is not None:
            time.sleep(GRACE_PERIOD)
            start_time = time.perf_counter()
            last_time = start_time
            print("Recording...")
            while time.perf_counter() - last_time < SAMPLE_RATE and time.perf_counter() - start_time <= duration:
                #Limit the sample rate to 10ms
                if time.perf_counter() - last_time < SAMPLE_RATE:
                    time.sleep(SAMPLE_RATE - (time.perf_counter() - last_time))
                normalized_inputs_x.append(pyautogui.position().x - screen_size_x / 2)
                normalized_inputs_y.append(pyautogui.position().y - screen_size_y / 2)
                last_time = time.perf_counter()

        print("Finished, calculating the area...")
        
        corrected_tablet_size_x = calculate_size(tablet_size_x, playfield_size_x / 2, normalized_inputs_x) * 2
        corrected_tablet_size_y = calculate_size(tablet_size_y, playfield_size_y / 2, normalized_inputs_y) * 2

        print("The area of the tablet is:\nWidth: " + str(corrected_tablet_size_x) + " mm\n" + "Height: " + str(corrected_tablet_size_y) + " mm\n")

        time.sleep(GRACE_PERIOD)

        user_input = input("Press Y to set this area to current or any key to ignore\n")
        if(user_input == 'Y' or user_input == 'y'):
            tablet_size_x = corrected_tablet_size_x
            tablet_size_y = corrected_tablet_size_y

        time.sleep(GRACE_PERIOD / 5)

        user_input = input("Press Enter to recalculate again or type Q to exit\n")
        if(user_input == 'Q' or user_input == 'q'):
            is_running = False

    print("Thank you for using the Area Calculator!\n")
    time.sleep(GRACE_PERIOD)

if __name__ == "__main__":
    main()