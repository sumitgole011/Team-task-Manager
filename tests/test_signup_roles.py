"""Regression tests for public registration privileges.

Run: python -m unittest discover -s tests -v
"""
import unittest

from test_support import app, db, User


class SignupRoleTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        app.config["TESTING"] = True
        with app.app_context():
            db.drop_all()
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.session.remove()
            db.engine.dispose()

    def test_api_signup_cannot_grant_admin(self):
        response = self.client.post("/api/auth/signup", json={
            "name": "Example User",
            "email": "example@example.test",
            "password": "safe-password-123",
            "role": "Admin",
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["role"], "Member")
        with app.app_context():
            self.assertEqual(User.query.filter_by(email="example@example.test").one().role, "Member")

    def test_form_signup_cannot_grant_admin(self):
        response = self.client.post("/signup", data={
            "name": "Form User",
            "email": "form@example.test",
            "password": "safe-password-123",
            "role": "Admin",
        })
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            self.assertEqual(User.query.filter_by(email="form@example.test").one().role, "Member")

    def test_public_signup_page_does_not_offer_admin_role(self):
        response = self.client.get("/signup")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'<option>Admin</option>', response.data)


if __name__ == "__main__":
    unittest.main()

