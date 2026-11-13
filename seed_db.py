import json
import os
from app import app, db
from models import Faculty, Group, Subgroup, Teacher, Building, Room, Discipline


def load_json(filename):
    # Пытаемся найти файл в папке payloads рядом со скриптом
    paths_to_try = [
        os.path.join("payloads", filename),
        os.path.join(os.path.dirname(__file__), "payloads", filename),
        os.path.join(os.path.dirname(__file__), "..", "payloads", filename)
    ]

    for path in paths_to_try:
        if os.path.exists(path):
            print(f"   Найден файл: {os.path.abspath(path)}")
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

    print(f"⚠️ ВНИМАНИЕ: Файл {filename} НЕ НАЙДЕН!")
    return []


def seed():
    with app.app_context():
        print("1. Удаляем старые таблицы (если есть)...")
        db.drop_all()  # Удаляем старую базу, чтобы избежать конфликтов
        print("2. Создаем таблицы заново...")
        db.create_all()

        print("3. Загружаем факультеты...")
        facs = load_json("faculties.json")
        for item in facs:
            db.session.add(Faculty(id=item['facultyId'], name=item['facultyName'], code=item.get('facultyCode', '')))

        print("4. Загружаем группы...")
        groups = load_json("groups.json")
        seen_groups = set()
        for item in groups:
            g_id = item['groupId']
            if g_id in seen_groups: continue
            seen_groups.add(g_id)
            # Берем курс из JSON, если нет - ставим 1
            course_val = item.get('course', 1)
            # Берем уровень из JSON, если нет - BACHELOR
            level_val = item.get('level', 'BACHELOR')

            db.session.add(Group(id=g_id, name=item['groupName'], faculty_id=item['facultyId'], course=course_val,
                                 level=level_val))

            # Если есть подгруппы
            if "subgroups" in item:
                for sub in item["subgroups"]:
                    db.session.add(Subgroup(id=f"{g_id}-{sub}", group_id=g_id, name=sub))

        print("5. Загружаем преподавателей...")
        seen_teachers = set()
        for item in load_json("teachers.json"):
            t_id = item['teacherId']
            if t_id in seen_teachers: continue
            seen_teachers.add(t_id)
            db.session.add(Teacher(id=t_id, full_name=item['teacherFullName'], short_name=item['teacherName'],
                                   rank=item.get('teacherRank', '')))

        print("6. Загружаем корпуса...")
        seen_buildings = set()
        for item in load_json("buildings.json"):
            b_id = item['buildingId']
            if b_id in seen_buildings: continue
            seen_buildings.add(b_id)
            db.session.add(Building(id=b_id, name=item['buildingName'], address=item.get('buildingAddressText', '')))

        print("7. Загружаем аудитории...")
        seen_rooms = set()
        for item in load_json("rooms.json"):
            r_id = item['roomId']
            if r_id in seen_rooms: continue
            seen_rooms.add(r_id)
            db.session.add(
                Room(id=r_id, name=item['roomName'], building_id=item['buildingId'], floor=item.get('floor', 1)))

        print("8. Собираем дисциплины из events1.json...")
        events_data = load_json("events1.json")
        seen_disciplines = set()
        for ev in events_data:
            d_name = ev.get('eventName')
            if d_name and d_name not in seen_disciplines:
                seen_disciplines.add(d_name)
                db.session.add(Discipline(name=d_name))

        print("9. Сохраняем всё в базу...")
        db.session.commit()
        print("✅ База данных успешно заполнена!")


if __name__ == "__main__":
    seed()