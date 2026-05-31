# tests/test_search.py
import pytest
from core.search import SearchAPI


class TestSearch:

    def test_search_history(self, auth_client):
        search_api = SearchAPI(auth_client)
        response = search_api.history()
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        # Правильный путь: data -> data -> history
        assert isinstance(data.get("data", {}).get("history"), list)

    def test_search_suggest_success(self, auth_client):
        search_api = SearchAPI(auth_client)
        response = search_api.suggest("evos", limit=5)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "suggestions" in data["data"]
        assert any(s["text"].lower() == "evos" for s in data["data"]["suggestions"])

    def test_search_suggest_empty(self, auth_client):
        search_api = SearchAPI(auth_client)
        response = search_api.suggest("", limit=5)
        assert response.status_code in (400, 422)

    def test_search_results_success(self, auth_client):
        search_api = SearchAPI(auth_client)
        response = search_api.search("evos", page=1, per_page=10,
                                     lat=37.4219983, lng=-122.084)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert any("name" in item and "EVOS" in item["name"] for item in data["data"])

    def test_search_results_no_query(self, auth_client):  # ВАЖНО: используй auth_client!
        search_api = SearchAPI(auth_client)
        # Если ты вызываешь поиск без параметров, проверь, что путь верный
        response = search_api.search("", page=1, per_page=10)

        # Если 302 всё еще здесь, проверь URL в поиске (может, он требует авторизации?)
        assert response.status_code in (400, 422)
