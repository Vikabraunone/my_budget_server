from flask import Flask, g, current_app
from flask_sqlalchemy import SQLAlchemy

from app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

