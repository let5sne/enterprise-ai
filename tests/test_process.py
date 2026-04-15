"""
Tests for the Process module (流程管理).
"""


def test_create_and_list_workflows(client):
    payload = {
        "name": "数据处理流程",
        "description": "自动化数据清洗与分析",
        "definition": '{"steps": ["extract", "transform", "load"]}',
    }
    resp = client.post("/api/v1/process/workflows", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "数据处理流程"
    assert data["status"] == "active"
    assert data["version"] == 1

    resp = client.get("/api/v1/process/workflows")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_workflow(client):
    wf_id = client.post(
        "/api/v1/process/workflows", json={"name": "WF1"}
    ).json()["id"]

    resp = client.get(f"/api/v1/process/workflows/{wf_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == wf_id


def test_get_workflow_not_found(client):
    assert client.get("/api/v1/process/workflows/9999").status_code == 404


def test_update_workflow_increments_version(client):
    wf_id = client.post(
        "/api/v1/process/workflows",
        json={"name": "WF", "definition": "v1"},
    ).json()["id"]

    resp = client.put(
        f"/api/v1/process/workflows/{wf_id}",
        json={"definition": "v2"},
    )
    assert resp.status_code == 200
    assert resp.json()["version"] == 2


def test_update_workflow_status(client):
    wf_id = client.post(
        "/api/v1/process/workflows", json={"name": "WF"}
    ).json()["id"]

    resp = client.put(
        f"/api/v1/process/workflows/{wf_id}", json={"status": "inactive"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "inactive"


def test_delete_workflow(client):
    wf_id = client.post(
        "/api/v1/process/workflows", json={"name": "Del WF"}
    ).json()["id"]

    assert client.delete(f"/api/v1/process/workflows/{wf_id}").status_code == 204
    assert client.get(f"/api/v1/process/workflows/{wf_id}").status_code == 404


def test_create_and_list_instances(client):
    wf_id = client.post(
        "/api/v1/process/workflows", json={"name": "WF"}
    ).json()["id"]

    resp = client.post(
        f"/api/v1/process/workflows/{wf_id}/instances",
        json={"input_data": '{"user_id": 42}'},
    )
    assert resp.status_code == 201
    inst = resp.json()
    assert inst["workflow_id"] == wf_id
    assert inst["status"] == "running"

    resp = client.get(f"/api/v1/process/workflows/{wf_id}/instances")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_instance(client):
    wf_id = client.post(
        "/api/v1/process/workflows", json={"name": "WF"}
    ).json()["id"]
    inst_id = client.post(
        f"/api/v1/process/workflows/{wf_id}/instances", json={}
    ).json()["id"]

    resp = client.get(f"/api/v1/process/instances/{inst_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == inst_id


def test_finish_instance(client):
    wf_id = client.post(
        "/api/v1/process/workflows", json={"name": "WF"}
    ).json()["id"]
    inst_id = client.post(
        f"/api/v1/process/workflows/{wf_id}/instances", json={}
    ).json()["id"]

    resp = client.put(
        f"/api/v1/process/instances/{inst_id}/finish",
        json={"status": "completed", "output_data": "success"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_create_and_list_tasks(client):
    wf_id = client.post(
        "/api/v1/process/workflows", json={"name": "WF"}
    ).json()["id"]
    inst_id = client.post(
        f"/api/v1/process/workflows/{wf_id}/instances", json={}
    ).json()["id"]

    for i, (name, ttype) in enumerate([("提取", "extract"), ("转换", "transform"), ("加载", "load")]):
        client.post(
            f"/api/v1/process/instances/{inst_id}/tasks",
            json={"task_name": name, "task_type": ttype, "sequence": i},
        )

    resp = client.get(f"/api/v1/process/instances/{inst_id}/tasks")
    assert resp.status_code == 200
    tasks = resp.json()
    assert len(tasks) == 3
    # Tasks should be ordered by sequence
    assert tasks[0]["task_name"] == "提取"
    assert tasks[2]["task_name"] == "加载"


def test_update_task_status(client):
    wf_id = client.post(
        "/api/v1/process/workflows", json={"name": "WF"}
    ).json()["id"]
    inst_id = client.post(
        f"/api/v1/process/workflows/{wf_id}/instances", json={}
    ).json()["id"]
    task_id = client.post(
        f"/api/v1/process/instances/{inst_id}/tasks",
        json={"task_name": "处理", "task_type": "process"},
    ).json()["id"]

    resp = client.put(
        f"/api/v1/process/tasks/{task_id}/status",
        json={"status": "completed", "output_data": "done"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"
    assert resp.json()["output_data"] == "done"
