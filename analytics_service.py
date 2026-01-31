from flask import Flask, jsonify, request, make_response
from minio import Minio
import json
from functools import wraps

app = Flask(__name__)
client = Minio("172.17.0.1:9000", "minio", "minio123", secure=False)

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
        bucket = "rawdata"
        prefix = f"raw_data/{symbol}/"
        objects = list(client.list_objects(bucket, prefix=prefix, recursive=True))
        
        if len(objects) < 21:
            return jsonify({"error": "Not enough data yet", "samples": len(objects)}), 400

        # 2. Παίρνουμε τα προηγούμενα 20 κεριά
        history_objects = objects[-21:-1]
        prices = []
        for obj in history_objects:
            data = client.get_object(bucket, obj.object_name)
            content = json.loads(data.read().decode())
            prices.append(float(content['price']))
        
        avg_price = sum(prices) / len(prices)

        # 3. Παίρνουμε το ΤΕΛΕΥΤΑΙΟ κερί
        current_obj = objects[-1]
        current_data = client.get_object(bucket, current_obj.object_name)
        current_content = json.loads(current_data.read().decode())
        current_price = float(current_content['price'])

        # 4. Υπολογισμός Απόκλισης
        diff_pct = (abs(current_price - avg_price) / avg_price) * 100
        is_outlier = diff_pct > 0.5

        return jsonify({
            "symbol": symbol,
            "current_price": current_price,
            "moving_avg_20": round(avg_price, 2),
            "deviation_pct": round(diff_pct, 4),
            "is_anomaly": bool(is_outlier),
            "suggested_threshold": round(avg_price * 1.005, 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)