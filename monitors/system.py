import psutil
from time import time
from .temperature import TemperatureMonitor

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