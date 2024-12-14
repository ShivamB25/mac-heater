import numpy as np
import multiprocessing as mp
from time import sleep, time
import psutil
import os
import platform
import signal
import sys
import atexit
from subprocess import Popen, PIPE
import warnings
warnings.filterwarnings('ignore')

# Configuration
TEMP_TARGET = 75  # Target temperature (°C)
TEMP_MAX = 85    # Maximum safe temperature (°C)
TEMP_CRITICAL = 95  # Emergency shutdown temperature (°C)
MATRIX_SIZES = [200, 500, 1000, 1500]
PROCESS_DELAY = 0.2
TEMP_CHECK_INTERVAL = 1.0

class TemperatureMonitor:
    def __init__(self):
        self.setup_temp_command()
        
    def setup_temp_command(self):
        if platform.system() == 'Darwin':  # macOS
            # Using a different approach for macOS temperature monitoring
            self.temp_command = [
                "sudo", "powermetrics", "-n", "1", 
                "--show-cpu-temp", "--format", "json"
            ]
        else:
            self.temp_command = None
            
    def get_temperature(self):
        try:
            if platform.system() == 'Darwin':
                try:
                    process = Popen(self.temp_command, stdout=PIPE, stderr=PIPE)
                    output, _ = process.communicate(timeout=2)
                    if output:
                        # Parse the CPU temperature from powermetrics output
                        return float(output.decode().split('CPU die temperature:')[1].split()[0])
                except:
                    return 0
            else:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        return entries[0].current
            return 0
        except:
            return 0

class SystemMonitor:
    def __init__(self):
        self.cpu_percent = 0
        self.memory_percent = 0
        self.temperature = 0
        self.start_time = time()
        self.temp_monitor = TemperatureMonitor()
        
    def update(self):
        self.cpu_percent = psutil.cpu_percent(interval=0.1)
        self.memory_percent = psutil.virtual_memory().percent
        self.temperature = self.temp_monitor.get_temperature()
        
    def get_status(self):
        return {
            'temperature': self.temperature,
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'runtime': int(time() - self.start_time)
        }

class MatrixCalculator:
    def __init__(self, size=500):
        self.size = size
        
    def generate_matrices(self):
        return (np.random.rand(self.size, self.size),
                np.random.rand(self.size, self.size))
    
    def heavy_calculation(self, matrix_a, matrix_b):
        try:
            # Matrix multiplication
            result = np.dot(matrix_a, matrix_b)
            
            # Additional operations to increase CPU load
            for _ in range(3):
                result = np.dot(result, result)
                result = np.linalg.matrix_power(result, 2)
                result = np.exp(result / np.max(result))
                
            # Force computation
            result = np.abs(result)
            _ = np.sum(result)
            
            return result
        except:
            return None

class ProcessManager:
    def __init__(self):
        self.processes = []
        self.stop_event = mp.Event()
        self.size_queue = mp.Queue()
        
    def cleanup(self):
        print("\nCleaning up processes...", flush=True)
        self.stop_event.set()
        
        for p in self.processes:
            try:
                p.terminate()
                p.join(timeout=1.0)
                if p.is_alive():
                    os.kill(p.pid, signal.SIGKILL)
            except:
                continue
                
        self.processes.clear()
        print("Cleanup complete", flush=True)

def worker_process(process_id, size_queue, stop_event):
    try:
        # Set up signal handlers in worker
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        
        calculator = MatrixCalculator(size=500)
        
        while not stop_event.is_set():
            try:
                # Get new size if available
                try:
                    new_size = size_queue.get_nowait()
                    calculator.size = new_size
                except:
                    pass
                    
                # Generate and calculate
                matrix_a, matrix_b = calculator.generate_matrices()
                _ = calculator.heavy_calculation(matrix_a, matrix_b)
                
            except Exception as e:
                if stop_event.is_set():
                    break
                continue
                
    except (KeyboardInterrupt, SystemExit):
        return
    except Exception as e:
        print(f"Process {process_id} error: {e}", flush=True)
    finally:
        sys.stdout.flush()
        sys.stderr.flush()

