import time
import array
import pyautogui
from statistics import median

SAMPLE_RATE = 0.01
GRACE_PERIOD = 5.0

def analyze_data(current_area_size: float, normalized_playfield_size: int, inputs: array):
    # Remove everything outside the playfield
    inputs = inputs[inputs[:, 0] < normalized_playfield_size * 1.03125]

    inputs9 = inputs[inputs[:, 0] > max(inputs) * 0.9]
    inputs1 = inputs[inputs[:, 0] < min(inputs) / 0.9]

    median_9: float = median(inputs9)
    median_1: float = median(inputs1)

    played_area = median_9.__abs__() + median_1.__abs__()

    if played_area - normalized_playfield_size * 2 < 0.1 and played_area - normalized_playfield_size * 2 > -0.1:
        return current_area_size
    
    return current_area_size * played_area / (normalized_playfield_size * 2)


def main():
    is_running = True

    normalized_inputs_x = array.array('i')
    normalized_inputs_y = array.array('i')

    playfield_size_y = pyautogui.size().y * 0.8
    playfield_size_x = playfield_size_y / 3 * 4

    print("Remember to set remove all the filters\n")
    time.sleep(GRACE_PERIOD)

    print("Enter the width of the tablet in mm (. for decimals): ")
    tablet_size_x = int(input())
    print('\n')

    time.sleep(GRACE_PERIOD / 5)

    print("Enter the height of the tablet in mm (. for decimals): ")
    tablet_size_y = int(input())
    print('\n')

    time.sleep(GRACE_PERIOD / 5)

    while(is_running):
        print('Enter the duration: ')
        duration = int(input())
        print('\n')

        input("Press Any Key to start recording\n")

        #Starting to store the cursor Position
        if duration is not None:
            time.sleep(GRACE_PERIOD)

            start_time = time.perf_counter()
            last_time = start_time
            while time.perf_counter() - last_time < SAMPLE_RATE and time.perf_counter() - start_time <= duration:
                #Limit the sample rate to 10ms
                if time.perf_counter() - last_time < SAMPLE_RATE:
                    time.sleep(SAMPLE_RATE - time.perf_counter() - last_time)
                normalized_inputs_x.append(pyautogui.position().x - pyautogui.size().x / 2)
                normalized_inputs_y.append(pyautogui.position().y - pyautogui.size().y / 2)
                last_time = time.perf_counter()

        corrected_tablet_size_x = analyze_data(tablet_size_x, playfield_size_x / 2, normalized_inputs_x)
        corrected_tablet_size_y = analyze_data(tablet_size_y, playfield_size_y / 2, normalized_inputs_y)

        print("The area of the tablet is:\nWidth: " + str(corrected_tablet_size_x) + " mm\n" + "Height: " + str(corrected_tablet_size_y) + " mm\n")

        time.sleep(GRACE_PERIOD)

        print("Press Y to set this area to current or any key to ignore\n")

        user_input = input("")
        if(user_input == 'Y' or user_input == 'y'):
            tablet_size_x = corrected_tablet_size_x
            tablet_size_y = corrected_tablet_size_y

        time.sleep(GRACE_PERIOD / 5)

        print("Press Enter to recalculate again or type Q to exit\n")

        user_input = input("")
        if(user_input == 'Q' or user_input == 'q'):
            is_running = False

        time.sleep(GRACE_PERIOD)

    print("Thank you for using the Area Calculator!\n")
    time.sleep(GRACE_PERIOD)

    return 0