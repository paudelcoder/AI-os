import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# A simple in-memory database of calendar events for demonstration purposes.
DUMMY_EVENTS = {
    "2024-09-27": [
        {"title": "Team Standup", "time": "10:00", "duration_minutes": 15},
        {"title": "Design Review", "time": "14:30", "duration_minutes": 90},
    ],
    "2024-09-28": [
        {"title": "Project Kick-off", "time": "11:00", "duration_minutes": 60},
    ],
}

@app.route('/search_calendar_events', methods=['GET'])
def search_calendar_events():
    """
    Implements the 'search_calendar_events' capability.
    Expects a 'date' query parameter in 'YYYY-MM-DD' format.
    """
    query_date = request.args.get('date')

    if not query_date:
        return jsonify({"error": "Missing 'date' parameter"}), 400

    events = DUMMY_EVENTS.get(query_date, [])

    # The output should match the 'output_schema' in the agent_manifest.json
    return jsonify({"events": events})

@app.route('/health', methods=['GET'])
def health_check():
    """A simple health check endpoint."""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # The port can be configured via an environment variable, defaulting to 5001.
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
