from abc import ABC

class AuthBase(ABC):
    def create_user(self, user_data: dict) -> bool:
        pass
    def get_user(self, user_id: str) -> dict:
        pass
    def update_user(self, user_id: str, update_data: dict) -> bool:
        pass
    def delete_user(self, user_id: str) -> bool:
        pass

    