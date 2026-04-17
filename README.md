# Taskflow

A Flask todo app with user login and SQLite.

## Features
- Register and log in
- Add, complete, and delete todos
- SQLite storage
- Session-based auth

## Run
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export SECRET_KEY='change-me'
flask --app app init-db
flask --app app run
```
