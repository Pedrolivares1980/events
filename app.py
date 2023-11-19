# app.py
from sqlalchemy import or_
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Event, Reservation
from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

def is_authenticated():
    return 'user_id' in session

def is_business_user():
    if is_authenticated():
        return User.query.get(session['user_id']).is_business
    return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def business_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_business_user():
            flash('This page is only accessible to business users.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def format_datetime(value, format='%Y-%m-%d'):
    """Convierte un objeto datetime a una cadena en el formato especificado."""
    if value is None:
        return ""
    return value.strftime(format)

# Añadir el filtro al entorno Jinja de Flask
app.jinja_env.filters['todatetime'] = format_datetime

def format_time(value, format='%H:%M'):
    """Convierte un objeto datetime a una cadena en el formato de hora especificado."""
    if value is None:
        return ""
    return value.strftime(format)

# Agregar el filtro al entorno Jinja de Flask
app.jinja_env.filters['totime'] = format_time


@app.route('/')
def index():
    """
    Render the index page.
    """
    events = Event.query.order_by(Event.start_time).limit(6).all()
    return render_template('index.html', events=events)

# User registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Route for user registration.
    """
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        is_business = request.form.get('is_business') == 'on'
        company_name = request.form.get('company_name') if is_business else None

        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already registered.', 'danger')
            return redirect(url_for('register'))
        
        is_business = request.form.get('is_business') == 'on'
        new_user = User(username=username, email=email, is_business=is_business, company_name=company_name)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Route for user login.
    """
    if request.method == 'POST':
        login_input = request.form['login']  # The form field can be renamed to 'username_or_email'
        password = request.form['password']

        # Check both username and email for login
        user = User.query.filter((User.username == login_input) | (User.email == login_input)).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['is_business'] = user.is_business
            flash('You have successfully logged in.', 'success')
            return redirect(url_for('index'))

        flash('Invalid username, email or password.', 'danger')

    return render_template('login.html')


# User logout route
@app.route('/logout')
def logout():
    """
    Route for user logout.
    """
    print("Processing user logout")
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# Ruta de perfil del usuario para gestionar reservas
@app.route('/user_profile')
@login_required
def user_profile():
    """
    User profile route for users to manage their reservations.
    """
    if 'user_id' not in session:
        flash('You need to login to access your profile.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)  # Obtener el objeto de usuario
    reservations = Reservation.query.filter_by(user_id=user_id).all()
    return render_template('user_profile.html', user=user, reservations=reservations)

@app.route('/events')
def events():
    # Parámetros de filtrado y búsqueda
    search = request.args.get('search', '')
    event_type = request.args.get('event_type', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # Query base
    query = Event.query

    # Aplica filtros según sea necesario
    if event_type:
        query = query.filter(Event.event_type == event_type)
    if start_date:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(Event.event_date >= start_date_obj)
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(Event.event_date <= end_date_obj)
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(Event.title.like(search_term), Event.description.like(search_term)))

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 6, type=int)
    events_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    event_types = [type[0] for type in Event.query.with_entities(Event.event_type).distinct().all()]

    for event in events_paginated.items:
        total_reserved_seats = sum(reservation.seats for reservation in event.reservations)
        event.available_seats = event.capacity - total_reserved_seats

    return render_template('events.html', events=events_paginated.items, pagination=events_paginated, event_types=event_types)

@app.route('/reserve/<int:event_id>', methods=['GET', 'POST'])
@login_required
def reserve(event_id):
    """
    Route to handle reservations for an event.
    """
    event = Event.query.get_or_404(event_id)
    
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('events'))

    if 'user_id' not in session:
        flash('You need to log in to make a reservation.', 'danger')
        return redirect(url_for('events'))

    # Verificar si el usuario actual es de tipo "business" utilizando tu lógica personalizada
    if is_business_user():
        flash('Business users cannot make reservations.', 'danger')
        return redirect(url_for('events'))

    if request.method == 'POST':
        seats = int(request.form['seats'])
        total_reserved_seats = sum(reservation.seats for reservation in event.reservations)
        available_seats = event.capacity - total_reserved_seats

        if seats <= available_seats:
            new_reservation = Reservation(user_id=session['user_id'], event_id=event.id, seats=seats)
            db.session.add(new_reservation)
            db.session.commit()
            flash('Reservation successful.', 'success')
        else:
            flash('Not enough seats available.', 'danger')

        return redirect(url_for('events'))

    return render_template('reserve.html', event=event)








