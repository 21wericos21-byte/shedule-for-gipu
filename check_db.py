from app import app, db
from models import Faculty, Group, User

with app.app_context():
    print("=== ПРОВЕРКА БАЗЫ ДАННЫХ ===")
    print(f"Пользователей: {User.query.count()}")
    print(f"Факультетов: {Faculty.query.count()}")
    print(f"Групп: {Group.query.count()}")

    print("\nСписок факультетов:")
    for f in Faculty.query.all():
        print(f" - {f.name} (ID: {f.id})")