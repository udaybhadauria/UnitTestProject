import unittest
from app import app  # Import your Flask app here

class TestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up once before any tests are run"""
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_get_users(self):
        response = self.client.get("/users")
        self.assertEqual(response.status_code, 200)

    def test_create_user(self):
        response = self.client.post("/user", json={"username": "test", "name": "Test User", "age": 99})
        self.assertEqual(response.status_code, 201)

    def test_update_user(self):
        self.client.post("/user", json={"username": "updateme", "name": "Update Me", "age": 30})
        response = self.client.put("/user/updateme", json={"age": 35})
        self.assertEqual(response.status_code, 200)

    def test_delete_user(self):
        self.client.post("/user", json={"username": "deleteme", "name": "Delete Me", "age": 40})
        response = self.client.delete("/user/deleteme")
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
