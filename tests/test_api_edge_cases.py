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


def test_async_job_endpoints():
    import pandas as pd

    df = pd.DataFrame({"num1": [10.0, 20.0, 30.0], "cat1": ["a", "b", "c"]})
    df_json = dataframe_to_split_json(df)

    # Enqueue async job
    resp = client.post(
        "/api/jobs/execute", data={"skill_id": "profile_dataset", "df_json": df_json}
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "pending"
    job_id = data["job_id"]

    # Check status
    res_status = client.get(f"/api/jobs/{job_id}")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] in ["pending", "running", "completed"]

    # Invalid job id
    res_invalid = client.get("/api/jobs/invalid-uuid-999")
    assert res_invalid.status_code == 404


def test_csv_formula_sanitization():
    import pandas as pd

    from src.adapters.fs.file_io import FileSystemAdapter

    df_unsafe = pd.DataFrame({"formula": ["=SUM(A1:A10)", "+1+1", "-2+2", "@cmd", "safe_text"]})

    file_path, err = FileSystemAdapter.export_file(df_unsafe, "CSV")
    assert err == ""
    assert file_path is not None

    df_read = pd.read_csv(file_path)
    assert df_read["formula"].iloc[0] == "'=SUM(A1:A10)"
    assert df_read["formula"].iloc[1] == "'+1+1"
    assert df_read["formula"].iloc[2] == "'-2+2"
    assert df_read["formula"].iloc[3] == "'@cmd"
    assert df_read["formula"].iloc[4] == "safe_text"
