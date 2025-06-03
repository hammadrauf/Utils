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
                      
    - python ./%prog --times 120

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
                time.sleep(0.001)
            # Count down
            for i in itertools.count(i, -1):
                if stop_event.is_set() or i <= 1:
                    return []
                time.sleep(0.001)
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

def worker_process(stop_event, threads_per_proc):
    from concurrent.futures import ThreadPoolExecutor
    import concurrent.futures
    import time
    import itertools

    myf = []
    with ThreadPoolExecutor(max_workers=threads_per_proc) as executor:
        for _ in range(threads_per_proc):
            myf.append(executor.submit(count_up_and_down, stop_event))
        for future in concurrent.futures.as_completed(myf):
            pass

def start_load_test(times=1):
    """
    Starts the load test using n-1 worker processes, each with threads.
    Main process checks for key press.
    """
    num_cores = os.cpu_count()
    num_worker_procs = max(1, num_cores - 1)
    total_threads = num_worker_procs * times

    print(f"Starting load test on {num_worker_procs} worker processes, {times} threads per process, total {total_threads} threads ...")

    from multiprocessing import Event, Process, Manager

    stop_event = Event()
    processes = []

    # Start worker processes
    for _ in range(num_worker_procs):
        p = Process(target=worker_process, args=(stop_event, times))
        p.start()
        processes.append(p)

    # Main process checks for key press
    check_if_key_pressed_proc(stop_event)

    # Wait for all worker processes to finish
    stop_event.set()
    for p in processes:
        p.join()

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
