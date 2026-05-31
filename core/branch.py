# core/branch.py

class BranchAPI:
    def __init__(self, client):
        self.client = client

    def get_favorites(self):
        # Метод НЕ принимает token
        return self.client.get("/api/v1/branches/favorites")