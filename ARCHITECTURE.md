# Mac CPU Heater - Architecture Overview

## System Architecture

### Core Components Interaction
```
                                    ┌─────────────────┐
                                    │    Main Entry   │
                                    │    (main.py)    │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │   Controller    │
                                    │(controller.py)  │
                                    └────────┬────────┘
                                             │
                    ┌──────────────┬─────────┴───────┬──────────────┐
            ┌───────▼───────┐┌─────▼─────┐┌──────────▼─────┐┌───────▼───────┐
            │Temperature    ││  Process   ││   Matrix       ││  System       │
            │Monitoring    ││Management  ││ Calculations   ││  Monitoring   │
            └───────┬───────┘└─────┬─────┘└──────────┬─────┘└───────┬───────┘
                    │              │               │              │
                    └──────────────┴───────┬───────┴──────────────┘
                                          │
                                   ┌──────▼──────┐
                                   │   Kernel    │
                                   └─────────────┘
```

## System Calls and Kernel Interactions

### Process Management
- `fork()`: Used by multiprocessing to create worker processes
- `execve()`: Underlying call when launching powermetrics
- `kill()`: Used for process termination (SIGTERM, SIGKILL)
- `wait4()`: Used by multiprocessing for process status monitoring

### Memory Operations
- `mmap()`: Used by NumPy for matrix operations
  - Anonymous mappings for matrix data
  - Shared memory for inter-process communication
- `munmap()`: Cleanup of matrix memory
- `brk()/sbrk()`: Dynamic memory allocation for process heap

### Temperature Monitoring
- `ioctl()`: System calls for hardware interaction
- `open()`: Opening device files and pipes
- `read()`: Reading temperature data
- `close()`: Closing file descriptors

### IPC (Inter-Process Communication)
- Multiprocessing Queue: Uses Unix domain sockets internally
- Event synchronization: Uses futex system calls
- Shared memory: Uses mmap with MAP_SHARED flag

## Memory Layout

### Process Memory Structure
```
┌─────────────────┐ High Addresses
│    Stack        │ - Local variables
│        ▼        │ - Function calls
│                 │
│        ▲        │
│    Shared       │ - Mapped files
│    Libraries    │ - Shared memory
│                 │
│    Memory       │ - Anonymous mappings
│    Mapped       │ - Matrix data
│    Region       │
│                 │
│        ▲        │
│    Heap         │ - Dynamic allocations
│                 │
│    BSS          │ - Uninitialized data
│    Data         │ - Initialized data
│    Text         │ - Program code
└─────────────────┘ Low Addresses
```

### Matrix Memory Management
- Large matrices are allocated using mmap
- Memory is page-aligned for optimal performance
- Uses huge pages when available for better TLB efficiency

## Temperature Monitoring Implementation

### macOS Specific
```
┌─────────────────┐
│  powermetrics   │ ─── privileged helper
│     daemon      │     (requires sudo)
└────────┬────────┘
         │
         │ SMC interface
┌────────▼────────┐
│  System         │
│  Management     │ ─── kernel extension
│  Controller     │
└────────┬────────┘
         │
         │ hardware access
┌────────▼────────┐
│    CPU Die      │
│  Temperature    │
│    Sensors      │
└─────────────────┘
```

## Process Management and Scaling

### Worker Process Lifecycle
1. Parent process creates worker via fork()
2. Worker initializes matrix calculator
3. Worker enters computation loop:
   - Allocate memory for matrices
   - Perform calculations
   - Check for size updates
   - Handle signals
4. Cleanup on termination

### Dynamic Scaling
- Scales based on temperature thresholds
- Uses CPU core count as baseline
- Implements graceful shutdown
- Handles resource cleanup

## Known Implementation Details

### Temperature Monitoring Permissions
- Requires sudo for powermetrics
- Falls back to zero if permission denied
- May require manual termination if permissions issue occurs

### Memory Management
- Large matrix operations use numpy's memory management
- Shared memory for inter-process communication
- Careful cleanup to prevent memory leaks

### Process Control
- Signal handling for graceful shutdown
- Resource cleanup on exit
- Zombie process prevention

## Performance Considerations

### CPU Load Generation
- Matrix operations chosen for predictable load
- Operations designed to prevent compiler optimization
- Balanced between memory and CPU intensity

### Memory Usage
- Controlled matrix sizes to prevent swapping
- Efficient use of shared memory
- Proper cleanup to prevent leaks

### Temperature Control
- Adaptive workload based on temperature
- Safety thresholds for hardware protection
- Graceful degradation under high load