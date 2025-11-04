import paho.mqtt.client as mqtt
import ssl
import json 
import time 

# --- Connection Details ---
BROKER_HOST = "192.168.56.1"
BROKER_PORT = 8883
CA_CERT_PATH = "certs/ca.crt"

# --- Replay Protection Settings ---
MAX_TIME_SKEW_SECONDS = 10 
seen_nonces = set() 

# --- 1. NEW: Rate Limiting Settings ---
MESSAGE_RATE_LIMIT = 20  # Max 20 messages
MESSAGE_RATE_WINDOW = 10 # in any 10 second window
message_timestamps = []  # List to store timestamps

# This function runs when a message is received
def on_message(client, userdata, msg):
    # --- 2. NEW: Rate Limiting Logic ---
    global message_timestamps # Tell Python we are using the global list
    current_time = time.time()
    
    # 2a. Clean out old timestamps
    message_timestamps = [t for t in message_timestamps if current_time - t < MESSAGE_RATE_WINDOW]
    
    # 2b. Check if we're over the limit
    if len(message_timestamps) >= MESSAGE_RATE_LIMIT:
        print(f"[RATE LIMIT EXCEEDED] Ignoring message. Current count: {len(message_timestamps)}")
        return # <-- Stop processing the message
        
    # 2c. If we're not over limit, add this message's timestamp
    message_timestamps.append(current_time)
    # --- END OF NEW RATE LIMIT LOGIC ---

    print(f"\nReceived raw message: {msg.payload.decode()}")
    
    try:
        # --- (The rest of your code is the same) ---
        data = json.loads(msg.payload.decode()) 
        
        # --- Check 1: Timestamp (Replay) ---
        msg_time = data.get("timestamp")
        
        if (current_time - msg_time) > MAX_TIME_SKEW_SECONDS:
            print(f"[REPLAY ATTACK DETECTED] Message timestamp is too old!")
            return 
            
        # --- Check 2: Nonce (Replay) ---
        nonce = data.get("nonce")
        if nonce in seen_nonces:
            print(f"[REPLAY ATTACK DETECTED] Nonce has been used before!")
            return 
            
        seen_nonces.add(nonce)
        
        temp = data.get("temperature")
        print(f"[VALID MESSAGE] Processed temperature: {temp} C")

    except json.JSONDecodeError:
        print(f"[WARNING] Received malformed (non-JSON) message.")
    except Exception as e:
        print(f"An error occurred: {e}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected securely to broker!")
        client.subscribe("iot/sensor/temp")
    else:
        print(f"Connection failed with code {rc}")

client = mqtt.Client(client_id="secure-subscriber")
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(username="iotdevice", password="ourprojectwillwork")
client.tls_set(
    ca_certs=CA_CERT_PATH,
    tls_version=ssl.PROTOCOL_TLSv1_2
)

try:
    client.connect(BROKER_HOST, BROKER_PORT, 60)
except Exception as e:
    print(f"Could not connect: {e}")
    exit()

print("Listening for messages... Press Ctrl+C to quit.")
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\nDisconnecting...")
    client.disconnect()