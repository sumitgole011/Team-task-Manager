"""Additional access-control tests using the isolated SQLite setup in test_signup_roles."""
import unittest

from app import app, db, User, Project
from werkzeug.security import generate_password_hash


class AccessControlTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        with app.app_context():
            db.drop_all()
            db.create_all()
            db.session.add_all([
                User(name="Alice", email="alice@example.test",
                     password_hash=generate_password_hash("alice-password"), role="Member"),
                User(name="Bob", email="bob@example.test",
                     password_hash=generate_password_hash("bob-password"), role="Member"),
            ])
            db.session.commit()
            alice = User.query.filter_by(email="alice@example.test").one()
            db.session.add(Project(name="Private project", owner_id=alice.id))
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.session.remove()
            db.engine.dispose()

    def login(self, email, password):
        return self.client.post("/api/auth/login", json={"email": email, "password": password})

    def test_anonymous_api_access_is_denied(self):
        for path in ["/api/auth/me", "/api/users", "/api/projects", "/api/tasks"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 401)

    def test_member_cannot_list_all_users(self):
        self.assertEqual(self.login("bob@example.test", "bob-password").status_code, 200)
        self.assertEqual(self.client.get("/api/users").status_code, 403)

    def test_member_cannot_access_another_members_project(self):
        self.assertEqual(self.login("bob@example.test", "bob-password").status_code, 200)
        with app.app_context():
            project_id = Project.query.filter_by(name="Private project").one().id
        self.assertEqual(self.client.get(f"/api/projects/{project_id}").status_code, 403)

    def test_owner_can_access_own_project(self):
        self.assertEqual(self.login("alice@example.test", "alice-password").status_code, 200)
        with app.app_context():
            project_id = Project.query.filter_by(name="Private project").one().id
        self.assertEqual(self.client.get(f"/api/projects/{project_id}").status_code, 200)


    def test_owner_can_update_project(self):
        self.assertEqual(self.login("alice@example.test", "alice-password").status_code, 200)
        with app.app_context():
            project_id = Project.query.filter_by(name="Private project").one().id
        response = self.client.patch(f"/api/projects/{project_id}", json={"name": "Updated project"})
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            self.assertEqual(db.session.get(Project, project_id).name, "Updated project")

    def test_member_can_read_but_cannot_edit_shared_project(self):
        from app import ProjectMember
        with app.app_context():
            project = Project.query.filter_by(name="Private project").one()
            bob = User.query.filter_by(email="bob@example.test").one()
            project_id = project.id
            db.session.add(ProjectMember(project_id=project_id, user_id=bob.id))
            db.session.commit()
        self.assertEqual(self.login("bob@example.test", "bob-password").status_code, 200)
        self.assertEqual(self.client.get(f"/api/projects/{project_id}").status_code, 200)
        response = self.client.patch(f"/api/projects/{project_id}", json={"name": "Unauthorized edit"})
        self.assertEqual(response.status_code, 403)
        with app.app_context():
            self.assertEqual(db.session.get(Project, project_id).name, "Private project")


if __name__ == "__main__":
    unittest.main()
