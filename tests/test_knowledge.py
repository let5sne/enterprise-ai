"""
Tests for the Knowledge module (知识管理).
"""


def test_create_and_list_knowledge_base(client):
    resp = client.post("/api/v1/knowledge/bases", json={"name": "测试知识库", "category": "技术"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "测试知识库"
    assert data["category"] == "技术"

    resp = client.get("/api/v1/knowledge/bases")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_knowledge_base(client):
    kb_id = client.post("/api/v1/knowledge/bases", json={"name": "KB1"}).json()["id"]

    resp = client.get(f"/api/v1/knowledge/bases/{kb_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == kb_id


def test_get_knowledge_base_not_found(client):
    resp = client.get("/api/v1/knowledge/bases/9999")
    assert resp.status_code == 404


def test_update_knowledge_base(client):
    kb_id = client.post("/api/v1/knowledge/bases", json={"name": "Old Name"}).json()["id"]

    resp = client.put(f"/api/v1/knowledge/bases/{kb_id}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


def test_delete_knowledge_base(client):
    kb_id = client.post("/api/v1/knowledge/bases", json={"name": "To Delete"}).json()["id"]

    resp = client.delete(f"/api/v1/knowledge/bases/{kb_id}")
    assert resp.status_code == 204

    resp = client.get(f"/api/v1/knowledge/bases/{kb_id}")
    assert resp.status_code == 404


def test_create_and_list_documents(client):
    kb_id = client.post("/api/v1/knowledge/bases", json={"name": "Doc KB"}).json()["id"]

    doc_payload = {
        "title": "Introduction to AI",
        "content": "Artificial Intelligence is ...",
        "tags": "AI,ML",
    }
    resp = client.post(f"/api/v1/knowledge/bases/{kb_id}/documents", json=doc_payload)
    assert resp.status_code == 201
    doc = resp.json()
    assert doc["title"] == "Introduction to AI"
    assert doc["knowledge_base_id"] == kb_id

    resp = client.get(f"/api/v1/knowledge/bases/{kb_id}/documents")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_document(client):
    kb_id = client.post("/api/v1/knowledge/bases", json={"name": "KB"}).json()["id"]
    doc_id = client.post(
        f"/api/v1/knowledge/bases/{kb_id}/documents",
        json={"title": "Doc", "content": "Content"},
    ).json()["id"]

    resp = client.get(f"/api/v1/knowledge/documents/{doc_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == doc_id


def test_update_document(client):
    kb_id = client.post("/api/v1/knowledge/bases", json={"name": "KB"}).json()["id"]
    doc_id = client.post(
        f"/api/v1/knowledge/bases/{kb_id}/documents",
        json={"title": "Old", "content": "old content"},
    ).json()["id"]

    resp = client.put(
        f"/api/v1/knowledge/documents/{doc_id}", json={"title": "New", "content": "new content"}
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New"


def test_delete_document(client):
    kb_id = client.post("/api/v1/knowledge/bases", json={"name": "KB"}).json()["id"]
    doc_id = client.post(
        f"/api/v1/knowledge/bases/{kb_id}/documents",
        json={"title": "Del", "content": "bye"},
    ).json()["id"]

    assert client.delete(f"/api/v1/knowledge/documents/{doc_id}").status_code == 204
    assert client.get(f"/api/v1/knowledge/documents/{doc_id}").status_code == 404


def test_search_documents(client):
    kb_id = client.post("/api/v1/knowledge/bases", json={"name": "KB"}).json()["id"]
    client.post(
        f"/api/v1/knowledge/bases/{kb_id}/documents",
        json={"title": "机器学习入门", "content": "监督学习与无监督学习的基本概念"},
    )
    client.post(
        f"/api/v1/knowledge/bases/{kb_id}/documents",
        json={"title": "深度学习", "content": "神经网络"},
    )

    resp = client.get("/api/v1/knowledge/search?q=学习")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = client.get("/api/v1/knowledge/search?q=神经网络")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
