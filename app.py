import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from sqlalchemy import or_

from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY
from models import db, User, Faculty, Group, Subgroup, Teacher, Building, Room, Event, Discipline
from collision_checker import check_collisions
from exporter import export_events_to_json

load_dotenv()

# ==========================================
# 1. ИНИЦИАЛИЗАЦИЯ
# ==========================================
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SECRET_KEY'] = SECRET_KEY
db.init_app(app)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password_hash=generate_password_hash('admin123'), role='admin')
        db.session.add(admin)
        db.session.commit()


# ==========================================
# 2. МАРШРУТЫ
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('index'))
        flash('Неверный логин или пароль', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    faculties = Faculty.query.all()
    courses = [1, 2, 3, 4, 5, 6]
    teachers = Teacher.query.all()
    buildings = Building.query.all()

    return render_template('schedule.html',
                           faculties=faculties, courses=courses,
                           teachers=teachers, buildings=buildings)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('role') != 'admin': return redirect(url_for('index'))

    if request.method == 'POST' and request.form.get('action') == 'export':
        json_data, count = export_events_to_json(db.session)
        filename = f"events_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json"

        return Response(
            json_data,
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )

    teachers = Teacher.query.order_by(Teacher.short_name).all()
    buildings = Building.query.all()

    return render_template('admin.html', teachers=teachers, buildings=buildings)


# --- API ---
@app.route('/api/rooms/<building_id>')
def api_get_rooms(building_id):
    return jsonify(
        {"rooms": [{"id": r.id, "name": r.name} for r in Room.query.filter_by(building_id=building_id).all()]})


@app.route('/api/disciplines')
def api_get_disciplines():
    return jsonify({"disciplines": [d.name for d in Discipline.query.all()]})


@app.route('/api/groups/<faculty_id>/<int:course>')
def api_get_groups(faculty_id, course):
    return jsonify({"groups": [{"id": g.id, "name": g.name} for g in
                               Group.query.filter_by(faculty_id=faculty_id, course=course).all()]})


@app.route('/api/subgroups/<group_id>')
def api_get_subgroups(group_id):
    return jsonify(
        {"subgroups": [{"id": s.id, "name": s.name} for s in Subgroup.query.filter_by(group_id=group_id).all()]})


@app.route('/api/group_details/<group_id>')
def api_get_group_details(group_id):
    group = Group.query.get(group_id)
    if not group: return jsonify({"error": "not found"}), 404
    return jsonify({"id": group.id, "faculty_id": group.faculty_id, "course": group.course})


@app.route('/api/events/<group_id>')
def api_get_group_events(group_id):
    events = Event.query.filter(Event.group_ids.contains(group_id)).all()
    return jsonify([{
        "id": e.id, "series_id": e.series_id, "name": e.name, "type": e.type,
        "day": e.day_of_week, "pair": e.pair_number, "week_type": e.week_type,
        "subgroup": e.subgroup_ids, "room": e.room_ids, "teacher": e.teacher_ids,
        "groups": e.group_ids, "color": e.color or '#ffffff'
    } for e in events])


@app.route('/api/event_series/<series_id>')
def api_get_series(series_id):
    events = Event.query.filter_by(series_id=series_id).all()
    if not events: return jsonify({"error": "not found"}), 404
    e = events[0]

    days_data = []
    for ev in events:
        days_data.append({
            "day": ev.day_of_week, "pair": ev.pair_number,
            "week_type": ev.week_type, "type": ev.type,
            "teacher": ev.teacher_ids
        })

    return jsonify({
        "series_id": e.series_id, "name": e.name, "repeat_weeks": e.repeat_weeks,
        "groups": e.group_ids.split(','), "subgroup": e.subgroup_ids,
        "room": e.room_ids, "days_data": days_data
    })


@app.route('/api/check_collision', methods=['POST'])
def api_check_collision():
    data = request.json
    collisions = check_collisions(data, db.session)
    if collisions: return jsonify({"status": "error", "reason": " / ".join(collisions)})
    return jsonify({"status": "ok"})


@app.route('/api/event/color', methods=['POST'])
def api_event_color():
    data = request.json
    series_id = data.get('series_id')
    color = data.get('color')

    if not series_id:
        return jsonify({"status": "error", "reason": "series_id is required"}), 400

    Event.query.filter_by(series_id=series_id).update({Event.color: color})
    db.session.commit()
    return jsonify({"status": "ok"})


# НОВЫЙ ЭНДПОИНТ ДЛЯ АНАЛИТИКИ ЗАГРУЗКИ
@app.route('/api/analytics/load', methods=['POST'])
def api_analytics_load():
    data = request.json
    entity_type = data.get('type')  # 'room' или 'teacher'
    entity_id = data.get('id')

    if not entity_type or not entity_id:
        return jsonify({"error": "Missing parameters"}), 400

    if entity_type == 'room':
        room = Room.query.get(entity_id)
        if not room:
            return jsonify([])

        # IDs в базе имеют формат "1.0-237", а Room.id — "1-237".
        # Проверяем оба варианта, чтобы не зависеть от формата хранения.
        ids_to_check = {room.id}
        parts = room.id.split('-', 1)
        if len(parts) == 2:
            ids_to_check.add(f"{parts[0]}.0-{parts[1]}")

        conditions = []
        for rid in ids_to_check:
            conditions.extend([
                Event.room_ids == rid,
                Event.room_ids.like(f"{rid},%"),
                Event.room_ids.like(f"%,{rid}"),
                Event.room_ids.like(f"%,{rid},%"),
            ])
        events = Event.query.filter(or_(*conditions)).all()

    elif entity_type == 'teacher':
        conditions = [
            Event.teacher_ids == entity_id,
            Event.teacher_ids.like(f"{entity_id},%"),
            Event.teacher_ids.like(f"%,{entity_id}"),
            Event.teacher_ids.like(f"%,{entity_id},%"),
        ]
        events = Event.query.filter(or_(*conditions)).all()
    else:
        return jsonify({"error": "Invalid type"}), 400

    return jsonify([{
        "id": e.id, "series_id": e.series_id, "name": e.name, "type": e.type,
        "day": e.day_of_week, "pair": e.pair_number, "week_type": e.week_type,
        "subgroup": e.subgroup_ids, "room": e.room_ids, "teacher": e.teacher_ids,
        "groups": e.group_ids, "color": e.color or '#ffffff'
    } for e in events])


@app.route('/event/save', methods=['POST'])
def save_event():
    data = request.json
    collisions = check_collisions(data, db.session)
    if collisions: return jsonify({"status": "error", "reason": " / ".join(collisions)})

    series_id = data.get('series_id')
    current_color = '#ffffff'

    if series_id:
        existing_ev = Event.query.filter_by(series_id=series_id).first()
        if existing_ev:
            current_color = existing_ev.color or '#ffffff'
        Event.query.filter_by(series_id=series_id).delete()
    else:
        series_id = str(uuid.uuid4())

    group_str = ",".join(data['groups'])

    for day_info in data['days_data']:
        new_event = Event(
            id=str(uuid.uuid4()),
            series_id=series_id, name=data['name'],
            type=day_info.get('type', 'Иное'),
            color=current_color,
            day_of_week=int(day_info['day']), pair_number=int(day_info['pair']),
            week_type=int(day_info['week_type']), repeat_weeks=int(data.get('repeat_weeks', 16)),
            group_ids=group_str, subgroup_ids=data.get('subgroup', ''),
            teacher_ids=day_info.get('teacher', ''), room_ids=data.get('room', '')
        )
        db.session.add(new_event)

    db.session.commit()
    return jsonify({"status": "ok"})


@app.route('/event/delete/<series_id>', methods=['DELETE'])
def delete_series(series_id):
    Event.query.filter_by(series_id=series_id).delete()
    db.session.commit()
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(debug=True, port=5001)