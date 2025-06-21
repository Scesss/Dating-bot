from .db import Database

if __name__ == "__main__":
    db = Database()
    db.create_tables()
    print("✅ All tables created and ready for PostgreSQL.")