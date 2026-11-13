from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False) # <--- БЫЛО 128, СТАЛО 255
    role = db.Column(db.String(20), default='dean')


class Faculty(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50), nullable=True)


class Group(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    faculty_id = db.Column(db.String(50), db.ForeignKey('faculty.id'))
    course = db.Column(db.Integer, nullable=False, default=1)
    level = db.Column(db.String(20), default='BACHELOR')


class Subgroup(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    group_id = db.Column(db.String(50), db.ForeignKey('group.id'))
    name = db.Column(db.String(10), nullable=False)


class Teacher(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    short_name = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.String(100))


class Building(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))


class Room(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    building_id = db.Column(db.String(50), db.ForeignKey('building.id'))
    floor = db.Column(db.Integer)


class Discipline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500), unique=True, nullable=False) # Увеличили до 500

class Event(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    series_id = db.Column(db.String(100), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False) # Увеличили до 500
    type = db.Column(db.String(100))                 # Увеличили до 100
    color = db.Column(db.String(20), nullable=True, default='#ffffff')

    day_of_week = db.Column(db.Integer, nullable=False)
    pair_number = db.Column(db.Integer, nullable=False)
    week_type = db.Column(db.Integer, nullable=False, default=1)  # 1-каждая, 2-числ, 3-знам
    repeat_weeks = db.Column(db.Integer, default=16)

    group_ids = db.Column(db.String(200), nullable=False)
    subgroup_ids = db.Column(db.String(200))
    teacher_ids = db.Column(db.String(200))
    room_ids = db.Column(db.String(200))