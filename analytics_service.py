from flask import Flask, jsonify, request, make_response
from minio import Minio
import json, io
from functools import wraps

app = Flask(__name__)
client = Minio("minio:9000", "minio", "minio123", secure=False)

# Οι κωδικοί πρόσβασης
USER_DATA = {
    "tasos": "charis"
}

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username in USER_DATA and USER_DATA[auth.username] == auth.password):
            return make_response('Unauthorised User', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated

@app.route('/get-prediction/<symbol>')
@auth_required
def calculate_prediction(symbol):
    try:
        # 1. Διάβασμα παραμέτρου από το URL (π.χ. ?limit=1000). Default το 20.
        limit = request.args.get('limit', default=20, type=int)
        
        bucket = "rawdata"
        prefix = f"raw_data/{symbol}/"
        objects = list(client.list_objects(bucket, prefix=prefix, recursive=True))
        
        total_found = len(objects)
        if total_found < 2:
            return jsonify({"error": "Not enough data to calculate even a simple trend", "samples": total_found}), 400

        # 2. ΠΡΟΣΑΡΜΟΓΗ: Αν ο χρήστης ζητήσει 1000 αλλά έχουμε 32, παίρνουμε τα 32.
        # Αν έχουμε 5000, παίρνουμε τα τελευταία 1000.
        actual_limit = min(limit, total_found)
        
        # Παίρνουμε τα αντικείμενα για το "παρελθόν" (όλα εκτός από το τελευταίο)
        history_objects = objects[-(actual_limit):-1]
        
        prices = []
        for obj in history_objects:
            data = client.get_object(bucket, obj.object_name)
            content = json.loads(data.read().decode())
            prices.append(float(content['price']))
        
        # Υπολογισμός Μέσου Όρου με βάση το δυναμικό πλήθος δειγμάτων
        avg_price = sum(prices) / len(prices)

        # 3. Παίρνουμε το ΤΕΛΕΥΤΑΙΟ κερί για σύγκριση
        current_obj = objects[-1]
        current_data = client.get_object(bucket, current_obj.object_name)
        current_content = json.loads(current_data.read().decode())
        current_price = float(current_content['price'])

        # 4. Υπολογισμός Απόκλισης
        diff_pct = (abs(current_price - avg_price) / avg_price) * 100
        is_outlier = diff_pct > 0.5

        return jsonify({
            "symbol": symbol,
            "requested_limit": limit,
            "actual_samples_used": len(prices),
            "current_price": current_price,
            "moving_avg": round(avg_price, 2),
            "deviation_pct": round(diff_pct, 4),
            "is_anomaly": bool(is_outlier),
            "status": "Success using available data" if actual_limit < limit else "Full limit reached"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@app.route('/set-thresholds', methods=['POST'])
@auth_required
def set_thresholds():
    try:
        # 1. Λήψη δεδομένων από το JSON body του request
        data = request.get_json()
        
        # Αναμενόμενο format: 
        # {
        #   "btcusdt": {"min": 93000.0, "max": 94000.0},
        #   "ethusdt": {"min": 3300.0, "max": 3400.0}
        # }
        if not data:
            return jsonify({"error": "No data provided"}), 400

        bucket_name = "thresholds" # Το bucket που θα περιέχει τα configs
        object_name = "config.json" # Το αρχείο μέσα στο bucket

        # 2. Έλεγχος αν υπάρχει το bucket, αλλιώς δημιουργία
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"Bucket {bucket_name} created.")

        # 3. Μετατροπή του dict σε bytes για το MinIO
        json_data = json.dumps(data).encode('utf-8')
        data_stream = io.BytesIO(json_data)

        # 4. Ανέβασμα του αρχείου (Overwrite το παλιό αν υπάρχει)
        client.put_object(
            bucket_name,
            object_name,
            data_stream,
            length=len(json_data),
            content_type='application/json'
        )

        return jsonify({
            "status": "success",
            "message": "Thresholds updated in MinIO",
            "path": f"{bucket_name}/{object_name}",
            "data": data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)