# OpenProject MCP Server

![status](https://img.shields.io/badge/status-WIP-yellow)

A [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server for the [OpenProject](https://www.openproject.org/) API v3. It lets LLM applications — Claude Desktop, Claude Code, and any other MCP client — read and manage projects, work packages, time entries, memberships, and more in your OpenProject instance through natural language.

> ⚠️ **Early-stage project.** Expect rough edges. Not recommended for production use yet.

---

## Table of Contents

- [What you can do](#what-you-can-do)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Connecting an MCP client](#connecting-an-mcp-client)
- [Self-hosting with Docker (internal network)](#self-hosting-with-docker-internal-network)
- [Available tools](#available-tools)
- [Notes & known limitations](#notes--known-limitations)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Security](#security)
- [License](#license)

---

## What you can do

- **Projects** — create, update, delete, list, inspect, manage sub-projects
- **Work packages** — full CRUD plus rich filtering (priority, type, status, dates, completion %, assignee, parent…)
- **Hierarchy & relations** — parent/child links and dependency relations (blocks, follows, relates…)
- **Time tracking** — log, edit, delete, and list time entries
- **Members & roles** — manage memberships, list members and roles
- **Versions** — create and list project versions/milestones
- **News** — create, update, delete, list project news
- **Reports** — generate weekly activity reports
- **Comments & assignment** — comment on and assign work packages

Around **60 tools** in total. See [Available tools](#available-tools).

---

## Requirements

- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package/venv manager
- An **OpenProject instance** (cloud or self-hosted)
- An **OpenProject API key** (see [Getting an API key](#getting-an-api-key))

---

## Quick start

```bash
# 1. Install uv
#    macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
#    Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. Clone
git clone https://github.com/mattiatrombella/openproject-mcp-server.git
cd openproject-mcp-server

# 3. Install dependencies (creates .venv automatically)
uv sync

# 4. Configure credentials
cp env_example.txt .env        # then edit .env

# 5. Run the server (stdio transport)
uv run python openproject-mcp-fastmcp.py
```

---

## Configuration

Credentials come from environment variables, either via a `.env` file or passed directly by your MCP client (preferred — see below).

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENPROJECT_URL` | ✅ | Your instance URL | `https://mycompany.openproject.com` |
| `OPENPROJECT_API_KEY` | ✅ | API key from your account | `8169846b42461e6e...` |
| `OPENPROJECT_PROXY` | ❌ | HTTP proxy URL | `http://proxy.company.com:8080` |
| `LOG_LEVEL` | ❌ | `DEBUG` / `INFO` / `WARNING` / `ERROR` | `INFO` |
| `TEST_CONNECTION_ON_STARTUP` | ❌ | Test API connection at boot | `true` |

### Getting an API key

1. Log in to OpenProject.
2. Open the user menu (top right) → **Account settings**.
3. Go to **Access tokens**.
4. Under **API**, click **+ Api token**, name it, and copy the value.

---

## Connecting an MCP client

The stdio entry point (`openproject-mcp-fastmcp.py`) works with both **Claude Desktop** and **Claude Code (VS Code extension)**.

### Option A — CLI (recommended)

Replace `<PROJECT_PATH>` with your absolute install path.

```powershell
# Windows
claude mcp add openproject-fastmcp "<PROJECT_PATH>\.venv\Scripts\python.exe" "<PROJECT_PATH>\openproject-mcp-fastmcp.py" `
  -e "PYTHONPATH=<PROJECT_PATH>" `
  -e "OPENPROJECT_URL=https://your-instance.com" `
  -e "OPENPROJECT_API_KEY=your-api-key"
```

```bash
# macOS / Linux
claude mcp add openproject-fastmcp "<PROJECT_PATH>/.venv/bin/python" "<PROJECT_PATH>/openproject-mcp-fastmcp.py" \
  -e "PYTHONPATH=<PROJECT_PATH>" \
  -e "OPENPROJECT_URL=https://your-instance.com" \
  -e "OPENPROJECT_API_KEY=your-api-key"
```

Verify:

```bash
claude mcp list
# openproject-fastmcp: ... - ✓ Connected
```

Then restart Claude Desktop or reload the VS Code window.

### Option B — Manual config

Edit your client config file:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "openproject-fastmcp": {
      "command": "<PROJECT_PATH>/.venv/bin/python",
      "args": ["<PROJECT_PATH>/openproject-mcp-fastmcp.py"],
      "env": {
        "PYTHONPATH": "<PROJECT_PATH>",
        "OPENPROJECT_URL": "https://your-instance.com",
        "OPENPROJECT_API_KEY": "your-api-key"
      }
    }
  }
}
```

On Windows use double-backslash paths (e.g. `C:\\Users\\you\\openproject-mcp-server\\.venv\\Scripts\\python.exe`).

> Passing credentials through the client config keeps them out of a committed `.env` file.

**If you see `✗ Failed to connect`:** check the Python path, confirm `openproject-mcp-fastmcp.py` exists, verify the env vars, and restart the client.

---

## Self-hosting with Docker (internal network)

Run one shared server on an internal host so your team connects over the network — no per-user Python install. This uses the **HTTP transport** entry point (`openproject-mcp-http.py`), which adds per-user API-key auth.

### How it works

```
Team clients ──HTTP (port 8000)──▶ Docker host (internal LAN) ──HTTPS──▶ OpenProject
   │                                                                         ▲
   └─ authenticate with their MCP_API_KEYS key                              │
                              the server uses one OPENPROJECT_API_KEY ───────┘
```

- **`OPENPROJECT_API_KEY`** — single key the server uses to talk to OpenProject.
- **`MCP_API_KEYS`** — per-user keys clients present to the server, format `key:User,key2:User2`. Used to identify/track who calls. If unset, HTTP auth is disabled (don't do that on a shared network).

### 1. Configure

Edit the `environment:` block in [docker-compose.yml](docker-compose.yml), or create a `.env` file and switch the compose service to `env_file: .env`:

```env
OPENPROJECT_URL=https://your-instance.openproject.com
OPENPROJECT_API_KEY=your-openproject-api-key
MCP_API_KEYS=alice-secret:Alice,bob-secret:Bob
MCP_HTTP_HOST=0.0.0.0
MCP_HTTP_PORT=8000
LOG_LEVEL=INFO
```

### 2. Build & run

```bash
docker compose up -d --build      # build image and start detached
docker compose logs -f            # follow startup logs
```

You should see `Loaded N API keys` and the server listening on `0.0.0.0:8000`.

Without compose:

```bash
docker build -t openproject-mcp .
docker run -d --name openproject-mcp --restart unless-stopped \
  -p 8000:8000 \
  -e OPENPROJECT_URL=https://your-instance.openproject.com \
  -e OPENPROJECT_API_KEY=your-openproject-api-key \
  -e MCP_API_KEYS="alice-secret:Alice,bob-secret:Bob" \
  openproject-mcp
```

### 3. Connect clients

Point each user's MCP client at the host (replace `mcp-host.internal` with the server's LAN hostname or IP, and use that user's key):

```json
{
  "mcpServers": {
    "openproject": {
      "url": "http://mcp-host.internal:8000/mcp",
      "transport": "http",
      "headers": { "Authorization": "Bearer alice-secret" }
    }
  }
}
```

Or via the Claude Code CLI:

```bash
claude mcp add --transport http openproject http://mcp-host.internal:8000/mcp \
  --header "Authorization: Bearer alice-secret"
```

### Production notes

- **TLS**: HTTP is fine inside a trusted LAN. For anything broader, front the container with a reverse proxy (nginx/Caddy/Traefik) terminating HTTPS.
- **Secrets**: keep keys out of git — use a `.env` file (git-ignored) or Docker/host secrets, not the committed compose file.
- **Updates**: `git pull && docker compose up -d --build` to redeploy.
- **Health**: `docker compose ps` and `docker compose logs -f` to check status.

---

## Project structure

```
openproject-mcp-fastmcp.py   # stdio entry point (local clients)
openproject-mcp-http.py      # HTTP entry point (shared/Docker hosting, API-key auth)
Dockerfile                   # container image
docker-compose.yml           # internal-network deployment
src/
  auth.py                    # per-user API-key auth (HTTP transport)
  server.py                  # FastMCP server + tool registration
  client.py                  # OpenProject API v3 client
  tools/                     # tools grouped by domain
    work_packages.py  hierarchy.py  relations.py
    projects.py       memberships.py  users.py
    versions.py       time_entries.py  news.py
    weekly_reports.py connection.py
```

---

## Available tools

### Connection
`test_connection`, `check_permissions`

### Work packages
`list_work_packages`, `search_work_packages`, `get_work_package`, `create_work_package`, `update_work_package`, `delete_work_package`, `assign_work_package`, `unassign_work_package`, `add_work_package_comment`, `list_work_package_activities`, `list_types`, `list_statuses`, `list_priorities`

Convenience filters: `list_overdue_work_packages`, `list_work_packages_due_soon`, `list_unassigned_work_packages`, `list_work_packages_created_recently`, `list_high_priority_work_packages`, `list_work_packages_nearly_complete`

`list_work_packages` is the most powerful search tool — it accepts ~23 filter parameters (project, assignee, priority/type/status/version IDs, date ranges, completion %, author, parent, unassigned/overdue flags), all combined with AND logic.

### Hierarchy & relations
`set_work_package_parent`, `remove_work_package_parent`, `list_work_package_children`, `create_work_package_relation`, `list_work_package_relations`, `get_work_package_relation`, `update_work_package_relation`, `delete_work_package_relation`

Relation types: `blocks`, `follows`, `precedes`, `relates`, `duplicates`, `includes`, `requires`, `partof`.

### Projects
`list_projects`, `get_project`, `create_project`, `update_project`, `delete_project`, `get_subprojects`, `add_subproject`

### Members & roles
`list_memberships`, `get_membership`, `create_membership`, `update_membership`, `delete_membership`, `list_project_members`, `list_user_projects`, `list_roles`, `get_role`

### Users
`list_users`, `get_user`

### Time tracking
`list_time_entries`, `create_time_entry`, `update_time_entry`, `delete_time_entry`, `list_time_entry_activities`

### Versions
`list_versions`, `create_version`

### News
`list_news`, `get_news`, `create_news`, `update_news`, `delete_news`

### Reports
`generate_weekly_report`, `generate_this_week_report`, `generate_last_week_report`, `get_report_data`

> Tool parameters are exposed via the MCP schema, so your client (and the LLM) sees the full argument list for each tool at runtime — no need to memorize them.

### Example prompts

```
Find high-priority bugs due this week in project 5
Show me unassigned tasks more than 80% complete
Create a task in project 5 titled "Update docs" of type 1
Log 2.5 hours of Development work on work package 42 for today
Set work package 15 as a child of work package 10
Generate this week's report
```

---

## Notes & known limitations

- **`list_time_entry_activities`** may return `404` on some instances even though time-entry activities work. Common default IDs: `1` Management, `2` Specification, `3` Development, `4` Testing — e.g. `create_time_entry` with `activity_id: 3`.
- **`list_memberships`** user-ID filtering isn't supported on all instances; project-level and global filtering work reliably.
- **`list_high_priority_work_packages`** assumes priority ID `3` = "High". If your instance differs, run `list_priorities` and pass `priority_ids` to `list_work_packages` instead.
- Most create/update/delete operations require matching OpenProject permissions. Run `check_permissions` to diagnose `403` errors.

---

## Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| `401 Unauthorized` | API key wrong or inactive |
| `403 Forbidden` | User lacks the required permission |
| `404 Not Found` | Wrong URL, or the resource doesn't exist |
| Proxy errors | Check `OPENPROJECT_PROXY` and proxy auth |
| SSL errors | Self-signed certs or proxy SSL interception |
| No projects found | API user lacks project-view permission |

Enable verbose logs with `LOG_LEVEL=DEBUG`.

---

## Development

```bash
uv sync --extra dev          # install dev dependencies
uv run pytest tests/         # run tests
uv run black src/            # format
uv run flake8 src/           # lint
uv add <package>             # add a dependency
```

---

## Security

- Never commit your `.env` file (it's git-ignored).
- Prefer passing credentials via the MCP client config over a `.env` file.
- Rotate API keys periodically and always use HTTPS.

---

## License

No license is currently granted. This is a fork of
[AndyEverything/openproject-mcp-server](https://github.com/AndyEverything/openproject-mcp-server),
which carries no license — so all rights are reserved by the original author(s).
Until a license is added upstream, you have no granted rights to use, copy, modify,
or distribute this code beyond viewing it. If you intend to reuse it, contact the
original author for permission.

## Acknowledgments

- Built on the [Model Context Protocol](https://modelcontextprotocol.io/) and [FastMCP](https://github.com/jlowin/fastmcp)
- Integrates with [OpenProject](https://www.openproject.org/)
- Forked from [AndyEverything/openproject-mcp-server](https://github.com/AndyEverything/openproject-mcp-server)
