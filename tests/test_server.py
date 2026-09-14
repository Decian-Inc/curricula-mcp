from curricula_mcp.server import CurriculaClient, OPERATIONS


def test_every_openapi_operation_is_exposed():
    assert len(OPERATIONS) == 44
    assert len({operation.name for operation in OPERATIONS}) == 44


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
