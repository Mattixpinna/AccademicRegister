# Academic Register

This is a private electronic register intended for academic use. It allows teachers to have a dashboard to work from and control the actions to be taken, and for managers to administer the system.

## Features

### Teacher (`docente`)
- **Dashboard**: A personalized home page.
- **Lesson Selection**: View a list of scheduled lessons for the current day.
- **Attendance Tracking**: Take and save student attendance for a specific lesson.
- **Presence Confirmation**: Sign off on their own attendance for a lesson they have taught.

### Manager
- **Dashboard**: A central dashboard for administrative tasks.
- **Teaching Management**:
    - Add, update, and remove subjects/courses (`insegnamenti`).
    - Assign subjects to different study plans (`PianoDiStudi`).
- **Student Management**:
    - Add, update, and delete student records.
    - Enroll (`iscrivere`) students in individual subjects or entire academic years.
    - View student attendance records.
- **Teacher Management**:
    - Add, update, and remove teacher accounts.
    - Assign teachers to subjects (`cattedre`).
    - Monitor teacher attendance and performance.
- **Lesson Scheduling**:
    - Create, view, and delete lessons in a calendar view.

## Technologies Used

- **Backend**: Python with [Flask](https://flask.palletsprojects.com/)
- **Database**: [MySQL](https://www.mysql.com/) (via `pymysql` and `dbutils` for connection pooling)
- **Frontend**: HTML templates with [Jinja2](https://jinja.palletsprojects.com/)
- **Security**:
    - [Flask-WTF](https://flask-wtf.readthedocs.io/) for CSRF protection.
    - Secure cookies (`SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE`, `SESSION_COOKIE_SECURE`).
    - [Flask-Limiter](https://flask-limiter.readthedocs.io/) for rate limiting API endpoints.
- **Dependencies**: Managed with `pip` and documented in `requirements.txt`.

## Project Structure

```
.
├── app.py              # Main Flask application factory
├── auth_routes.py      # Handles login, logout, and authentication
├── teacher_routes.py   # Routes for the teacher role
├── manager_routes.py   # Routes for the manager role
├── database.py         # Database connection pooling and setup
├── extensions.py       # Initialization of Flask extensions (e.g., CSRF, Limiter)
├── requirements.txt    # Python package dependencies
├── static/             # CSS, JavaScript, and other static assets
└── templates/          # HTML templates for different views
    ├── manager/
    ├── teacher/
    └── ...
```

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up the database:**
    - Make sure you have a running MySQL server.
    - Create a database for the project (e.g., `academic_register`).
    - You will need to create the necessary tables. A `schema.sql` file is not provided, but the table structure can be inferred from the queries in the `*_routes.py` files.

5.  **Configure environment variables:**
    - Create a file named `.env` in the root of the project directory.
    - Add the following variables, replacing the placeholder values with your actual database credentials:
      ```
      DB_HOST=localhost
      DB_USER=your_db_user
      DB_PASSWORD=your_db_password
      DB_NAME=academic_register
      SECRET_KEY=a-very-strong-and-secret-key-for-sessions
      ```
    - The `SECRET_KEY` is crucial for session security and CSRF protection.

## How to Run the Application

Once the setup is complete, you can run the Flask development server:

```bash
python app.py
```

The application will be available at `http://127.0.0.1:5001` by default.