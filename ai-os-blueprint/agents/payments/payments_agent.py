import os
import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/make_payment', methods=['POST'])
def make_payment():
    """
    Implements the 'make_payment' capability.
    Expects a JSON body with amount, merchant, and a payment_token_key.
    """
    data = request.get_json()
    if not data or not all(k in data for k in ["amount", "merchant", "payment_token_key"]):
        return jsonify({"error": "Missing required payment parameters"}), 400

    amount = data["amount"]
    currency = data.get("currency", "USD")
    merchant = data["merchant"]
    token_key = data["payment_token_key"]

    # In a real-world agent, this is where it would connect to a payment
    # processor's API (e.g., Stripe) using a securely handled payment token.
    # For this simulation, we just log the action.
    print(f"Simulating payment of {amount} {currency} to '{merchant}' using token key '{token_key}'.")

    # Simulate a successful payment transaction and return a confirmation.
    response_data = {
        "transaction_id": f"txn_{uuid.uuid4().hex}",
        "status": "approved",
        "amount_paid": amount,
        "merchant_name": merchant
    }
    return jsonify(response_data)

@app.route('/health', methods=['GET'])
def health_check():
    """A simple health check endpoint for the agent."""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # Defaulting to port 5003 to avoid conflict with other agents.
    port = int(os.environ.get('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=True)
