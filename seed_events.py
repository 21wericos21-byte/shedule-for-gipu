import json
import os
import datetime
import uuid
from app import app, db
from models import Event

PAIR_TIMES = {
    1: (8 * 60 + 20, 9 * 60 + 55), 2: (10 * 60 + 5, 11 * 60 + 40),
    3: (12 * 60 + 20, 13 * 60 + 55), 4: (14 * 60 + 5, 15 * 60 + 40),
    5: (15 * 60 + 50, 17 * 60 + 25), 6: (17 * 60 + 35, 19 * 60 + 10)
}


def get_pair_number(dt):
    time_val = dt.hour * 60 + dt.minute
    for pair, (start, end) in PAIR_TIMES.items():
        if start <= time_val <= end:
            return pair
    return 1


def load_events_json():
    paths = ["payloads/events_old.json", os.path.join(os.path.dirname(__file__), "payloads/events1.json")]
    for p in paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f: return json.load(f)
    return []


def seed_events():
    data = load_events_json()
    if not data: return

    with app.app_context():
        Event.query.delete()
        db.session.commit()

        count = 0
        for ev in data:
            dt_start = datetime.datetime.fromtimestamp(ev['eventDateStart'])
            dt_rec_end = datetime.datetime.fromtimestamp(ev.get('recurrenceDateEnd', ev['eventDateStart']))

            day_of_week = dt_start.weekday()
            if day_of_week > 5: continue

            pair_num = get_pair_number(dt_start)
            weekly_rec = ev.get('weeklyRecurrence', 1)

            if weekly_rec == 1:
                week_type = 1
            else:
                week_num = dt_start.isocalendar()[1]
                week_type = 2 if week_num % 2 != 0 else 3

            repeat_weeks = max(1, (dt_rec_end - dt_start).days // 7)

            new_event = Event(
                id=str(uuid.uuid4()),
                series_id=ev.get('eventId', str(uuid.uuid4())),
                name=ev.get('eventName', 'Без названия'),
                type=ev.get('eventType', 'Иное'),
                color="#ffffff",  # <--- Цвет по умолчанию
                day_of_week=day_of_week,
                pair_number=pair_num,
                week_type=week_type,
                repeat_weeks=repeat_weeks,
                group_ids=",".join(ev.get('groupId', [])),
                subgroup_ids="",
                teacher_ids=",".join(ev.get('teacherIds', [])) if 'teacherIds' in ev else "",
                room_ids=",".join(ev.get('roomIds', [])) if 'roomIds' in ev else ""
            )
            db.session.add(new_event)
            count += 1

        db.session.commit()
        print(f"✅ Успешно добавлено {count} занятий!")


if __name__ == "__main__":
    seed_events()