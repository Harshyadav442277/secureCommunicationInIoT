import paho.mqtt.client as mqtt
import ssl
import time
import random
import json  # <-- 1. Import json
import uuid  # <-- 2. Import uuid

# --- Connection Details ---
BROKER_HOST = "192.168.56.1" 
BROKER_PORT = 8883
CA_CERT_PATH = "certs/ca.crt"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected securely to broker!")
    else:
        print(f"Connection failed with code {rc}")

client = mqtt.Client(client_id="secure-iot-device")
client.on_connect = on_connect
client.username_pw_set(username="iotdevice", password="ourprojectwillwork")
client.tls_set(
    ca_certs=CA_CERT_PATH,
    tls_version=ssl.PROTOCOL_TLSv1_2
)

try:
    client.connect(BROKER_HOST, BROKER_PORT, 60)
except Exception as e:
    print(f"Could not connect: {e}")

client.loop_start()

print("Publishing messages with replay protection...")
try:
    while True:
        # --- 3. THIS IS THE NEW PAYLOAD LOGIC ---
        
        # Get the data
        temp = round(random.uniform(20.0, 30.0), 1)
        current_time = int(time.time()) # Get current time as a simple integer
        nonce = uuid.uuid4().hex # Generate a unique ID
        
        # Pack it into a Python dictionary
        payload_data = {
            "temperature": temp,
            "timestamp": current_time,
            "nonce": nonce
        }
        
        # Convert the dictionary to a JSON string
        payload = json.dumps(payload_data)
        
        # --- END OF NEW LOGIC ---
        
        client.publish("iot/sensor/temp", payload)
        print(f"Published: {payload}")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nDisconnecting...")
    pass

client.loop_stop()
client.disconnect()