class HeatingController:
    def __init__(self):
        self.monitor = SystemMonitor()
        self.process_manager = ProcessManager()
        self.running = True
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        atexit.register(self.cleanup)
        
    def signal_handler(self, signum, frame):
        print("\nReceived signal to stop...", flush=True)
        self.running = False
        
    def cleanup(self):
        if hasattr(self, 'process_manager'):
            self.process_manager.cleanup()
            
    def adjust_workload(self, status):
        temp = status['temperature']
        
        if temp < TEMP_TARGET - 10:
            return {'action': 'increase', 'size': MATRIX_SIZES[-1]}
        elif temp < TEMP_TARGET:
            return {'action': 'maintain', 'size': MATRIX_SIZES[2]}
        elif temp < TEMP_MAX:
            return {'action': 'reduce', 'size': MATRIX_SIZES[1]}
        else:
            return {'action': 'stop', 'size': MATRIX_SIZES[0]}
            
    def run(self):
        print("\033[H\033[J")  # Clear screen
        print("CPU Heater Starting...")
        print(f"Target Temperature: {TEMP_TARGET}°C")
        print(f"Maximum Temperature: {TEMP_MAX}°C")
        print("Press Ctrl+C to stop\n")
        
        try:
            while self.running:
                try:
                    self.monitor.update()
                    status = self.monitor.get_status()
                    action = self.adjust_workload(status)
                    
                    print(f"\rTemp: {status['temperature']:.1f}°C | "
                          f"CPU: {status['cpu_percent']}% | "
                          f"Memory: {status['memory_percent']}% | "
                          f"Processes: {len(self.process_manager.processes)} | "
                          f"Runtime: {status['runtime']}s | "
                          f"Action: {action['action']}", end="", flush=True)
                    
                    self.handle_action(action)
                    
                    if status['temperature'] >= TEMP_CRITICAL:
                        print("\nCritical temperature reached! Shutting down...", flush=True)
                        break
                        
                    sleep(TEMP_CHECK_INTERVAL)
                    
                except Exception as e:
                    print(f"\nError in main loop: {e}", flush=True)
                    if not self.running:
                        break
                    sleep(1)
                    
        except (KeyboardInterrupt, SystemExit):
            print("\nStopping by user request...", flush=True)
        finally:
            self.cleanup()
            final_temp = self.monitor.temp_monitor.get_temperature()
            print(f"\nFinal temperature: {final_temp:.1f}°C", flush=True)

    def handle_action(self, action):
        if not self.running:
            return
            
        if action['action'] == 'increase' and len(self.process_manager.processes) < mp.cpu_count() * 2:
            self.spawn_process(action['size'])
        elif action['action'] == 'stop':
            if len(self.process_manager.processes) > mp.cpu_count():
                self.remove_process()
                
        self.update_all_processes(action['size'])
        
    def spawn_process(self, matrix_size):
        if not self.running:
            return
            
        process = mp.Process(
            target=worker_process,
            args=(len(self.process_manager.processes),
                  self.process_manager.size_queue,
                  self.process_manager.stop_event)
        )
        process.start()
        self.process_manager.processes.append(process)
        
    def remove_process(self):
        if self.process_manager.processes:
            p = self.process_manager.processes.pop()
            try:
                p.terminate()
                p.join(timeout=1.0)
                if p.is_alive():
                    os.kill(p.pid, signal.SIGKILL)
            except:
                pass

    def update_all_processes(self, matrix_size):
        for _ in range(len(self.process_manager.processes)):
            try:
                self.process_manager.size_queue.put_nowait(matrix_size)
            except:
                pass

if __name__ == "__main__":
    try:
        controller = HeatingController()
        controller.run()
    except Exception as e:
        print(f"Fatal error: {e}", flush=True)
    finally:
        # Ensure all processes are cleaned up
        if 'controller' in locals():
            controller.cleanup()