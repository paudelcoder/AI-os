import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/request_ride', methods=['POST'])
def request_ride():
    """
    Implements the 'request_ride' capability.
    Expects a JSON body with a 'destination' key.
    """
    data = request.get_json()
    if not data or "destination" not in data:
        return jsonify({"error": "Missing 'destination' in request body"}), 400

    # Simulate a successful ride booking with dummy data
    destination = data["destination"]
    vehicle_type = data.get("vehicle_type", "standard")

    print(f"Ride requested to '{destination}' in a '{vehicle_type}' vehicle.")

    # Return a dummy response that matches the manifest's output_schema
    response_data = {
        "ride_id": "ride_xyz_789123",
        "driver_name": "Alex",
        "eta_minutes": 5,
        "price_estimate": 15.75
    }
    return jsonify(response_data)

@app.route('/health', methods=['GET'])
def health_check():
    """A simple health check endpoint for the agent."""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # Defaulting to port 5002 to avoid conflict with the calendar agent (5001)
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)
