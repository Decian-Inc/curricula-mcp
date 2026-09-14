# Curricula MCP

An MCP server that exposes all 44 operations in the Huntress Curricula public API. It uses the OAuth access token issued by Curricula and supports the production and development-sandbox APIs.

## Install

```bash
pip install curricula-mcp
```

Or run from a checkout:

```bash
pip install -e .
```

## Configure

Create an OAuth access token with the Curricula scopes required for the operations you plan to use, then set:

```bash
export CURRICULA_ACCESS_TOKEN="your-access-token"
# Optional; default is production.
export CURRICULA_BASE_URL="https://mycurricula.com/api/v1"
```

For the development sandbox, set `CURRICULA_BASE_URL=https://dev.curricula.com/api/v1`.

The server sends `Authorization: Bearer <token>` and uses the JSON:API media type. See the [Curricula authentication and scopes documentation](https://curricula.stoplight.io/docs/curricula-api/90755b35b33f4-authentication).

## Connect an MCP client

```json
{
  "mcpServers": {
    "curricula": {
      "command": "curricula-mcp",
      "env": {
        "CURRICULA_ACCESS_TOKEN": "your-access-token"
      }
    }
  }
}
```

Each API operation is an MCP tool. Supply URI identifiers through `path_params`, filters/pagination/includes through `query`, and JSON:API request content through `body`. For example:

```json
{
  "path_params": {"accountId": "abc123"},
  "query": {"include": "learners", "page": 1, "perPage": 50}
}
```

See [TOOLS.md](TOOLS.md) for the complete catalog.

## Safety

Most tools are read-only. The five state-changing tools (`delete_account`, `report_phishing_attempt`, `create_admin_user`, `update_admin_user`, and `delete_admin_user`) forward the request immediately. Agents should confirm intent before calling them.

## Development

```bash
pip install -e ".[dev]"
pytest
```

