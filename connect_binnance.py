import json
import csv
import time
import io
from collections import deque, defaultdict
from datetime import datetime, timezone
import requests
import websocket
from publish_to_queue import init_rabbitmq, publish_to_rabbitmq
from minio import Minio

# =========================
# CONFIG
# =========================
SYMBOLS = ["btcusdt", "ethusdt"]  # lowercase
INTERVAL = "1m"

# Default Thresholds (Fallback)
# PRICE_THRESHOLDS = {
#     "btcusdt": (93099.18, 93100.18),
#     "ethusdt": (3317.88, 3320.88),
# }

PCT_MOVE_THRESHOLD = 0.7  
VOLUME_SPIKE_MULT = 3.0   
VOLUME_ROLLING_WINDOW = 30 

vol_hist = defaultdict(lambda: deque(maxlen=VOLUME_ROLLING_WINDOW))

def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()

# =========================
# MINIO CONFIG
# =========================
MINIO_ENDPOINT = "minio:9000"  
MINIO_ACCESS_KEY = "minio"
MINIO_SECRET_KEY = "minio123"
MINIO_BUCKET = "alerts"
MINIO_BUCKET_FOR_RAW_DATA = "rawdata"

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

# Ensure buckets exist
if not minio_client.bucket_exists(MINIO_BUCKET):
    minio_client.make_bucket(MINIO_BUCKET)

if not minio_client.bucket_exists(MINIO_BUCKET_FOR_RAW_DATA):
    minio_client.make_bucket(MINIO_BUCKET_FOR_RAW_DATA)

def make_alert(symbol, alert_type, message, price=None, pct_move=None, volume=None, vol_avg=None):
    return {
        "event_type": alert_type,
        "symbol": symbol,
        "timestamp_utc": utc_now_iso(),
        "message": message,
        "metrics": {
            "price": price,
            "pct_move": pct_move,
            "volume": volume,
            "volume_avg": vol_avg
        },
        "source": "binance-websocket",
        "interval": INTERVAL
    }

def make_raw_data(symbol, price=None):
    return {
        "event_type": "raw_type",
        "symbol": symbol,
        "timestamp_utc": utc_now_iso(),
        "price": price
    }

def get_live_thresholds():
    """Διαβάζει τα thresholds από το MinIO bucket 'thresholds'."""
    try:
        bucket_name = "thresholds"
        object_name = "config.json"
        
        # Έλεγχος αν υπάρχει το bucket και το αρχείο
        # Αν δεν υπάρχει το bucket, θα πετάξει exception που πιάνουμε παρακάτω
        response = minio_client.get_object(bucket_name, object_name)
        content = json.loads(response.read().decode("utf-8"))
        response.close()
        response.release_conn()
        
        # FIX: Χρήση f-string για να μην σκάει το print επειδή το content είναι dict
        # print(f"Thresholds loaded: {content}") 
        return content
    except Exception as e:
        # print(f"[INFO] Could not load live thresholds (using defaults): {e}")
        return None

def save_raw_data_to_minio(data_obj, minio_client):
    try:
        ts = data_obj["timestamp_utc"].replace(":", "-")
        symbol = data_obj["symbol"]
        object_name = f"raw_data/{symbol}/{ts}.json"
        
        data_bytes = json.dumps(data_obj).encode("utf-8")
        
        minio_client.put_object(
            MINIO_BUCKET_FOR_RAW_DATA,
            object_name,
            io.BytesIO(data_bytes),
            length=len(data_bytes),
            content_type="application/json"
        )
        # print(f"[MINIO] Saved raw data to {object_name}")
    except Exception as e:
        print("[WARN] Failed to save raw data to MinIO:", repr(e))

