import platform
from subprocess import Popen, PIPE
import psutil

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