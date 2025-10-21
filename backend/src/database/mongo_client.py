from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from src.database.base import AuthBase
from dotenv import load_dotenv
import os

load_dotenv()

uri = os.getenv("MONGO_DB_URI")


class MongoDBClient(AuthBase):
    def __init__(self):
        super().__init__()
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        self.db = self.client.get_database("edna_database")  # Replace with your database name

    def ping(self) -> None:
        try:
            self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)

    # User authentication methods
    def create_user(self, user_data: dict) -> bool:
        users_collection = self.db.get_collection("users")
        result = users_collection.insert_one(user_data)
        return result.acknowledged

    def get_user(self, user_id: str) -> dict:
        users_collection = self.db.get_collection("users")
        user = users_collection.find_one({"user_id": user_id})
        return user

    def update_user(self, user_id: str, update_data: dict) -> bool:
        users_collection = self.db.get_collection("users")
        result = users_collection.update_one({"user_id": user_id}, {"$set": update_data})
        return result.modified_count > 0

    def delete_user(self, user_id: str) -> bool:
        users_collection = self.db.get_collection("users")
        result = users_collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0


    def close(self):
        self.client.close()



client = MongoDBClient()

if __name__ == "__main__":
    client.ping()
    client.close()