# =========================
# RULES
# =========================
def check_rules(symbol, o, c, v):
    alerts = []
    
    # 1. Δημιουργία Raw Data Object
    raw_data_obj = make_raw_data(symbol, c)

    # 2. Αποθήκευση Raw Data στο Minio
    save_raw_data_to_minio(raw_data_obj, minio_client)

    # 4. Λήψη Δυναμικών Thresholds
    live_cfg = get_live_thresholds()
    
    below = None
    above = None

    if live_cfg and symbol in live_cfg:
        try:
            below = float(live_cfg[symbol].get("min"))
            above = float(live_cfg[symbol].get("max"))
            # FIX: f-string για αποφυγή TypeError (str + float)
            # print(f"Live Config -> below: {below}, above: {above}")
        except (ValueError, TypeError):
            print(f"[WARN] Invalid numeric values in MinIO config for {symbol}")
            below, above = PRICE_THRESHOLDS.get(symbol, (None, None))
    else:
        below, above = PRICE_THRESHOLDS.get(symbol, (None, None))

    # 5. Έλεγχος Price Threshold
    if above is not None and c > above:
        alerts.append(make_alert(symbol, "PRICE_ABOVE", f"Close {c:.4f} > {above}", price=c))
    if below is not None and c < below:
        alerts.append(make_alert(symbol, "PRICE_BELOW", f"Close {c:.4f} < {below}", price=c))
    
    # 6. % move in candle
    if o > 0:
        pct_move = abs((c - o) / o) * 100.0
        if pct_move >= PCT_MOVE_THRESHOLD:
            alerts.append(make_alert(symbol, "PCT_MOVE", f"1m move {pct_move:.2f}%", price=c, pct_move=pct_move, volume=v))

    # 7. Volume spike
    hist = vol_hist[symbol]
    if len(hist) >= 10:
        vol_avg = sum(hist) / len(hist)
        if vol_avg > 0 and v > VOLUME_SPIKE_MULT * vol_avg:
            alerts.append(make_alert(symbol, "VOLUME_SPIKE", f"Vol {v:.2f} > {VOLUME_SPIKE_MULT}x avg", price=c, volume=v, vol_avg=vol_avg))
    
    # 8. Δημοσίευση Alerts
    for alert in alerts:
        # Αν η publish_to_rabbitmq δεν κάνει json.dumps μέσα της, 
        # βεβαιώσου ότι στέλνεις json string ή dictionary ανάλογα με το τι περιμένει.
        # Συνήθως οι βιβλιοθήκες RabbitMQ θέλουν bytes ή string.
        publish_to_rabbitmq(alert)
        print(f"[ALERT] {symbol} {alert['event_type']}: {alert['message']}")

# =========================
# WEBSOCKET HANDLERS
# =========================
def on_message(ws, message):
    try:
        msg = json.loads(message)
        data = msg.get("data", msg)

        if data.get("e") != "kline":
            return

        k = data["k"]
        symbol = k["s"].lower()
        is_closed = bool(k["x"])
        
        # Parsing values
        o = float(k["o"])
        c = float(k["c"])
        v = float(k["v"])

        if is_closed:
            check_rules(symbol, o, c, v)
            vol_hist[symbol].append(v)

    except Exception as e:
        print("[WARN] failed to parse message:", repr(e))

def on_error(ws, error):
    print("[ERROR]", error)

def on_close(ws, close_status_code, close_msg):
    print("[CLOSE]", close_status_code, close_msg)

def on_open(ws):
    print("[OPEN] Connected to Binance WebSocket")

# =========================
# MAIN
# =========================
def main():
    streams = "/".join([f"{s}@kline_{INTERVAL}" for s in SYMBOLS])
    ws_url = f"wss://stream.binance.com:9443/stream?streams={streams}"
    print("Streaming URL:", ws_url)

    while True:
        try:
            ws = websocket.WebSocketApp(
                ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever(ping_interval=20, ping_timeout=10)
        except KeyboardInterrupt:
            print("\nStopped by user.")
            break
        except Exception as e:
            print("[WARN] reconnecting after error:", repr(e))
            time.sleep(3)

if __name__ == "__main__":
    connected = False
    while not connected:
        try:
            init_rabbitmq()
            connected = True
            print("Successfully connected to RabbitMQ")
        except Exception as e:
            print(f"RabbitMQ not ready yet, retrying in 5 seconds... ({e})")
            time.sleep(5)
    main()