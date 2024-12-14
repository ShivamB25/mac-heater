from controller import HeatingController

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