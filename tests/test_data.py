"""
Tests for the Data module (数据管理).
"""


def test_create_and_list_data_sources(client):
    payload = {"name": "MySQL生产库", "source_type": "mysql", "description": "生产数据库"}
    resp = client.post("/api/v1/data/sources", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "MySQL生产库"
    assert data["source_type"] == "mysql"

    resp = client.get("/api/v1/data/sources")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_data_source(client):
    src_id = client.post(
        "/api/v1/data/sources", json={"name": "S1", "source_type": "postgres"}
    ).json()["id"]

    resp = client.get(f"/api/v1/data/sources/{src_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == src_id


def test_get_data_source_not_found(client):
    assert client.get("/api/v1/data/sources/9999").status_code == 404


def test_update_data_source(client):
    src_id = client.post(
        "/api/v1/data/sources", json={"name": "Old", "source_type": "csv"}
    ).json()["id"]

    resp = client.put(f"/api/v1/data/sources/{src_id}", json={"name": "New", "status": "inactive"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"
    assert resp.json()["status"] == "inactive"


def test_delete_data_source(client):
    src_id = client.post(
        "/api/v1/data/sources", json={"name": "Del", "source_type": "json"}
    ).json()["id"]

    assert client.delete(f"/api/v1/data/sources/{src_id}").status_code == 204
    assert client.get(f"/api/v1/data/sources/{src_id}").status_code == 404


def test_create_and_list_datasets(client):
    src_id = client.post(
        "/api/v1/data/sources", json={"name": "SRC", "source_type": "mysql"}
    ).json()["id"]

    resp = client.post(
        f"/api/v1/data/sources/{src_id}/datasets",
        json={"name": "用户数据集", "description": "包含用户行为数据"},
    )
    assert resp.status_code == 201
    ds = resp.json()
    assert ds["name"] == "用户数据集"
    assert ds["data_source_id"] == src_id

    resp = client.get(f"/api/v1/data/sources/{src_id}/datasets")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_dataset(client):
    src_id = client.post(
        "/api/v1/data/sources", json={"name": "SRC", "source_type": "mysql"}
    ).json()["id"]
    ds_id = client.post(
        f"/api/v1/data/sources/{src_id}/datasets", json={"name": "DS"}
    ).json()["id"]

    resp = client.get(f"/api/v1/data/datasets/{ds_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == ds_id


def test_delete_dataset(client):
    src_id = client.post(
        "/api/v1/data/sources", json={"name": "SRC", "source_type": "mysql"}
    ).json()["id"]
    ds_id = client.post(
        f"/api/v1/data/sources/{src_id}/datasets", json={"name": "DS"}
    ).json()["id"]

    assert client.delete(f"/api/v1/data/datasets/{ds_id}").status_code == 204
    assert client.get(f"/api/v1/data/datasets/{ds_id}").status_code == 404


def test_create_and_list_jobs(client):
    src_id = client.post(
        "/api/v1/data/sources", json={"name": "SRC", "source_type": "mysql"}
    ).json()["id"]
    ds_id = client.post(
        f"/api/v1/data/sources/{src_id}/datasets", json={"name": "DS"}
    ).json()["id"]

    resp = client.post(f"/api/v1/data/datasets/{ds_id}/jobs", json={"job_type": "import"})
    assert resp.status_code == 201
    job = resp.json()
    assert job["job_type"] == "import"
    assert job["status"] == "pending"

    resp = client.get(f"/api/v1/data/datasets/{ds_id}/jobs")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_job_status(client):
    src_id = client.post(
        "/api/v1/data/sources", json={"name": "SRC", "source_type": "mysql"}
    ).json()["id"]
    ds_id = client.post(
        f"/api/v1/data/sources/{src_id}/datasets", json={"name": "DS"}
    ).json()["id"]
    job_id = client.post(
        f"/api/v1/data/datasets/{ds_id}/jobs", json={"job_type": "export"}
    ).json()["id"]

    resp = client.put(
        f"/api/v1/data/jobs/{job_id}/status",
        json={"status": "completed", "result": "exported 1000 rows"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"
    assert resp.json()["result"] == "exported 1000 rows"
