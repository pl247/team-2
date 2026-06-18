# Machine Downtime Log

A real-time tracker for manufacturing-floor machine stoppages designed to run on Cisco Secure AI Factory.

## What This App Does

Monitors live machine event streams and automatically logs machine stoppages as downtime tickets, recording:
- Machine ID
- Machine type  
- Start time
- End time
- Downtime in minutes

Features a live dashboard showing:
- Total downtime minutes today across all machines
- Visual highlight of the worst machine by downtime today
- Running list of events
- On-screen event-to-display latency indicator (in milliseconds)
- On-prem secure operation indicator

Logging is automatic with no manual entry required, but allows manual notes. The latency indicator proves the no-cloud-round-trip advantage of the Cisco Secure AI Factory's high-performance local network.

## Cisco Secure AI Factory Benefits

- **On-Premises**: All processing and data stays within your secure facility
- **Secure**: No external dependencies or data egress; runs entirely on-prem
- **High-Performance Network**: Sub-millisecond latency demonstrated by real-time UI updates
- **Splunk Visibility**: Structured stdout logging for easy integration with Splunk monitoring

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_PORT` | 8742 | Port for the web application |
| `LLM_BASE_URL` | http://ray-serve-llama.apps.rtp-ai1-ucs.svpod.dc-01.com/v1 | Base URL for the vLLM server |
| `LLM_MODEL` | /nvidia/nemotron-3-super | Model identifier for the Nemotron model |
| `LLM_API_KEY` | *** | API key for the LLM service (read from .env) |
| `LLM_TIMEOUT_SECONDS` | 15 | Timeout for LLM requests in seconds |
| `DB_PATH` | /data/downtime.db | Path to SQLite database file |
| `SIMULATOR_ENABLED` | true | Whether to run the built-in event simulator |
| `SIMULATOR_INTERVAL_SECONDS` | 8 | Interval between simulated events in seconds |
| `GITHUB_REPO` | https://github.com/pl247/team-2 | GitHub repository for source code |
| `GHCR_IMAGE` | ghcr.io/pl247/team-1 | GitHub Container Registry image location |

## Prerequisites

- Ubuntu host
- Docker and Docker Compose
- Access to GitHub Container Registry (GHCR)
- GitHub token stored in `hermes/.env` file (not committed)
- Running vLLM server with NVIDIA Nemotron model (accessible at LLM_BASE_URL)

## Local Development & Testing

1. Clone the repository:
   ```bash
   git clone https://github.com/pl247/team-2.git
   cd team-2
   ```

2. Copy hermes/.env.example to hermes/.env and add your GitHub token:
   ```bash
   cp hermes/.env.example hermes/.env
   # Edit hermes/.env to add GITHUB_TOKEN=your_token_here
   ```

3. Build and run with Docker Compose:
   ```bash
   docker compose up --build
   ```

4. Open your browser to http://localhost:8742 (or whatever APP_PORT is set to)

## Production Deployment on Cisco Secure AI Factory

1. Ensure your vLLM server with Nemotron model is running and accessible
2. Verify GitHub token is in hermes/.env
3. Run:
   ```bash
   docker compose up -d
   ```

4. Access the application at http://<your-host>:8742

## Project Structure

```
machine-downtime-log/
├── app/                    # Main application code
│   ├── __init__.py
│   ├── main.py            # FastAPI application
│   ├── models.py          # Database models
│   ├── database.py        # SQLite database layer
│   ├── event_simulator.py # Built-in event simulator
│   ├── llm_client.py      # LLM integration with fallback
│   └── templates/         # HTML templates
│       └── index.html     # Single-page dashboard
├── hermes/                 # Environment configuration
│   └── .env.example       # Example environment file
├── .github/
│   └── workflows/
│       └── docker-publish.yml # GitHub Actions workflow
├── Dockerfile              # Container image definition
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies (pinned versions)
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Architecture Overview

- **Backend**: Python FastAPI serving REST API and WebSocket/SSE endpoints
- **Frontend**: Single-page HTML/JavaScript served directly by FastAPI (no separate build step)
- **Database**: SQLite with automatic migrations, persisted to `/data` volume
- **Real-time Updates**: Server-Sent Events (SSE) for efficient streaming to frontend
- **Event Simulation**: Built-in simulator for testing/demo (toggleable via env var)
- **LLM Integration**: Calls on-prem vLLM/Nemotron for event classification with graceful fallback
- **Containerization**: Multi-stage Docker build using slim Python base image
- **Orchestration**: Docker Compose with volume persistence and environment configuration

## Key Features

✅ Automatic downtime ticket creation from event stream  
✅ Live dashboard with real-time updates  
✅ Event classification via on-prem LLM (Nemotron)  
✅ Graceful LLM failure handling (never crashes the stream)  
✅ Event-to-display latency monitoring  
✅ On-prem security indicator  
✅ Manual note addition capability  
✅ Structured logging for Splunk integration  
✅ Port conflict detection with clear error messages  
✅ GitHub Container Registry integration  
✅ Automated build/publish via GitHub Actions  

## Error Handling

- **Port Conflicts**: Clear error message on stderr if APP_PORT is in use
- **LLM Failures**: Graceful fallback to Unclassified/Medium classification
- **Database Errors**: Application continues operating with degraded functionality
- **Network Issues**: Frontend handles disconnections gracefully with reconnection logic

## Version Pinning

All Python dependencies are pinned to specific versions in requirements.txt to ensure reproducible builds.

## Security Notes

- Never hardcodes or prints sensitive credentials
- GitHub token is read exclusively from hermes/.env
- All data processing occurs on-prem within the Cisco Secure AI Factory
- No external API calls except to the internal vLLM server
- Container runs as non-root user where possible