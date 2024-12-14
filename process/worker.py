import signal
import sys
from calculations.matrix import MatrixCalculator

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