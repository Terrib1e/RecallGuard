"""Script to create database tables."""

from database import engine, Base
from models import User, Product, Recall, RecallAlert

if __name__ == "__main__":
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    print("Tables created:")
    print("  - users")
    print("  - products")
    print("  - recalls")
    print("  - recall_alerts")