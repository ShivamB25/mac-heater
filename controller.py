import signal
import atexit
import multiprocessing as mp
from time import sleep
from monitors.system import SystemMonitor
from process.manager import ProcessManager
from config import (
    TEMP_TARGET, TEMP_MAX, TEMP_CRITICAL,
    MATRIX_SIZES, TEMP_CHECK_INTERVAL
)

class HeatingController:
    def __init__(self):
        try:
            self.monitor = SystemMonitor()
            self.process_manager = ProcessManager()
            self.running = True
            
            # Set up signal handlers
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            atexit.register(self.cleanup)
        except Exception as e:
            print(f"Error initializing controller: {e}")
            raise
        
    def signal_handler(self, signum, frame):
        print("\nReceived signal to stop...", flush=True)
        self.running = False
        
    def cleanup(self):
        if hasattr(self, 'process_manager'):
            self.process_manager.cleanup()
            
    def adjust_workload(self, status):
        try:
            temp = status['temperature']
            
            if temp < TEMP_TARGET - 10:
                return {'action': 'increase', 'size': MATRIX_SIZES[-1]}
            elif temp < TEMP_TARGET:
                return {'action': 'maintain', 'size': MATRIX_SIZES[2]}
            elif temp < TEMP_MAX:
                return {'action': 'reduce', 'size': MATRIX_SIZES[1]}
            else:
                return {'action': 'stop', 'size': MATRIX_SIZES[0]}
        except Exception as e:
            print(f"\nError adjusting workload: {e}", flush=True)
            return {'action': 'stop', 'size': MATRIX_SIZES[0]}  # Safe default
            
    def run(self):
        try:
            print("\033[H\033[J")  # Clear screen
            print("CPU Heater Starting...")
            print(f"Target Temperature: {TEMP_TARGET}°C")
            print(f"Maximum Temperature: {TEMP_MAX}°C")
            print("Press Ctrl+C to stop\n")
            
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
        except Exception as e:
            print(f"\nUnexpected error: {e}", flush=True)
        finally:
            self.cleanup()
            final_temp = self.monitor.temp_monitor.get_temperature()
            print(f"\nFinal temperature: {final_temp:.1f}°C", flush=True)

    def handle_action(self, action):
        try:
            if not self.running:
                return
                
            if action['action'] == 'increase' and len(self.process_manager.processes) < mp.cpu_count() * 2:
                self.process_manager.spawn_process(action['size'])
            elif action['action'] == 'stop':
                if len(self.process_manager.processes) > mp.cpu_count():
                    self.process_manager.remove_process()
                    
            self.process_manager.update_all_processes(action['size'])
        except Exception as e:
            print(f"\nError handling action: {e}", flush=True)