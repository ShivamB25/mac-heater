import multiprocessing as mp
import os
import signal
from .worker import worker_process

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

    def spawn_process(self, matrix_size):
        process = mp.Process(
            target=worker_process,
            args=(len(self.processes),
                  self.size_queue,
                  self.stop_event)
        )
        process.start()
        self.processes.append(process)
        
    def remove_process(self):
        if self.processes:
            p = self.processes.pop()
            try:
                p.terminate()
                p.join(timeout=1.0)
                if p.is_alive():
                    os.kill(p.pid, signal.SIGKILL)
            except:
                pass

    def update_all_processes(self, matrix_size):
        for _ in range(len(self.processes)):
            try:
                self.size_queue.put_nowait(matrix_size)
            except:
                pass