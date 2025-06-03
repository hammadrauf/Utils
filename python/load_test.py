import threading
import itertools
import os
from concurrent.futures import ThreadPoolExecutor
import concurrent. futures
import keyboard
import time
from optparse import OptionParser
from multiprocessing import Process, Event


parser = OptionParser(usage=f"""usage: %prog [--times INT] [--help] [--version]

Description
    This script tries to create artificail load on the CPU by counting up and down to the maximum integer.
    The script uses all available CPU cores to create multiple threads to count up and down. The Jobs are multi
    threaded and run in parallel. The script will run until the "Space" key is pressed. The script will then stop
    
    There are frequent checks for the "Space" key press. All the threads also frequently give up control to the
    main thread to check if the "Space" key has been pressed. This is done to ensure that the script can be stopped
    at any time.

    The script will create a specified number of threads for all the cores. The default is 1 times per core.
    The times parameter can be used to specify the number of times to run the load test. After some empirical testing on
    a 4-core machine, it was found that the a times value of 300 is enough to put the CPU on 100% usage.

Default Values:
    - INT: 1

Examples
    - ./%prog

    - ./%prog -t 20
                      
    - python ./%prog -- times 120

Requirements
    - python 3.6 or greater
    - pip install keyboard
""", version="%prog 1.0")
                      
parser.add_option('-t','--times', dest='ptimes', metavar = "NUMBER", type='int', help='Number of times to run the load test', default=1)

try:
    (options, args) = parser.parse_args ()
    ptimes = options.ptimes
except ValueError:
    print("Could not convert option value to an integer.")
except Exception as e:
    print(f"Error: {e}")
    os.exit(0)

# Global flag to signal threads to stop
#stop_flag = False


def count_up_and_down(stop_event=None):
    """
    Function to count up to the maximum integer and then count down.
    Checks the stop flag at every step to exit gracefully.
    """
    try:
        while not stop_event.is_set():
            # Count up
            for i in itertools.count(1) :
                if stop_event.is_set():
                    return []
                time.sleep(0.05)
            # Count down
            for i in itertools.count(i, -1):
                if stop_event.is_set() or i <= 1:
                    return []
                time.sleep(0.05)
    except Exception as e:
        print(f"Thread encountered an error: {e}")
    finally:
        return []


def check_if_key_pressed_proc(stop_event=None):
    print("Awaiting key press ... (Space bar to stop)")
    while not stop_event.is_set():
        if keyboard.is_pressed(' '):
            stop_event.set()
            break
        time.sleep(0.001)
    print("Key pressed")
    return []


def start_load_test (times=1):
    """
    Starts the load test using all available CPU cores!
    """
    num_cores = os.cpu_count()
    total_processes = num_cores*times
    print(f"Starting load test on {num_cores} cores, {times} times, ie {total_processes} threads ... ")
    
    from multiprocessing import Event
    stop_event = Event()

    # Start the key press checker in a separate process
    key_proc = Process(target=check_if_key_pressed_proc, args=(stop_event,))
    key_proc.start()    

    myf = []
    with ThreadPoolExecutor(max_workers=total_processes) as executor:
        for _ in range(total_processes):
            myf.append(executor.submit(count_up_and_down, stop_event))

        print("Running load test.")

        # Wait for the key process to finish (i.e., space pressed)
        key_proc.join()

        # Wait for all threads to finish
        print("Waiting for threads to finish..")
        stop_event.set()  # Signal all threads to stop
        for future in concurrent.futures.as_completed(myf):
            pass
            #future.result ()

    print("Load test stopped.")


def main() :
    """
    Main function to start the load test.
    """
    try:
        start_load_test(times=ptimes)
    except KeyboardInterrupt:
        print("Interrupted by user. Exiting ... ")


if __name__ == "__main__":
    main()
