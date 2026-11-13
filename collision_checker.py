from models import Event

DAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб"]


def check_collisions(new_events_data, db_session):
    collisions = []
    groups = new_events_data.get('groups', [])
    subgroup = new_events_data.get('subgroup', '')
    room = new_events_data.get('room', '')
    series_id = new_events_data.get('series_id', 'new')

    for day_info in new_events_data['days_data']:
        day = int(day_info['day'])
        pair = int(day_info['pair'])
        week_type = int(day_info['week_type'])
        teacher = day_info.get('teacher', '')  # <--- Препод для конкретного дня

        existing_events = db_session.query(Event).filter(
            Event.day_of_week == day,
            Event.pair_number == pair,
            Event.series_id != series_id
        ).all()

        for ex in existing_events:
            if week_type != 1 and ex.week_type != 1:
                if week_type != ex.week_type:
                    continue

            day_str = DAYS_RU[day] if day < len(DAYS_RU) else str(day)

            if room and ex.room_ids and room in ex.room_ids.split(','):
                collisions.append(f"Ауд. {room} занята в {day_str}, {pair} пара")

            if teacher and ex.teacher_ids and teacher in ex.teacher_ids.split(','):
                collisions.append(f"Преподаватель занят в {day_str}, {pair} пара")

            if groups:
                new_g = set(groups)
                ex_g = set(ex.group_ids.split(','))
                if new_g & ex_g:
                    new_s = {subgroup} if subgroup else set()
                    ex_s = set(ex.subgroup_ids.split(',')) if ex.subgroup_ids else set()
                    if not new_s or not ex_s or (new_s & ex_s):
                        collisions.append(f"Группа занята в {day_str}, {pair} пара")

    return list(set(collisions))