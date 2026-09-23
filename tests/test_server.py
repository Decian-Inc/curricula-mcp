from urllib.parse import parse_qs

from curricula_mcp.server import CurriculaClient, OPERATIONS, REQUIRED_MANAGEMENT_SCOPES


def test_every_openapi_operation_is_exposed():
    assert len(OPERATIONS) == 46
    assert len({operation.name for operation in OPERATIONS}) == 46


def test_client_builds_json_api_request(monkeypatch):
    captured = {}

    class Response:
        status = 200
        def read(self): return b'{"data": []}'
        def __enter__(self): return self
        def __exit__(self, *args): return False

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.method
        captured["auth"] = request.get_header("Authorization")
        return Response()

    monkeypatch.setattr("curricula_mcp.server.urlopen", fake_urlopen)
    response = CurriculaClient("token", "https://example.test/api/v1").request(
        OPERATIONS[1], {"accountId": "A 1"}, {"page": 2}, None
    )
    assert response == {"status": 200, "data": {"data": []}}
    assert captured == {"url": "https://example.test/api/v1/accounts/A%201?page=2", "method": "GET", "auth": "Bearer token"}


def test_client_credentials_request_management_scopes(monkeypatch):
    captured = {}

    class Response:
        status = 200
        def read(self): return b'{"access_token":"issued-token","expires_in":3600}'
        def __enter__(self): return self
        def __exit__(self, *args): return False

    def fake_urlopen(request, timeout):
        captured["body"] = request.data.decode()
        return Response()

    monkeypatch.setenv("CURRICULA_CLIENT_ID", "client-id")
    monkeypatch.setenv("CURRICULA_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr("curricula_mcp.server.urlopen", fake_urlopen)
    assert CurriculaClient()._access_token() == "issued-token"
    assert parse_qs(captured["body"])["scope"] == [REQUIRED_MANAGEMENT_SCOPES]
