"""MCP server exposing the Huntress Curricula API."""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from mcp.server.fastmcp import FastMCP

DEFAULT_BASE_URL = "https://mycurricula.com/api/v1"
DEFAULT_TOKEN_URL = "https://mycurricula.com/oauth/token"
JSON_API = "application/vnd.api+json"
REQUIRED_MANAGEMENT_SCOPES = "assignments:read assignments:manage learners:read learners:manage"


@dataclass(frozen=True)
class Operation:
    """A public API operation represented by an MCP tool."""

    name: str
    method: str
    path: str
    summary: str
    has_body: bool = False


# Derived from the public Curricula OpenAPI 3.1 specification (version 1.0).
OPERATIONS: tuple[Operation, ...] = (
    Operation("list_accounts", "GET", "/accounts", "List accounts available to the authenticated administrator."),
    Operation("get_account", "GET", "/accounts/{accountId}", "Get an account's details."),
    Operation("delete_account", "DELETE", "/accounts/{accountId}", "Permanently delete an account."),
    Operation("list_account_assignments", "GET", "/accounts/{accountId}/assignments", "List assignments for an account."),
    Operation("list_account_departments", "GET", "/accounts/{accountId}/departments", "List departments in an account."),
    Operation("list_account_groups", "GET", "/accounts/{accountId}/groups", "List learner groups in an account."),
    Operation("list_account_learners", "GET", "/accounts/{accountId}/learners", "List learners in an account."),
    Operation("list_account_phishing_campaigns", "GET", "/accounts/{accountId}/phishing-campaigns", "List phishing campaigns for an account."),
    Operation("list_account_phishing_scenarios", "GET", "/accounts/{accountId}/phishing-scenarios", "List phishing scenarios for an account."),
    Operation("list_account_admin_users", "GET", "/accounts/{accountId}/users", "List account administrators."),
    Operation("list_account_summary_reports_for_account", "GET", "/accounts/{accountId}/account-summary-reports", "List summary reports for an account."),
    Operation("list_account_summary_reports", "GET", "/account-summary-reports", "List account summary reports."),
    Operation("get_account_summary_report", "GET", "/account-summary-reports/{accountSummaryReportId}", "Get an account summary report."),
    Operation("list_assignments", "GET", "/assignments", "List assignments."),
    Operation("create_assignment", "POST", "/assignments", "Create a training assignment.", True),
    Operation("get_assignment", "GET", "/assignments/{assignmentId}", "Get assignment details."),
    Operation("list_assignment_learners", "GET", "/assignments/{assignmentId}/learners", "List learners assigned to an assignment."),
    Operation("get_assignment_learner_activity", "GET", "/assignments/{assignmentId}/learner-activity", "Get learner activity for an assignment."),
    Operation("get_assignment_completion_certificate", "GET", "/assignments/{assignmentId}/completion-certificate", "Get a learner's assignment completion certificate."),
    Operation("list_assignment_enrollment_conditions", "GET", "/assignments/{assignmentId}/enrollment-conditions", "List assignment enrollment conditions."),
    Operation("list_assignment_enrollment_extras", "GET", "/assignments/{assignmentId}/enrollment-extras", "List assignment enrollment extras."),
    Operation("list_departments", "GET", "/departments", "List departments."),
    Operation("get_department", "GET", "/departments/{departmentId}", "Get department details."),
    Operation("list_episodes", "GET", "/episodes", "List training episodes."),
    Operation("get_episode", "GET", "/episodes/{episodeId}", "Get training episode details."),
    Operation("list_groups", "GET", "/groups", "List learner groups."),
    Operation("create_group", "POST", "/groups", "Create a learner group.", True),
    Operation("get_group", "GET", "/groups/{groupId}", "Get learner group details."),
    Operation("list_learners", "GET", "/learners", "List learners."),
    Operation("get_learner", "GET", "/learners/{learnerId}", "Get learner details."),
    Operation("list_phishing_campaigns", "GET", "/phishing-campaigns", "List phishing campaigns."),
    Operation("get_phishing_campaign", "GET", "/phishing-campaigns/{phishingCampaignId}", "Get phishing campaign details."),
    Operation("list_phishing_campaign_attempts", "GET", "/phishing-campaigns/{phishingCampaignId}/attempts", "List phishing attempts for a campaign."),
    Operation("list_phishing_campaign_scenarios", "GET", "/phishing-campaigns/{phishingCampaignId}/campaign-scenarios", "List scenarios attached to a phishing campaign."),
    Operation("get_phishing_campaign_scenario", "GET", "/phishing-campaign-scenarios/{phishingCampaignScenarioId}", "Get a campaign-scenario's details."),
    Operation("list_phishing_campaign_scenario_attempts", "GET", "/phishing-campaign-scenarios/{phishingCampaignScenarioId}/attempts", "List attempts for a campaign-scenario."),
    Operation("get_phishing_campaign_scenario_campaign", "GET", "/phishing-campaign-scenarios/{phishingCampaignScenarioId}/campaign", "Get the campaign related to a campaign-scenario."),
    Operation("get_phishing_campaign_scenario_scenario", "GET", "/phishing-campaign-scenarios/{phishingCampaignScenarioId}/scenario", "Get the phishing scenario related to a campaign-scenario."),
    Operation("report_phishing_attempt", "POST", "/phishing-attempts/actions/report", "Mark a phishing attempt reported using a code or message ID.", True),
    Operation("list_phishing_scenarios", "GET", "/phishing-scenarios", "List phishing scenarios."),
    Operation("get_phishing_scenario", "GET", "/phishing-scenarios/{phishingScenarioId}", "Get phishing scenario details."),
    Operation("list_admin_users", "GET", "/users", "List administrator users."),
    Operation("create_admin_user", "POST", "/users", "Create an administrator user.", True),
    Operation("get_admin_user", "GET", "/users/{userId}", "Get administrator user details."),
    Operation("update_admin_user", "PATCH", "/users/{userId}", "Update an administrator user.", True),
    Operation("delete_admin_user", "DELETE", "/users/{userId}", "Permanently delete an administrator user."),
)


