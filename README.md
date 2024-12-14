# Mac CPU Heater

A Python utility to heat up your Mac's CPU through intensive matrix calculations while monitoring temperature.

## Features

- Dynamically adjusts workload based on CPU temperature
- Real-time monitoring of CPU temperature, usage, and memory
- Automatic process scaling based on system conditions
- Safe temperature limits and emergency shutdown
- Multi-process matrix calculations

## Requirements

- Python 3.8+
- macOS (temperature monitoring is optimized for Mac)
- `uv` package manager

## Setup

Clone the repository:
```bash
git clone https://github.com/ShivamB25/mac-heater.git
cd mac-heater
```

## Usage

Run the heater:
```bash
uv run main.py
```

The program will:
- Start monitoring your CPU temperature
- Create worker processes for matrix calculations
- Adjust workload based on temperature readings
- Display real-time stats in the terminal

### Temperature Thresholds

- Target: 75°C
- Maximum: 85°C
- Critical: 95°C (emergency shutdown)

### Controls

- Press `Ctrl+C` to stop the program
- The program will automatically clean up processes on exit

## Project Structure

```
mac-heater/
├── calculations/           # Matrix calculation modules
│   ├── __init__.py
│   └── matrix.py
├── monitors/              # System monitoring modules
│   ├── __init__.py
│   ├── system.py
│   └── temperature.py
├── process/               # Process management modules
│   ├── __init__.py
│   ├── manager.py
│   └── worker.py
├── config.py             # Configuration settings
├── controller.py         # Main heating controller
└── main.py              # Entry point
```

## Safety Notes

- The program includes safety measures to prevent overheating
- Monitors CPU temperature and automatically reduces load if needed
- Emergency shutdown at critical temperatures
- Always ensure proper ventilation when running CPU-intensive tasks

## License

See the [LICENSE](LICENSE) file for details.