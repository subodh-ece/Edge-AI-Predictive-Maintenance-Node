from flask import Flask, render_template, jsonify
import threading
import random
import time
import serial
import os 
import csv 

app = Flask(__name__)
latest_data = {
    "x_axis": 0,
    "y_axis" :0,
    "z_axis" : 0,
    "status": "baseline"
}
def read_serial_port():
    global latest_data
    com_port = 'COM8'
    baud_rate = 460800 # 500Hz sampling rate
    csv_filename = 'motor_baseline.csv'
    
    # Check if file exists so we only write headers once
    file_exists = os.path.isfile(csv_filename)

    try :
        ser = serial.Serial(com_port, baud_rate, timeout=1)
        print(f"SUCCESS: Connected to STM32 on com port: {com_port}")
        
        # OPEN FILE ONCE, KEEP IT OPEN FOR THE DURATION
        with open(csv_filename, 'a', newline='') as f:
            writer = csv.writer(f)
            
            # Write headers if it's a brand new file
            if not file_exists:
                writer.writerow(['timestamp', 'accel_x', 'accel_y', 'accel_z'])
            
            print("Listening for data at 500Hz...")
            print_throttle_counter = 0 
            
            while True:
                if ser.in_waiting > 0:
                    try:
                        # Decode inside the try block with error ignoring!
                        # 1. Throw away the massive backlog of 500Hz data waiting in the USB port
                        ser.reset_input_buffer()
                        raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
                        parts = raw_line.split(',')
                        
                        if len(parts) == 3:
                            g_x = round(float(parts[0]) / 4096.0, 3)
                            g_y = round(float(parts[1]) / 4096.0, 3)
                            g_z = round(float(parts[2]) / 4096.0, 3)
                            current_time = time.time()
                            
                            # Fast write to the already-open file
                            writer.writerow([current_time, g_x, g_y, g_z])
                            
                            # Update global dict for Flask to serve
                            latest_data["x_axis"] = g_x
                            latest_data["y_axis"] = g_y
                            latest_data["z_axis"] = g_z
                            latest_data["status"] = "Hardware Connected (3D Data)"
                            
                            # Throttle the terminal print to prevent UI freezing
                            # Only print 5 times a second (every 100th reading)
                            print_throttle_counter += 1
                            if print_throttle_counter >= 100:
                                print(f"X: {g_x}g | Y: {g_y}g | Z: {g_z}g")
                                print_throttle_counter = 0
                                
                    except (ValueError, IndexError):
                        # Gracefully ignore incomplete lines or math conversion errors
                        pass
                        
    except serial.SerialException as e:
        print(f"ERROR: Could not open {com_port}.")
        print(e)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_sensor_data():
    # Flask simply serves whatever the background thread last recorded
    return jsonify(latest_data)

if __name__ == '__main__':
    #Hardware reading thread 
    hardware_thread = threading.Thread(target=read_serial_port)
    hardware_thread.daemon = True # Ensures thread closes when Flask closes
    hardware_thread.start()
    
    
    app.run(debug=True, port=5000, use_reloader=False) 
    # use_reloader is false to avoid the formation of duplicate threads ! 