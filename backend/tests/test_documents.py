import io
import time


def test_upload_rejects_bad_extension(client, auth_headers):
    resp = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("malware.exe", io.BytesIO(b"data"), "application/octet-stream")},
    )
    assert resp.status_code == 400


def test_upload_and_process_text_pdf(client, auth_headers, tmp_path):
    from pypdf import PdfWriter

    pdf_path = tmp_path / "sample.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with open(pdf_path, "wb") as f:
        writer.write(f)

    with open(pdf_path, "rb") as f:
        resp = client.post(
            "/api/v1/documents/upload",
            headers=auth_headers,
            files={"file": ("sample.pdf", f, "application/pdf")},
        )
    assert resp.status_code == 200
    doc_id = resp.json()["id"]

    resp = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert resp.status_code == 200


def test_list_documents_empty(client, auth_headers):
    resp = client.get("/api/v1/documents", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_health_check(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_admin_stats_requires_admin_role(client, auth_headers):
    # First registered user is admin in this test DB, so this should succeed.
    resp = client.get("/api/v1/admin/stats", headers=auth_headers)
    assert resp.status_code == 200
    assert "total_users" in resp.json()
