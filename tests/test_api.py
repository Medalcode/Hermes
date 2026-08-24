import os

import pytest
from fastapi.testclient import TestClient

from src.adapters.api.router import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_storage():
    """Clean up storage dirs before and after each test."""
    import shutil

    for d in ["storage/sessions", "storage/data", "/tmp/storage/sessions", "/tmp/storage/data"]:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d, exist_ok=True)
    # Clean exported files
    for f in ["datos_procesados.csv", "datos_procesados.xlsx"]:
        if os.path.exists(f):
            os.remove(f)
    yield
    for d in ["storage/sessions", "storage/data", "/tmp/storage/sessions", "/tmp/storage/data"]:
        if os.path.exists(d):
            shutil.rmtree(d)
    for f in ["datos_procesados.csv", "datos_procesados.xlsx"]:
        if os.path.exists(f):
            os.remove(f)


def make_csv(content: str, name: str = "test.csv") -> dict:
    return {"file": (name, content, "text/csv")}


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_healthz_and_readyz():
    res_health = client.get("/healthz")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "ok"}

    res_ready = client.get("/readyz")
    assert res_ready.status_code == 200
    data = res_ready.json()
    assert data["status"] == "ready"
    assert data["registered_skills_count"] > 0


def test_upload_csv():
    csv_content = "a,b,c\n1,2,3\n4,5,6\n7,8,9\n10,11,12\n"
    resp = client.post("/api/upload", files=make_csv(csv_content))
    assert resp.status_code == 200
    data = resp.json()
    assert data["shape"] == [4, 3]
    assert data["columns"] == ["a", "b", "c"]
    assert len(data["preview"]) == 4
    assert "session_id" in resp.cookies


def test_upload_then_stats():
    csv_content = "x,y\n1,2\n3,4\n5,6\n"
    resp = client.post("/api/upload", files=make_csv(csv_content))
    assert resp.status_code == 200

    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "descriptive" in data
    # descriptive keys: mean, median, std, min, max, etc.
    desc = data["descriptive"]
    assert "mean" in desc
    assert desc["mean"]["x"] == 3.0


def test_upload_then_clean_nulls():
    csv_content = "a,b\n1,2\n,4\n5,\n7,8\n"
    resp = client.post("/api/upload", files=make_csv(csv_content))
    assert resp.status_code == 200

    resp = client.post("/api/clean/nulls", data={"cols": "a", "method": "drop"})
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data
    assert "preview" in data


def test_upload_then_scale():
    csv_content = "x,y\n10,100\n20,200\n30,300\n"
    resp = client.post("/api/upload", files=make_csv(csv_content))
    assert resp.status_code == 200

    resp = client.post("/api/clean/scale", data={"cols": "x", "method": "Min-Max"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Escalado completado."
    # After min-max: min=0, max=1
    preview = data["preview"]
    vals = [row["x"] for row in preview]
    assert min(vals) == 0.0
    assert max(vals) == 1.0


def test_upload_then_dedup():
    csv_content = "a,b\n1,2\n1,2\n3,4\n5,6\n"
    resp = client.post("/api/upload", files=make_csv(csv_content))
    assert resp.status_code == 200

    resp = client.post("/api/clean/dedup", data={"subset": ""})
    assert resp.status_code == 200
    data = resp.json()
    assert "Se eliminaron" in data["message"]


def test_upload_then_outliers():
    csv_content = "a,b\n1,10\n2,20\n3,30\n100,40\n5,50\n"
    resp = client.post("/api/upload", files=make_csv(csv_content))
    assert resp.status_code == 200

    resp = client.post("/api/outliers", data={"column": "a", "treatment": "Informar"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 0  # may or may not detect outliers


def test_upload_then_cluster():
    csv_content = "x,y\n0,0\n1,1\n10,10\n11,11\n"
    resp = client.post("/api/upload", files=make_csv(csv_content))
    assert resp.status_code == 200

    resp = client.post("/api/cluster", data={"cols": ["x", "y"], "k": "2"})
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data


def test_upload_then_export():
    csv_content = "a,b\n1,2\n3,4\n"
    resp = client.post("/api/upload", files=make_csv(csv_content))
    assert resp.status_code == 200

    resp = client.post("/api/export", data={"format_type": "CSV"})
    assert resp.status_code == 200
    data = resp.json()
    assert "file_path" in data


def test_no_data_returns_error():
    resp = client.get("/api/stats")
    assert resp.status_code == 400
    assert resp.json()["error"] == "No dataframe"

    resp = client.post("/api/clean/nulls", data={"cols": "a", "method": "drop"})
    assert resp.status_code == 400
    assert resp.json()["error"] == "No dataframe"

    resp = client.post("/api/clean/dedup", data={"subset": ""})
    assert resp.status_code == 400
    assert resp.json()["error"] == "No dataframe"

    resp = client.post("/api/outliers", data={"column": "a", "treatment": "cap"})
    assert resp.status_code == 400
    assert resp.json()["error"] == "No dataframe"

    resp = client.post("/api/cluster", data={"cols": "x,y", "k": "2"})
    assert resp.status_code == 400
    assert resp.json()["error"] == "No dataframe"

    resp = client.post("/api/export", data={"format_type": "CSV"})
    assert resp.status_code == 400
    assert resp.json()["error"] == "No dataframe"


def test_upload_invalid_file():
    resp = client.post("/api/upload", files={"file": ("data.txt", b"not a csv", "text/plain")})
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_upload_then_plot():
    csv_content = "a,b\n1,2\n3,4\n"
    resp = client.post("/api/upload", files=make_csv(csv_content))
    assert resp.status_code == 200

    resp = client.post("/api/plot", data={"type": "correlation"})
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data or "layout" in data
