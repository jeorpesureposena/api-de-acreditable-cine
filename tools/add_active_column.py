from app.database import engine
from sqlalchemy import text

def main():
    with engine.begin() as conn:
        conn.execute(
            text("ALTER TABLE boletos ADD COLUMN IF NOT EXISTS activo boolean DEFAULT true")
        )
    print("ok")


if __name__ == "__main__":
    main()
