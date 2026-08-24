from fastapi.testclient import TestClient

from src.adapters.api.dataframe_json import dataframe_to_split_json
from src.adapters.api.router import app

client = TestClient(app)


def test_api_key_auth_enabled(monkeypatch):
    monkeypatch.setenv("MYNA_API_KEY", "secret-key-123")

    # Missing header -> 401
    resp = client.get("/api/stats")
    assert resp.status_code == 401

    # Invalid header -> 401
    resp = client.get("/api/stats", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 401

    # Valid X-API-Key -> Proceeds
    resp = client.get("/api/stats", headers={"X-API-Key": "secret-key-123"})
    # Status code 400 because session has no dataframe, but passed auth!
    assert resp.status_code == 400
    assert resp.json()["error"] == "No dataframe"

    # Valid Bearer token
    resp = client.get("/api/stats", headers={"Authorization": "Bearer secret-key-123"})
    assert resp.status_code == 400


def test_vercel_stateless_mode(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    import pandas as pd

    df = pd.DataFrame({"a": [1, 2, 3], "b": [10, 20, 30]})
    df_json = dataframe_to_split_json(df)

    # Clean nulls in vercel mode passing df_json
    resp = client.post(
        "/api/clean/nulls", data={"cols": ["a"], "method": "drop", "df_json": df_json}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "df_json" in data

    # Scale in vercel mode
    resp = client.post(
        "/api/clean/scale", data={"cols": ["a"], "method": "Min-Max", "df_json": df_json}
    )
    assert resp.status_code == 200

    # Auto analyze in vercel mode
    resp = client.post("/api/auto-analyze", data={"df_json": df_json})
    assert resp.status_code == 200
    assert "report" in resp.json()

    # Missing df_json in Vercel mode -> 400
    resp = client.post("/api/clean/nulls", data={"cols": ["a"], "method": "drop"})
    assert resp.status_code == 400
    assert "Session dataframe payload is required" in resp.json()["error"]
