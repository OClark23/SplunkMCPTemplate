# Splunk MCP Template

Template MCP in Python to run Splunk searches, apply count-over-window thresholds, generate a markdown report, open Jira tickets, and post to Microsoft Teams. Credentials are placeholders for you to fill.

## Setup
1. Python 3.10+ recommended.
2. Install deps:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
   or with the project entrypoint:
   ```bash
   pip install -e .
   ```

## Configure
1. Copy `config.example.yaml` to `config.yaml`.
2. Fill placeholders (validation will fail if required fields stay at defaults):
   - `splunk.host`: e.g., `https://your-splunk:8089`
   - `splunk.token` or `splunk.username/password`: add your auth (or env vars).
   - `search.spl`, `earliest`, `latest`: your SPL and time bounds.
   - `threshold.count`, `window_minutes`, `group_by`: set your trigger rules.
   - `jira.base_url`, `project_key`, `user_email`, `api_token`: Jira credentials.
   - `teams.webhook_url`: Teams incoming webhook if you want chat notifications.
3. Ensure `jira.enabled`/`teams.enabled` reflect what you want to call.

## Run
```bash
python -m src.main --config config.yaml            # executes Splunk/Jira/Teams as configured
python -m src.main --config config.yaml --output report.md  # also save report
```
Entrypoint alternative (after `pip install -e .`):
```bash
splunk-mcp --config config.yaml
```

## Notes on credentials
- Splunk: update `splunk.token` (preferred) or `username/password`. Keep them out of version control.
- Jira: set `user_email` + `api_token`; enable `jira.enabled`.
- Teams: set `teams.webhook_url`; enable `teams.enabled`.

## Testing
```bash
pytest
```
