# Reference Agent: Calendar

This directory contains a reference implementation of a simple "Calendar" agent for the AI-First OS.

The agent is a small web service written in Python using the Flask framework. It exposes a single capability as defined in its `agent_manifest.json`.

## Files

- **`agent_manifest.json`**: Declares the capabilities of this agent (`search_calendar_events`).
- **`calendar_agent.py`**: The Flask application source code.
- **`requirements.txt`**: Python dependencies (just Flask).
- **`Dockerfile`**: Instructions to build a container image for the agent.

## Capability: `search_calendar_events`

- **Endpoint**: `POST /search_calendar_events`
- **JSON Body**: `{"date": "YYYY-MM-DD"}`
- **Success Response**: A JSON object containing a list of events.
  ```json
  {
    "events": [
      {
        "title": "Team Standup",
        "time": "10:00",
        "duration_minutes": 15
      }
    ]
  }
  ```
- **Error Response**: A JSON object with an error message if the `date` key is missing.

## Running the Agent with Docker

This agent is designed to be run as a container, which is how the AI OS would manage and isolate agents.

### 1. Build the Docker Image

From within this directory (`agents/calendar`), run the following command:

```sh
docker build -t calendar-agent:latest .
```

### 2. Run the Docker Container

Once the image is built, you can run it as a container:

```sh
docker run -p 5001:5001 calendar-agent:latest
```

The agent will now be running and listening on port 5001 on your local machine.

### 3. Test the Agent

You can test the running agent by sending a request to its endpoint. Open a new terminal and use `curl`:

```sh
# Test with a date that has events
curl -X POST -H "Content-Type: application/json" -d '{"date": "2024-09-27"}' http://localhost:5001/search_calendar_events

# Test with a date that has no events
curl -X POST -H "Content-Type: application/json" -d '{"date": "2024-01-01"}' http://localhost:5001/search_calendar_events

# Test the health check endpoint
curl http://localhost:5001/health
```
