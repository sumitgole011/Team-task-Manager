# ✅ Team Task Manager

## Recruiter quick view

**Problem:** Teams need a central place to coordinate projects, ownership, deadlines and progress.

**Approach:** A Flask application using SQLAlchemy, role-based permissions, relational storage and REST APIs to support team and task workflows.

**Explore:** Review the feature list, local setup instructions and API documentation below. Database configuration supports SQLite locally and PostgreSQL in supported deployments.

**Engineering discussion points:** Authentication and authorization boundaries, project/member relationships, task lifecycle, database migrations, and deployment configuration.

> **Verification note:** This section summarizes the documented architecture; it does not claim that the application has been independently deployed or end-to-end tested.


<p align="center">
  <strong>A full-stack web application to organize projects, collaborate with teams, assign tasks, and track progress efficiently.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask"/>
  <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge" alt="SQLAlchemy"/>
  <img src="https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL-4169E1?style=for-the-badge" alt="Databases"/>
  <img src="https://img.shields.io/badge/Deployment-Railway-8A2BE2?style=for-the-badge" alt="Railway"/>
</p>

## 📌 Overview

**Team Task Manager** is a Python Flask-based full-stack application that simplifies team collaboration and project organization through a centralized task management system.

Users can create projects, manage team members, assign tasks, set priorities and deadlines, and monitor task progress through a dashboard. The application incorporates authentication, role-based access control, REST APIs, and relational database management.

The backend uses Flask-SQLAlchemy with SQLite for local development and supports PostgreSQL through environment-based configuration for deployment.

## ✨ Key Features

- 🔐 **User Authentication:** User registration, login, logout, and session management.
- 👥 **Role-Based Access Control:** Separate permissions for Admin and Member roles.
- 📁 **Project Management:** Create, update, view, and delete projects.
- 🤝 **Team Collaboration:** Add or remove members from projects.
- ✅ **Task Management:** Create, assign, update, and delete tasks.
- 🚦 **Priority Management:** Classify tasks as Low, Medium, or High priority.
- 📅 **Deadline Tracking:** Set due dates and identify overdue tasks.
- 📊 **Dashboard:** Monitor task totals, status counts, and overdue items.
- 🔌 **REST APIs:** Endpoints for authentication, users, projects, project members, and tasks.
- 🗄️ **Database Integration:** Manage relational data using Flask-SQLAlchemy.
- 🚀 **Deployment Configuration:** Includes Railway configuration and Gunicorn support.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| Flask-SQLAlchemy | ORM and database operations |
| SQLite | Local database |
| PostgreSQL | Production database option |
| HTML & CSS | Frontend templates and styling |
| Werkzeug | Password hashing |
| Gunicorn | Production WSGI server |
| Railway | Deployment platform |

## 🏗️ Application Workflow

1. **Authentication:** Users register or log in to access the application.
2. **Project Creation:** Project owners create projects and manage membership.
3. **Task Assignment:** Tasks are created with descriptions, priorities, deadlines, and optional assignees.
4. **Progress Tracking:** Task statuses are updated as work progresses.
5. **Dashboard Monitoring:** Task summaries and overdue work are displayed.
6. **API Integration:** REST endpoints allow programmatic interaction with the application's resources.

## 📂 Project Structure

```text
team-task-manager/
├── app.py
├── requirements.txt
├── Procfile
├── railway.json
├── templates/
├── static/
├── .gitignore
└── README.md
```

## ⚙️ Installation & Setup

### Prerequisites

- Python 3
- Git
- pip

### Step 1: Clone the repository

```bash
git clone https://github.com/sumitgole011/Team-task-Manager.git
cd Team-task-Manager
```

### Step 2: Create a virtual environment

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure environment variables

Create a `.env` file in the project directory:

```env
SECRET_KEY=your-strong-secret-key
```

For local development, the application uses SQLite by default. To use PostgreSQL, configure the `DATABASE_URL` environment variable with your database connection string.

