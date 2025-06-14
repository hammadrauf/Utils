import os
import sys
import time
import itertools
import random
import multiprocessing
from multiprocessing import Process, Event, Manager
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from collections import defaultdict, deque

# Worker thread function
def count_up_and_down(proc_idx, thread_idx, stop_event, shared_state):
    global anim_speed, ptimes
    try:
        max_count = 100
        # Each thread starts at a random value within the range
        i = random.randint(1, max_count)
        # Each process bar (thread) randomly starts going up or down
        direction = random.choice([1, -1])
        while not stop_event.is_set():
            shared_state[(proc_idx, thread_idx)] = (i, direction)
            # Randomly decide to change direction at the ends or randomly
            if direction == 1:
                i += 1
                if i > max_count or random.random() < 0.01:
                    direction = -1
            else:
                i -= 1
                if i <= 1 or random.random() < 0.01:
                    direction = 1
            if anim_speed > 0.0:
                time.sleep(anim_speed)
    except Exception as e:
        print(f"Thread error: {e}")

# Worker process function
def worker_process(proc_idx, threads_per_proc, stop_event, shared_state):
    global anim_speed, ptimes
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=threads_per_proc) as executor:
        for thread_idx in range(threads_per_proc):
            executor.submit(count_up_and_down, proc_idx, thread_idx, stop_event, shared_state)
        while not stop_event.is_set():
            time.sleep(0.1)

# Kivy Widget for the bar graph
class LoadBarGraph(Widget):
    def __init__(self, num_procs, threads_per_proc, shared_state, **kwargs):
        global anim_speed, ptimes
        super().__init__(**kwargs)
        self.num_procs = num_procs
        self.threads_per_proc = threads_per_proc
        self.shared_state = shared_state
        # Assign a random color (not black) to each thread at startup
        self.thread_colors = {}
        for proc_idx in range(self.num_procs):
            for thread_idx in range(self.threads_per_proc):
                while True:
                    color = (random.random(), random.random(), random.random(), 1)
                    # Avoid black or too dark colors
                    if sum(color[:3]) > 0.5:
                        break
                self.thread_colors[(proc_idx, thread_idx)] = color
        # Smaller dots, more trail points
        self.trails = defaultdict(lambda: deque(maxlen=60))  # More points for smoother trail
        Clock.schedule_interval(self.update_graph, 0.05)

    def update_graph(self, dt):
        global anim_speed, ptimes
        self.canvas.clear()
        width = self.width
        height = self.height
        gap = 10  # Gap in pixels between process bars
        total_gap = gap * (self.num_procs + 1)
        bar_width = (width - total_gap) / self.num_procs
        max_count = 100  # Should match the max in count_up_and_down
        trail_length = int(height * 0.0175)  # Half of previous 3.5%

        for proc_idx in range(self.num_procs):
            x = gap + proc_idx * (bar_width + gap)
            for thread_idx in range(self.threads_per_proc):
                key = (proc_idx, thread_idx)
                count, direction = self.shared_state.get(key, (1, 1))
                y = (count / max_count) * height
                # Update trail
                self.trails[key].appendleft(y)
                # Draw trail (fading out)
                for i, trail_y in enumerate(self.trails[key]):
                    if i > trail_length:
                        break
                    alpha = max(0, 1 - i / trail_length)
                    # Trail color: cyan when going up, orange when going down
                    if direction == 1:
                        trail_color = (0.2, 0.7, 1, alpha)  # Cyan-ish
                    else:
                        trail_color = (1, 0.5, 0, alpha)    # Orange
                    with self.canvas:
                        Color(*trail_color)
                        Rectangle(
                            pos=(x + thread_idx * (bar_width / self.threads_per_proc) + (bar_width / self.threads_per_proc) / 2 - 0.75,
                                 trail_y - 0.75),
                            size=(1.5, 1.5)  # Very small dot size, dots are very close
                        )
                # Draw the moving ball (main count box) with its assigned color
                color = self.thread_colors.get(key, (0, 1, 0, 1))
                with self.canvas:
                    Color(*color)
                    Rectangle(
                        pos=(x + thread_idx * (bar_width / self.threads_per_proc) + (bar_width / self.threads_per_proc) / 2 - 3,
                             y - 3),
                        size=(6, 6)  # Smaller ball size
                    )

# --- Parse command line arguments using sys.argv ---
""" try:
    custom_args = [arg for arg in sys.argv]
    print(f"Custom args: {custom_args}")
    if "--" in custom_args:
        idx = custom_args.index("--")
        print("Arguments after '--':", custom_args[idx+1:])
        ptimes = 1 if len(custom_args) < idx + 2 else int(custom_args[idx + 1])
        anim_speed = 0.0 if len(custom_args) < idx + 3 else float(custom_args[idx + 2])
    else:
        print("No '--' found, using default values.")
        ptimes = 1
        anim_speed = 0.0
except (ValueError, IndexError) as e:
    print(f"Error parsing command line arguments: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1) """

def to_int(value):
    try:
        return int(value)
    except Exception:
        return None

def to_float(value):
    try:
        return float(value)
    except Exception:
        return None

ptimes = 1
anim_speed = 0.0

try:
    custom_args = [arg for arg in sys.argv if not arg.startswith("--")]
    print(f"Custom args: {custom_args}")
    ptimes = 1 if (len(custom_args) < 2 or to_int(custom_args[1])==None ) else int(custom_args[1])
    anim_speed = 0.0 if (len(custom_args) < 3 or to_float(custom_args[2])==None ) else float(custom_args[2])
    if len(custom_args) > 3 and len(custom_args) < 6:
        ptimes = 1 if (len(custom_args) > 3 or to_int(custom_args[3])==None ) else int(custom_args[3])
        anim_speed = 0.0 if (len(custom_args) > 3 or to_float(custom_args[4])==None ) else float(custom_args[4])

except (ValueError, IndexError):
    print("Could not convert option value to an integer.")
    exit(1)
except Exception as e:
    print(f"Error: {e}")
    exit(1)

class LoadTestApp(App):
    def build(self):
        global ptimes, anim_speed
        num_cores = os.cpu_count()
        num_worker_procs = max(1, num_cores - 1)
        threads_per_proc = ptimes  # Use the parsed argument

        manager = Manager()
        shared_state = manager.dict()
        stop_event = Event()
        self.processes = []

        # Start worker processes
        for proc_idx in range(num_worker_procs):
            p = Process(target=worker_process, args=(proc_idx, threads_per_proc, stop_event, shared_state))
            p.start()
            self.processes.append(p)

        # GUI layout
        root = BoxLayout(orientation='vertical')
        self.graph = LoadBarGraph(num_worker_procs, threads_per_proc, shared_state, size_hint=(1, 0.95))
        root.add_widget(self.graph)
        # Add buttons or controls as needed

        # Stop everything on close
        self.stop_event = stop_event
        return root

    def on_stop(self):
        self.stop_event.set()
        for p in self.processes:
            p.join()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    LoadTestApp().run()