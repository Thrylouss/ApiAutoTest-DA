# core/search.py
class SearchAPI:
    def __init__(self, client):
        self.client = client

    def history(self):
        """История поиска (GET, требует токен)"""
        return self.client.get("/api/v1/search/history")

    def suggest(self, q: str, limit: int = 5):
        """Подсказки поиска"""
        return self.client.get("/api/v1/search/suggest", params={
            "q": q,
            "limit": limit
        })

    def search(self, q: str, page: int = 1, per_page: int = 10,
               lat: float = None, lng: float = None):
        """Основной поиск"""
        params = {
            "q": q,
            "page": page,
            "per_page": per_page
        }
        if lat and lng:
            params["lat"] = lat
            params["lng"] = lng

        return self.client.get("/api/v1/search", params=params)
