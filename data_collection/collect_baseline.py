import serial
import csv
import time

# --- Configuration ---
com_port = 'COM8'
baud_rate = 460800
samples_needed = 5000  # 5000 samples @ 500Hz = Exactly 10 seconds of data
csv_filename = 'imbalance_anomaly.csv'

try:
    ser = serial.Serial(com_port, baud_rate, timeout=1)
    print(f"Connected to {com_port}")
    
    # 1. Flush the buffer ONCE before we start, so we start with a clean slate
    ser.reset_input_buffer() 
    print("Buffer cleared. Starting pristine 500Hz capture...")
    print(f"Recording {samples_needed} samples. DO NOT TOUCH THE RIG...")

    with open(csv_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        # NanoEdge AI Studio usually just wants raw numbers without timestamps
        writer.writerow(['accel_x', 'accel_y', 'accel_z']) 
        
        count = 0
        while count < samples_needed:
            try:
                # 2. Notice there is NO reset_input_buffer() here! 
                # We catch every single wave peak and valley.
                raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
                parts = raw_line.split(',')
                
                if len(parts) == 3:
                    g_x = round(float(parts[0]) / 4096.0, 3)
                    g_y = round(float(parts[1]) / 4096.0, 3)
                    g_z = round(float(parts[2]) / 4096.0, 3)
                    
                    writer.writerow([g_x, g_y, g_z])
                    count += 1
                    
                    # Print progress every 1 second (500 samples)
                    if count % 500 == 0:
                        print(f"Progress: {count} / {samples_needed} samples saved.")
                        
            except (ValueError, IndexError):
                pass # Ignore mid-transmission glitches

    print(f"\nSUCCESS! 10 seconds of perfect 500Hz data saved to '{csv_filename}'.")
    ser.close()

except serial.SerialException as e:
    print(f"ERROR: {e}")