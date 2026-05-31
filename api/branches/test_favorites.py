import pytest
from core.branch import BranchAPI


class TestBranchFavorites:

    def test_get_favorites_list(self, auth_client):
        """Позитивный тест: получение списка избранного"""
        branch_api = BranchAPI(auth_client)
        response = branch_api.get_favorites()

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

        # Если в избранном есть товары, проверяем структуру первого элемента
        if len(data["data"]) > 0:
            item = data["data"][0]
            assert "branch" in item
            assert item["branch"]["is_favorite"] is True

    def test_favorites_pagination(self, auth_client):
        """Проверка пагинации (если поддерживается)"""
        branch_api = BranchAPI(auth_client)
        response = branch_api.get_favorites()  # Можно добавить params={"page": 1}
        data = response.json()
        assert "meta" in data
        assert "current_page" in data["meta"]

    def test_favorites_unauthorized(self, guest_client):
        """Проверка доступа к избранному неавторизованным пользователем"""
        branch_api = BranchAPI(guest_client)
        response = branch_api.get_favorites()
        assert response.status_code == 401