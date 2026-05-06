"""
Tests cho URL Shortener
Chạy: docker compose run app pytest -v
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Mock DB và Redis trước khi import app
import sys
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['redis'] = MagicMock()

from app.main import app

client = TestClient(app)


def test_home_page():
    """Trang chủ phải trả về HTML"""
    res = client.get("/")
    assert res.status_code == 200
    assert "URL Shortener" in res.text


def test_health_endpoint_structure():
    """Health endpoint phải có đúng format"""
    # Chỉ kiểm tra endpoint tồn tại (DB mock sẽ pass)
    res = client.get("/health")
    assert res.status_code in [200, 503]


def test_shorten_invalid_url():
    """URL không có http:// phải bị từ chối"""
    with patch("app.routes.get_db"), patch("app.routes.get_redis"):
        res = client.post("/shorten", json={"url": "google.com"})
    assert res.status_code == 400
    assert "http" in res.json()["detail"].lower()


def test_generate_code_length():
    """Short code phải đúng 6 ký tự"""
    from app.utils import generate_code
    code = generate_code()
    assert len(code) == 6


def test_generate_code_unique():
    """Các code sinh ra phải khác nhau"""
    from app.utils import generate_code
    codes = {generate_code() for _ in range(100)}
    assert len(codes) > 90  # ít nhất 90% unique


def test_metrics_endpoint():
    """Prometheus metrics endpoint phải hoạt động"""
    res = client.get("/metrics")
    assert res.status_code == 200