class CurriculaClient:
    """Small standard-library HTTP client so the server has few dependencies."""

    def __init__(self, token: str | None = None, base_url: str | None = None) -> None:
        self.token = token or os.getenv("CURRICULA_ACCESS_TOKEN")
        self.base_url = (base_url or os.getenv("CURRICULA_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.client_id = os.getenv("CURRICULA_CLIENT_ID")
        self.client_secret = os.getenv("CURRICULA_CLIENT_SECRET")
        self.token_url = os.getenv("CURRICULA_TOKEN_URL", DEFAULT_TOKEN_URL)
        self.oauth_scope = os.getenv("CURRICULA_OAUTH_SCOPE", REQUIRED_MANAGEMENT_SCOPES)
        self.token_expires_at = 0.0

    def _access_token(self) -> str:
        if self.token and (not self.client_id or time.monotonic() < self.token_expires_at):
            return self.token
        if not self.client_id or not self.client_secret:
            raise ValueError("Configure CURRICULA_ACCESS_TOKEN or CURRICULA_CLIENT_ID and CURRICULA_CLIENT_SECRET.")
        payload = urlencode({
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.oauth_scope,
        }).encode()
        request = Request(
            self.token_url,
            data=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "axios/1.7.9",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:  # nosec B310 - endpoint is operator-configured
                token_response = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Curricula OAuth returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Unable to reach Curricula OAuth: {exc.reason}") from exc
        token = token_response.get("access_token")
        if not token:
            raise RuntimeError("Curricula OAuth response did not contain an access_token.")
        self.token = token
        self.token_expires_at = time.monotonic() + max(int(token_response.get("expires_in", 300)) - 60, 1)
        return token

    def request(self, operation: Operation, path_params: dict[str, str], query: dict[str, Any], body: dict[str, Any] | None) -> dict[str, Any]:
        token = self._access_token()
        try:
            escaped_params = {key: quote(str(value), safe="") for key, value in path_params.items()}
            path = operation.path.format(**escaped_params)
        except KeyError as exc:
            raise ValueError(f"Missing required path parameter: {exc.args[0]}") from exc
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{urlencode(query, doseq=True)}"
        data = json.dumps(body).encode() if body is not None else None
        headers = {
            "Accept": JSON_API,
            "Authorization": f"Bearer {token}",
            "User-Agent": "axios/1.7.9",
        }
        if data is not None:
            headers["Content-Type"] = JSON_API
        request = Request(url, data=data, headers=headers, method=operation.method)
        try:
            with urlopen(request, timeout=30) as response:  # nosec B310 - endpoint is configurable by the operator
                raw = response.read().decode("utf-8")
                return {"status": response.status, "data": json.loads(raw) if raw else None}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Curricula API returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Unable to reach Curricula API: {exc.reason}") from exc


def create_server(client: CurriculaClient | None = None) -> FastMCP:
    """Create a server and register one MCP tool for every documented operation."""
    api_client = client or CurriculaClient()
    server = FastMCP(
        "Curricula",
        host=os.getenv("MCP_HOST", "0.0.0.0"),
        port=int(os.getenv("MCP_PORT", "8000")),
    )

    def make_tool(operation: Operation):
        async def invoke(
            path_params: dict[str, str] | None = None,
            query: dict[str, Any] | None = None,
            body: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            """Call the corresponding Curricula JSON:API endpoint."""
            if operation.has_body and body is None:
                raise ValueError("This operation requires a JSON:API request body.")
            return await asyncio.to_thread(api_client.request, operation, path_params or {}, query or {}, body)

        invoke.__name__ = operation.name
        invoke.__doc__ = (
            f"{operation.summary} Calls `{operation.method} {operation.path}`. "
            "Put route IDs in path_params and filtering, pagination, sorting, or include values in query. "
            + ("Provide the JSON:API payload in body." if operation.has_body else "")
        )
        return invoke

    for operation in OPERATIONS:
        invoke = make_tool(operation)
        server.tool(name=operation.name, description=invoke.__doc__)(invoke)

    async def move_learner_to_group(learner_id: str, group_id: str) -> dict[str, Any]:
        """Move a learner into a group. Requires the `learners:manage` OAuth scope."""
        payload = {
            "data": {
                "type": "learners",
                "id": learner_id,
                "relationships": {"group": {"data": {"type": "groups", "id": group_id}}},
            }
        }
        operation = Operation("move_learner_to_group", "PATCH", "/learners/{learnerId}", "Move learner to group.", True)
        return await asyncio.to_thread(api_client.request, operation, {"learnerId": learner_id}, {}, payload)

    async def remove_learner_from_group(learner_id: str) -> dict[str, Any]:
        """Remove a learner's group relationship. Requires the `learners:manage` OAuth scope."""
        payload = {
            "data": {
                "type": "learners",
                "id": learner_id,
                "relationships": {"group": {"data": None}},
            }
        }
        operation = Operation("remove_learner_from_group", "PATCH", "/learners/{learnerId}", "Remove learner from group.", True)
        return await asyncio.to_thread(api_client.request, operation, {"learnerId": learner_id}, {}, payload)

    async def add_learner_to_assignment(assignment_id: str, learner_id: str, operator: str = "=") -> dict[str, Any]:
        """Add a learner to an assignment through an enrollment extra. Requires `assignments:manage` and `learners:manage`."""
        if operator not in {"=", "!="}:
            raise ValueError("operator must be '=' or '!='.")
        payload = {
            "data": {
                "type": "assignment-enrollment-extras",
                "attributes": {"operator": operator},
                "relationships": {
                    "assignment": {"data": {"type": "assignments", "id": assignment_id}},
                    "learner": {"data": {"type": "learners", "id": learner_id}},
                },
            }
        }
        operation = Operation("add_learner_to_assignment", "POST", "/assignments/{assignmentId}/enrollment-extras", "Add learner to assignment.", True)
        return await asyncio.to_thread(api_client.request, operation, {"assignmentId": assignment_id}, {}, payload)

    async def add_group_to_assignment(assignment_id: str, group_id: str, operator: str = "=") -> dict[str, Any]:
        """Add a group to an assignment through an enrollment condition. Requires `assignments:manage` and `learners:manage`."""
        if operator not in {"=", "!="}:
            raise ValueError("operator must be '=' or '!='.")
        payload = {
            "data": {
                "type": "assignment-enrollment-conditions",
                "attributes": {"conditionType": "group", "conditionOperator": operator, "conditionId": group_id},
                "relationships": {
                    "assignment": {"data": {"type": "assignments", "id": assignment_id}},
                    "subject": {"data": {"type": "groups", "id": group_id}},
                },
            }
        }
        operation = Operation("add_group_to_assignment", "POST", "/assignments/{assignmentId}/enrollment-conditions", "Add group to assignment.", True)
        return await asyncio.to_thread(api_client.request, operation, {"assignmentId": assignment_id}, {}, payload)

    server.tool(name="move_learner_to_group")(move_learner_to_group)
    server.tool(name="remove_learner_from_group")(remove_learner_from_group)
    server.tool(name="add_learner_to_assignment")(add_learner_to_assignment)
    server.tool(name="add_group_to_assignment")(add_group_to_assignment)
    return server


mcp = create_server()


def main() -> None:
    """Run the MCP server over Kubernetes-reachable streamable HTTP."""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