**Security note:** Use a strong secret key and never commit credentials or production database URLs to GitHub.

### Step 5: Run the application

```bash
python app.py
```

Open the following URL in your browser:

```text
http://127.0.0.1:5000
```

## 🔌 REST API Documentation

The application provides REST endpoints for authentication, users, projects, members, and tasks.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/signup` | Register a user |
| POST | `/api/auth/login` | Authenticate a user |
| POST | `/api/auth/logout` | End the current session |
| GET | `/api/auth/me` | Retrieve current user details |

### Users

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/users` | List registered users (Admin only) |

### Projects

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/projects` | List accessible projects |
| POST | `/api/projects` | Create a project |
| GET | `/api/projects/<project_id>` | Retrieve project details |
| PATCH | `/api/projects/<project_id>` | Update a project |
| DELETE | `/api/projects/<project_id>` | Delete a project |

### Project Members

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/projects/<project_id>/members` | List project members |
| POST | `/api/projects/<project_id>/members` | Add a member |
| DELETE | `/api/projects/<project_id>/members` | Remove a member |
| GET | `/api/projects/<project_id>/tasks` | Retrieve project tasks |

### Tasks

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/tasks` | List accessible tasks |
| POST | `/api/tasks` | Create a task |
| PATCH | `/api/tasks/<task_id>` | Update a task |
| DELETE | `/api/tasks/<task_id>` | Delete a task |

### Example Task Payload

```json
{
  "title": "Create login page",
  "description": "Build UI and validation",
  "project_id": 1,
  "assignee_id": 2,
  "status": "Todo",
  "priority": "High",
  "due_date": "2026-05-20"
}
```

**Supported statuses:** `Todo`, `In Progress`, `Done`

**Supported priorities:** `Low`, `Medium`, `High`

## 🔒 Role-Based Permissions

- **Admin:** Can manage projects, members, and tasks across the application.
- **Member:** Can access projects and tasks permitted by their membership or assignment.
- **Project Owner:** Can add or remove project members.
- **Task Creator:** Can delete tasks they created.

Administrative permissions take precedence where supported by the backend access rules.

## 🚀 Deployment with Railway

The repository contains deployment configuration for Railway and Gunicorn.

1. Push the application code to GitHub.
2. Create a Railway project using the repository.
3. Add a PostgreSQL database if using PostgreSQL in production.
4. Configure `DATABASE_URL` and `SECRET_KEY` in the service's environment variables.
5. Deploy the application.
6. Verify authentication, database connectivity, project operations, and task management.

The configured Gunicorn command is:

```bash
gunicorn app:app
```

## 🎯 Skills Demonstrated

- Full-stack web development with Python and Flask
- User authentication and authorization
- REST API development
- Relational database design and ORM
- CRUD operations
- Role-based access control
- Backend validation and session management
- Environment configuration
- Application deployment using Railway and Gunicorn

## 👨‍💻 Author

**Sumit Gole**

- GitHub Profile: [@sumitgole011](https://github.com/sumitgole011)
- Project Repository: [Team Task Manager](https://github.com/sumitgole011/team-task-manager)

---

<p align="center">
  <strong>Built with Python and Flask to make project coordination and task tracking easier.</strong>
</p>

## Production security configuration

Before deploying, configure a strong, unique `SECRET_KEY` using the hosting platform's secret manager. The development fallback key in `app.py` is **not safe for public deployment**. Set `COOKIE_SECURE=true` only when your app is served over HTTPS; this makes session cookies HTTPS-only. Keep `FLASK_DEBUG=false` in production and serve with a production WSGI server rather than Flask's development server.

This project sets HttpOnly and SameSite=Lax session cookies and basic response security headers. **These are baseline protections, not a complete security audit.** State-changing HTML forms still need a dedicated CSRF-protection review, and production secrets, TLS, database backups, and deployment settings must be verified separately. See `.env.example` for non-secret variable names.

