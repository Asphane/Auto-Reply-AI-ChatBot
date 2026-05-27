import pyautogui
import time

print("=" * 50)
print("MOUSE COORDINATES CALIBRATOR")
print("=" * 50)
print("Instructions:")
print("1. Hover your mouse over the desired button or location.")
print("2. The coordinates (X, Y) will update below every second.")
print("3. Press Ctrl+C in this terminal to exit.")
print("=" * 50)

try:
    while True:
        x, y = pyautogui.position()
        print(f"Current Position -> X: {x}, Y: {y}      ", end="\r", flush=True)
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\n\nCalibration stopped.")
