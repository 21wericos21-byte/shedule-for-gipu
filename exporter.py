import json
import datetime
from models import Event

# Базовые времена начала и конца пар
PAIR_TIMES = {
    1: (datetime.time(8, 20), datetime.time(9, 55)),
    2: (datetime.time(10, 5), datetime.time(11, 40)),
    3: (datetime.time(12, 20), datetime.time(13, 55)),
    4: (datetime.time(14, 5), datetime.time(15, 40)),
    5: (datetime.time(15, 50), datetime.time(17, 25)),
    6: (datetime.time(17, 35), datetime.time(19, 10))
}

# Опорная дата: первый понедельник семестра (для генерации timestamp)
# Вы можете поменять год, месяц и день под свой семестр.
# 7 сентября 2026 года — это понедельник.
BASE_DATE = datetime.date(2026, 9, 7)


def export_events_to_json(db_session):
    events = db_session.query(Event).all()
    result = []

    for e in events:
        # 1. Восстанавливаем даты начала и конца пары
        # e.day_of_week: 0 = Пн, 1 = Вт и т.д.
        target_date = BASE_DATE + datetime.timedelta(days=e.day_of_week)

        pair_start_time, pair_end_time = PAIR_TIMES.get(e.pair_number, (datetime.time(8, 20), datetime.time(9, 55)))

        dt_start = datetime.datetime.combine(target_date, pair_start_time)
        dt_end = datetime.datetime.combine(target_date, pair_end_time)

        # 2. Восстанавливаем дату окончания повторения
        dt_rec_end = dt_start + datetime.timedelta(weeks=e.repeat_weeks)

        # 3. Переводим в UNIX timestamp (как в исходном events_old.json)
        start_ts = int(dt_start.timestamp())
        end_ts = int(dt_end.timestamp())
        rec_end_ts = int(dt_rec_end.timestamp())

        # 4. Определяем тип повторяемости (1 - каждую неделю, 2 - раз в две недели)
        weekly_recurrence = 1 if e.week_type == 1 else 2

        # 5. Формируем словарь
        event_dict = {
            "eventId": e.series_id,  # Используем ID серии, чтобы сгруппировать дни одной пары
            "eventName": e.name,
            "eventType": e.type,
            "groupId": [g.strip() for g in e.group_ids.split(',')] if e.group_ids else [],
            "eventDateStart": start_ts,
            "eventDateEnd": end_ts,
            "recurrenceDateEnd": rec_end_ts,
            "weeklyRecurrence": weekly_recurrence
        }

        # Добавляем необязательные поля, если они есть
        if e.teacher_ids:
            event_dict["teacherIds"] = [t.strip() for t in e.teacher_ids.split(',')]
        if e.room_ids:
            event_dict["roomIds"] = [r.strip() for r in e.room_ids.split(',')]

        result.append(event_dict)

    # Сохраняем в файл
    #with open('../integration_max/payloads/events.json', 'w', encoding='utf-8') as f:
    #    json.dump(result, f, ensure_ascii=False, indent=2)
    return json.dumps(result, ensure_ascii=False, indent=2), len(result)
    #return len(result)