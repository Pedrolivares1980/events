from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """
    Represents a user in the system. Can be either a regular user or a business user.
    """
    __tablename__ = 'users' 
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_business = db.Column(db.Boolean, default=False)  # New field to indicate business user
    company_name = db.Column(db.String(100))
    reservations = db.relationship('Reservation', backref='user', lazy='dynamic')

    def set_password(self, password):
        """Generates and sets the password hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks the password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Event(db.Model):
    """
    Represents an event created by a business user.
    """
    __tablename__ = 'events' 

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    event_date = db.Column(db.Date, nullable=False) 
    start_time = db.Column(db.Time, nullable=False) 
    duration = db.Column(db.Integer, nullable=False) 
    capacity = db.Column(db.Integer, nullable=False) 
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organizer = db.relationship('User', backref='organized_events')
    event_type = db.Column(db.String(50))
    location = db.Column(db.String(120))

    reservations = db.relationship('Reservation', backref='event', lazy='dynamic')
    @property
    def event_image(self):
        event_images = {
            'Concert': 'concert.webp',
            'Sport': 'sport.webp',
            'Theatre': 'theatre.webp',
            'Cinema': 'cinema.webp',
            'Exhibition': 'exhibition.webp',
            'Festival': 'festival.webp',
            'Workshop': 'workshop.webp',
            'Other': 'other.webp'
        }
        return event_images.get(self.event_type, 'default.jpg')

class Reservation(db.Model):
    """
    Represents a reservation made by a user for an event.
    """
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) 
    seats = db.Column(db.Integer, nullable=False) 

    def __repr__(self):
        return f'<Reservation User: {self.user_id}, Event: {self.event_id}>'
