"""Additional access-control tests using the isolated SQLite setup in test_signup_roles."""
import unittest

from test_support import app, db, User
from app import Project, ProjectMember
from sqlalchemy import event
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

    def test_project_task_and_membership_ids_require_valid_integers(self):
        self.assertEqual(self.login("alice@example.test", "alice-password").status_code, 200)
        with app.app_context():
            project_id = Project.query.filter_by(name="Private project").one().id
            member_id = User.query.filter_by(email="bob@example.test").one().id
        members = f"/api/projects/{project_id}/members"
        self.assertEqual(self.client.post(members, json={"user_id": str(member_id)}).status_code, 200)
        task_payload = {"title": "Task", "project_id": str(project_id)}
        task = self.client.post("/api/tasks", json={**task_payload, "assignee_id": str(member_id)})
        self.assertEqual(task.status_code, 201)
        path = f"/api/tasks/{task.json['id']}"
        for value in ([], [1], {}, True, 1.0, -1, 2**63, "bad"):
            with self.subTest(value=value):
                for method, route, body in (
                    ("POST", members, {"user_id": value}),
                    ("DELETE", members, {"user_id": value}),
                    ("POST", "/api/tasks", {**task_payload, "project_id": value}),
                    ("POST", "/api/tasks", {**task_payload, "assignee_id": value}),
                    ("PATCH", path, {"assignee_id": value}),
                ):
                    self.assertEqual(self.client.open(route, method=method, json=body).status_code, 422)
        cleared = self.client.patch(path, json={"assignee_id": None})
        self.assertEqual(cleared.status_code, 200)
        self.assertIsNone(cleared.json["assignee"])

    def test_project_and_task_description_types_are_validated(self):
        self.assertEqual(self.login("alice@example.test", "alice-password").status_code, 200)
        project = self.client.post("/api/projects", json={"name": "New project"})
        self.assertEqual(project.status_code, 201)
        project_id = project.json["id"]
        task = self.client.post("/api/tasks", json={"title": "A task", "project_id": project_id})
        self.assertEqual(task.status_code, 201)
        for collection, item_id, fields in (
            ("/api/projects", project_id, {"name": "Another project"}),
            ("/api/tasks", task.json["id"], {"title": "Another task", "project_id": project_id}),
        ):
            path = f"{collection}/{item_id}"
            for description in ([], {}, 10, True):
                with self.subTest(collection=collection, description=description):
                    created = self.client.post(collection, json={**fields, "description": description})
                    updated = self.client.patch(path, json={"description": description})
                    self.assertEqual(created.status_code, 422)
                    self.assertEqual(updated.status_code, 422)
            self.assertEqual(self.client.patch(path, json={"description": None}).status_code, 200)

    def test_task_status_and_priority_reject_structured_values(self):
        self.assertEqual(self.login("alice@example.test", "alice-password").status_code, 200)
        with app.app_context():
            project_id = Project.query.filter_by(name="Private project").one().id
        payload = {"title": "Task", "project_id": project_id}
        task = self.client.post("/api/tasks", json=payload)
        self.assertEqual(task.status_code, 201)
        path = f"/api/tasks/{task.json['id']}"
        for field in ("status", "priority"):
            for value in ([], {}, None, True):
                with self.subTest(field=field, value=value):
                    self.assertEqual(self.client.post("/api/tasks", json={
                        **payload, field: value,
                    }).status_code, 422)
                    self.assertEqual(self.client.patch(path, json={
                        "title": "Should not persist", field: value,
                    }).status_code, 422)
        tasks = self.client.get("/api/tasks").json
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["title"], "Task")

    def test_mutating_api_requires_json_objects(self):
        self.assertEqual(self.login("alice@example.test", "alice-password").status_code, 200)
        with app.app_context():
            project_id = Project.query.filter_by(name="Private project").one().id
        task = self.client.post("/api/tasks", json={"title": "Task", "project_id": project_id})
        self.assertEqual(task.status_code, 201)
        for method, path in (
            ("POST", "/api/projects"),
            ("PATCH", f"/api/projects/{project_id}"),
            ("POST", f"/api/projects/{project_id}/members"),
            ("DELETE", f"/api/projects/{project_id}/members"),
            ("POST", "/api/tasks"),
            ("PATCH", f"/api/tasks/{task.json['id']}"),
        ):
            for body in ("[]", "[1]", "null", '"name"', "{"):
                with self.subTest(method=method, path=path, body=body):
                    result = self.client.open(path, method=method, data=body,
                                              content_type="application/json")
                    self.assertEqual(result.status_code, 400)
                    self.assertEqual(result.json["error"], "A JSON object is required")

    def test_project_creation_rolls_back_if_owner_membership_fails(self):
        self.assertEqual(self.login("alice@example.test", "alice-password").status_code, 200)

        def reject_membership(*args):
            raise RuntimeError("Owner membership insert failed")

        event.listen(ProjectMember, "before_insert", reject_membership)
        try:
            for path, payload in (
                ("/api/projects", {"json": {"name": "API project"}}),
                ("/projects/create", {"data": {"name": "Form project"}}),
            ):
                with self.subTest(path=path):
                    with self.assertRaisesRegex(RuntimeError, "Owner membership insert failed"):
                        self.client.post(path, **payload)
                    with app.app_context():
                        self.assertEqual(Project.query.count(), 1)
        finally:
            event.remove(ProjectMember, "before_insert", reject_membership)

    def test_invalid_due_date_types_return_validation_error(self):
        self.login("alice@example.test", "alice-password")
        with app.app_context():
            project_id = Project.query.filter_by(name="Private project").one().id
        for value in [123, True, [], {}]:
            with self.subTest(value=value):
                response = self.client.post("/api/tasks", json={
                    "title": "Invalid date", "project_id": project_id, "due_date": value,
                })
                self.assertEqual(response.status_code, 422)

    def test_task_creation_rejects_invalid_title_without_creating_task(self):
        from app import Task
        self.login("alice@example.test", "alice-password")
        with app.app_context():
            project_id = Project.query.filter_by(name="Private project").one().id
        for title in [None, "", "   ", 123, True, [], {}]:
            with self.subTest(title=title):
                response = self.client.post("/api/tasks", json={
                    "title": title, "project_id": project_id,
                })
                self.assertEqual(response.status_code, 422)
                with app.app_context():
                    self.assertEqual(Task.query.count(), 0)
        response = self.client.post("/api/tasks", json={
            "title": "  Valid task  ", "project_id": project_id,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["title"], "Valid task")

    def test_task_update_rejects_invalid_title_without_changes(self):
        from app import Task
        self.login("alice@example.test", "alice-password")
        with app.app_context():
            alice = User.query.filter_by(email="alice@example.test").one()
            project = Project.query.filter_by(name="Private project").one()
            task = Task(title="Original", project_id=project.id, created_by_id=alice.id)
            db.session.add(task)
            db.session.commit()
            task_id = task.id
        for title in [None, "", "   ", 123, [], {}]:
            with self.subTest(title=title):
                response = self.client.patch(f"/api/tasks/{task_id}", json={"title": title})
                self.assertEqual(response.status_code, 422)
                with app.app_context():
                    self.assertEqual(db.session.get(Task, task_id).title, "Original")
        response = self.client.patch(f"/api/tasks/{task_id}", json={"title": "  Updated  "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["title"], "Updated")

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


    def test_project_api_rejects_non_string_names(self):
        self.login("alice@example.test", "alice-password")
        with app.app_context():
            project_id = Project.query.filter_by(name="Private project").one().id

        for name in [None, 123, True, [], {}]:
            with self.subTest(name=name):
                create = self.client.post("/api/projects", json={"name": name})
                update = self.client.patch(f"/api/projects/{project_id}", json={"name": name})
                self.assertEqual(create.status_code, 422)
                self.assertEqual(update.status_code, 422)

        with app.app_context():
            self.assertEqual(Project.query.count(), 1)
            self.assertEqual(db.session.get(Project, project_id).name, "Private project")

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


    def test_unrelated_member_cannot_modify_or_delete_task(self):
        from app import Task
        with app.app_context():
            alice = User.query.filter_by(email="alice@example.test").one()
            project = Project.query.filter_by(name="Private project").one()
            task = Task(title="Private task", project_id=project.id, created_by_id=alice.id)
            db.session.add(task)
            db.session.commit()
            task_id = task.id
        self.assertEqual(self.login("bob@example.test", "bob-password").status_code, 200)
        self.assertEqual(self.client.patch(f"/api/tasks/{task_id}", json={"title": "Tampered"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/tasks/{task_id}").status_code, 403)
        with app.app_context():
            self.assertEqual(db.session.get(Task, task_id).title, "Private task")

    def test_task_creator_can_delete_own_task(self):
        from app import Task
        with app.app_context():
            alice = User.query.filter_by(email="alice@example.test").one()
            project = Project.query.filter_by(name="Private project").one()
            task = Task(title="My task", project_id=project.id, created_by_id=alice.id)
            db.session.add(task)
            db.session.commit()
            task_id = task.id
        self.assertEqual(self.login("alice@example.test", "alice-password").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/tasks/{task_id}").status_code, 200)
        with app.app_context():
            self.assertIsNone(db.session.get(Task, task_id))

    def test_assignee_cannot_reassign_task(self):
        from app import Task
        with app.app_context():
            alice = User.query.filter_by(email="alice@example.test").one()
            bob = User.query.filter_by(email="bob@example.test").one()
            project = Project.query.filter_by(name="Private project").one()
            task = Task(title="Assigned task", project_id=project.id,
                        created_by_id=alice.id, assignee_id=bob.id)
            db.session.add(task)
            db.session.commit()
            task_id = task.id
            alice_id = alice.id
            bob_id = bob.id
        self.assertEqual(self.login("bob@example.test", "bob-password").status_code, 200)
        response = self.client.patch(f"/api/tasks/{task_id}", json={"assignee_id": alice_id})
        self.assertEqual(response.status_code, 403)
        with app.app_context():
            self.assertEqual(db.session.get(Task, task_id).assignee_id, bob_id)

    def test_creator_cannot_assign_task_to_unknown_user(self):
        from app import Task
        with app.app_context():
            alice = User.query.filter_by(email="alice@example.test").one()
            project = Project.query.filter_by(name="Private project").one()
            task = Task(title="Valid task", project_id=project.id, created_by_id=alice.id)
            db.session.add(task)
            db.session.commit()
            task_id = task.id
        self.assertEqual(self.login("alice@example.test", "alice-password").status_code, 200)
        response = self.client.patch(f"/api/tasks/{task_id}", json={"assignee_id": 99999999})
        self.assertEqual(response.status_code, 422)
        with app.app_context():
            self.assertIsNone(db.session.get(Task, task_id).assignee_id)

if __name__ == "__main__":
    unittest.main()

