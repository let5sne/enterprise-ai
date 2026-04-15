"""
Tests for the Content module (内容管理).
"""


def test_create_and_list_templates(client):
    payload = {
        "name": "文章模板",
        "template_type": "article",
        "prompt_template": "请根据以下主题生成一篇文章：{topic}",
        "variables": "topic",
    }
    resp = client.post("/api/v1/content/templates", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "文章模板"
    assert data["template_type"] == "article"

    resp = client.get("/api/v1/content/templates")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_template(client):
    tmpl_id = client.post(
        "/api/v1/content/templates",
        json={"name": "T", "template_type": "report", "prompt_template": "Report: {title}"},
    ).json()["id"]

    resp = client.get(f"/api/v1/content/templates/{tmpl_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == tmpl_id


def test_get_template_not_found(client):
    assert client.get("/api/v1/content/templates/9999").status_code == 404


def test_update_template(client):
    tmpl_id = client.post(
        "/api/v1/content/templates",
        json={"name": "Old", "template_type": "email", "prompt_template": "Old prompt"},
    ).json()["id"]

    resp = client.put(
        f"/api/v1/content/templates/{tmpl_id}",
        json={"name": "New", "prompt_template": "New prompt"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"
    assert resp.json()["prompt_template"] == "New prompt"


def test_delete_template(client):
    tmpl_id = client.post(
        "/api/v1/content/templates",
        json={"name": "Del", "template_type": "sms", "prompt_template": "prompt"},
    ).json()["id"]

    assert client.delete(f"/api/v1/content/templates/{tmpl_id}").status_code == 204
    assert client.get(f"/api/v1/content/templates/{tmpl_id}").status_code == 404


def test_create_and_list_contents(client):
    payload = {
        "title": "企业AI白皮书",
        "body": "本白皮书介绍企业AI的最佳实践...",
        "content_type": "whitepaper",
        "author": "张三",
        "tags": "AI,企业",
    }
    resp = client.post("/api/v1/content/items", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "企业AI白皮书"
    assert data["status"] == "draft"

    resp = client.get("/api/v1/content/items")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_content(client):
    cid = client.post(
        "/api/v1/content/items",
        json={"title": "C", "body": "body", "content_type": "article"},
    ).json()["id"]

    resp = client.get(f"/api/v1/content/items/{cid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == cid


def test_update_content(client):
    cid = client.post(
        "/api/v1/content/items",
        json={"title": "Old", "body": "old body", "content_type": "blog"},
    ).json()["id"]

    resp = client.put(
        f"/api/v1/content/items/{cid}", json={"title": "New", "body": "new body"}
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New"


def test_delete_content(client):
    cid = client.post(
        "/api/v1/content/items",
        json={"title": "Del", "body": "bye", "content_type": "note"},
    ).json()["id"]

    assert client.delete(f"/api/v1/content/items/{cid}").status_code == 204
    assert client.get(f"/api/v1/content/items/{cid}").status_code == 404


def test_publish_content(client):
    cid = client.post(
        "/api/v1/content/items",
        json={"title": "Pub", "body": "publish me", "content_type": "news"},
    ).json()["id"]

    resp = client.post(f"/api/v1/content/items/{cid}/publish")
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"


def test_content_with_template(client):
    tmpl_id = client.post(
        "/api/v1/content/templates",
        json={"name": "Blog Template", "template_type": "blog", "prompt_template": "{intro}"},
    ).json()["id"]

    resp = client.post(
        "/api/v1/content/items",
        json={
            "title": "Blog Post",
            "body": "content here",
            "content_type": "blog",
            "template_id": tmpl_id,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["template_id"] == tmpl_id