@app.route('/edit_reservation/<int:reservation_id>', methods=['GET', 'POST'])
@login_required
def edit_reservation(reservation_id):
    """
    Route for users to edit or cancel their reservation.
    """
    reservation = Reservation.query.get_or_404(reservation_id)
    event = Event.query.get_or_404(reservation.event_id)
    
    # Ensure the logged-in user is the one who made the reservation
    if 'user_id' not in session or session['user_id'] != reservation.user_id:
        flash('You can only edit your own reservations.', 'danger')
        return redirect(url_for('user_profile'))

    if request.method == 'POST':
        if 'cancel' in request.form:
            # Delete the reservation if the user chooses to cancel it
            db.session.delete(reservation)
            db.session.commit()
            flash('Reservation cancelled successfully.', 'success')
        else:
            # Update the number of seats in the reservation
            seats = int(request.form['seats'])
            # Check if the updated number of seats exceeds the event's capacity
            if seats > event.capacity:
                flash('Not enough seats available.', 'danger')
                return redirect(url_for('edit_reservation', reservation_id=reservation_id))
            reservation.seats = seats
            db.session.commit()
            flash('Reservation updated successfully.', 'success')

        return redirect(url_for('user_profile'))

    return render_template('edit_reservation.html', reservation=reservation, event=event)

@app.route('/business_profile')
@login_required
@business_required
def business_profile():
    """
    Business profile route for business users to manage their events and reservations.
    Renders the business profile page with the list of events organized by the business user and the corresponding reservations.
    """
    user_id = session['user_id']
    events = Event.query.filter_by(organizer_id=user_id).all()
    
    # Obtener el dato de company_name en lugar de username
    user = User.query.get(user_id)
    business_name = user.company_name

    # Calculate available seats for each event and check if it's sold out
    for event in events:
        total_reserved_seats = sum(reservation.seats for reservation in event.reservations)
        event.available_seats = event.capacity - total_reserved_seats
        event.sold_out = total_reserved_seats >= event.capacity

    return render_template('business_profile.html', events=events, business_name=business_name)



@app.route('/create_event', methods=['GET', 'POST'])
@login_required
@business_required
def create_event():
    """
    Route for creating a new event.
    Only accessible to business users.
    """
    if 'user_id' not in session or not User.query.get(session['user_id']).is_business:
        flash('Only business users can create events.', 'danger')
        return redirect(url_for('index'))
    
    company_name = User.query.get(session['user_id']).company_name
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        event_date_str = request.form['event_date']
        start_time_str = request.form['start_time']
        duration = int(request.form['duration'])
        capacity = int(request.form['capacity'])
        event_type = request.form['event_type']
        location = request.form['location']

        # Convert event_date and start_time to appropriate types
        event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()

        new_event = Event(title=title, description=description, event_date=event_date, location=location, start_time=start_time, duration=duration, capacity=capacity, event_type=event_type, organizer_id=session['user_id'])
        db.session.add(new_event)
        db.session.commit()

        flash('Event created successfully.', 'success')
        return redirect(url_for('business_profile'))

    return render_template('create_event.html', company_name=company_name)


@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
@business_required
def edit_event(event_id):
    """
    Route for editing an existing event.
    Only accessible by the event's organizer.
    """
    event = Event.query.get_or_404(event_id)
    if session['user_id'] != event.organizer_id:
        flash('Only the organizer can edit this event.', 'danger')
        return redirect(url_for('business_profile'))

    if request.method == 'POST':
        event.title = request.form['title']
        event.description = request.form['description']
        event.capacity = int(request.form['capacity'])
        event_date_str = request.form['event_date']
        start_time_str = request.form['start_time']
        event.duration = int(request.form['duration'])
        event.location = request.form['location']

        # Update event_date and start_time
        event.event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
        event.start_time = datetime.strptime(start_time_str, '%H:%M').time()

        db.session.commit()

        flash('Event updated successfully.', 'success')
        return redirect(url_for('business_profile'))

    return render_template('edit_event.html', event=event)


# Run the app
if __name__ == '__main__':
    app.run(debug=True)