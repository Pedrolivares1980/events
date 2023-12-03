from sqlalchemy import or_
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Event, Reservation
from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY
from flask_migrate import Migrate

# Initialize Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

# Setup Flask-Migrate for database migrations
migrate = Migrate(app, db)


# Helper function to check if user is authenticated
def is_authenticated():
    return "user_id" in session


# Helper function to check if the logged-in user is a business user
def is_business_user():
    if is_authenticated():
        return User.query.get(session["user_id"]).is_business
    return False


# Decorator to ensure user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            flash("Please log in to access this page.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


# Decorator to ensure user is a business user
def business_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_business_user():
            flash("This page is only accessible to business users.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


# Custom Jinja filter to format datetime
def format_datetime(value, format="%Y-%m-%d"):
    if value is None:
        return ""
    return value.strftime(format)


app.jinja_env.filters["todatetime"] = format_datetime


# Custom Jinja filter to format time
def format_time(value, format="%H:%M"):
    if value is None:
        return ""
    return value.strftime(format)


app.jinja_env.filters["totime"] = format_time


# Route for the index page
@app.route("/")
def index():
    """
    Render the index page.
    Fetches a list of events ordered by start time and limits to 6 for display.
    """
    events = Event.query.order_by(Event.start_time).limit(6).all()
    return render_template("index.html", events=events)


# Route for user registration
@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Handles user registration. Processes the form data to register a new user.
    Includes validation for field lengths and checks for existing usernames or emails.
    """
    if request.method == "POST":
        # Extracting form data
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        is_business = request.form.get("is_business") == "on"
        company_name = request.form.get("company_name") if is_business else None

        # Validation checks for field lengths
        if len(username) > 80:
            flash("Username is too long. Maximum 80 characters allowed.", "danger")
            return render_template("register.html")
        if len(email) > 120:
            flash("Email is too long. Maximum 120 characters allowed.", "danger")
            return render_template("register.html")
        if len(password) > 128:
            flash("Password is too long. Maximum 128 characters allowed.", "danger")
            return render_template("register.html")
        if company_name and len(company_name) > 100:
            flash("Company name is too long. Maximum 100 characters allowed.", "danger")
            return render_template("register.html")

        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            flash("Username or email already registered.", "danger")
            return redirect(url_for("register"))

        # Create new user object and set password
        new_user = User(
            username=username,
            email=email,
            is_business=is_business,
            company_name=company_name,
        )
        new_user.set_password(password)

        # Add to database and commit
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# Route for user login
@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Handles user login. It processes the form data to authenticate the user.
    On successful login, the user's ID and their business status are stored in the session.
    """
    if request.method == "POST":
        login_input = request.form["login"]  # Could be either username or email
        password = request.form["password"]

        # Check both username and email for login
        user = User.query.filter(
            (User.username == login_input) | (User.email == login_input)
        ).first()

        # If user exists and password is correct
        if user and user.check_password(password):
            session["user_id"] = user.id  # Store user ID in session
            session[
                "is_business"
            ] = user.is_business  # Store business status in session
            flash("You have successfully logged in.", "success")
            return redirect(url_for("index"))

        # If authentication fails
        flash("Invalid username, email or password.", "danger")

    return render_template("login.html")


# Route for user logout
@app.route("/logout")
def logout():
    """
    Handles user logout. Clears the user's session data and redirects to the index page.
    """
    # Clearing the user's session data
    session.pop("user_id", None)
    session.pop("is_business", None)  # Clearing business status as well

    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


# Route for business profile
@app.route("/business_profile")
@login_required
@business_required
def business_profile():
    """
    Renders the business profile page for business users. Lists the events organized by the business user.
    Implements pagination for the list of events.
    """
    user_id = session["user_id"]
    events = Event.query.filter_by(organizer_id=user_id).all()

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 8, type=int)
    events_paginated = Event.query.filter_by(organizer_id=user_id).paginate(
        page=page, per_page=per_page, error_out=False
    )

    user = User.query.get(user_id)
    business_name = user.company_name

    # Calculate available seats for each event and check if it's sold out
    for event in events_paginated.items:
        total_reserved_seats = sum(
            reservation.seats for reservation in event.reservations
        )
        event.available_seats = event.capacity - total_reserved_seats
        event.sold_out = total_reserved_seats >= event.capacity

    return render_template(
        "business_profile.html",
        events=events_paginated.items,
        pagination=events_paginated,
        business_name=business_name,
    )


# Route for create event
@app.route("/create_event", methods=["GET", "POST"])
@login_required
@business_required
def create_event():
    """
    Handles the creation of new events by business users.
    Validates the form data for length constraints and adds the new event to the database.
    """
    if "user_id" not in session or not User.query.get(session["user_id"]).is_business:
        flash("Only business users can create events.", "danger")
        return redirect(url_for("index"))

    company_name = User.query.get(session["user_id"]).company_name

    if request.method == "POST":
        # Extracting form data
        title = request.form["title"]
        description = request.form["description"]
        location = request.form["location"]

        # Validation for field lengths
        if len(title) > 100:
            flash("Title is too long. Maximum 100 characters allowed.", "danger")
            return render_template("create_event.html", company_name=company_name)
        if len(description) > 1000:
            flash("Description is too long. Maximum 1000 characters allowed.", "danger")
            return render_template("create_event.html", company_name=company_name)
        if len(location) > 120:
            flash("Location is too long. Maximum 120 characters allowed.", "danger")
            return render_template("create_event.html", company_name=company_name)

        # Extract and parse date and time
        event_date_str = request.form["event_date"]
        start_time_str = request.form["start_time"]
        event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
        start_time = datetime.strptime(start_time_str, "%H:%M").time()

        # Extract other event details
        duration = int(request.form["duration"])
        capacity = int(request.form["capacity"])
        event_type = request.form["event_type"]

        # Create new event object
        new_event = Event(
            title=title,
            description=description,
            event_date=event_date,
            start_time=start_time,
            duration=duration,
            capacity=capacity,
            event_type=event_type,
            location=location,
            organizer_id=session["user_id"],
        )

        # Add new event to database
        db.session.add(new_event)
        db.session.commit()

        flash("Event created successfully.", "success")
        return redirect(url_for("business_profile"))

    return render_template("create_event.html", company_name=company_name)


# Route for edit events
@app.route("/edit_event/<int:event_id>", methods=["GET", "POST"])
@login_required
@business_required
def edit_event(event_id):
    """
    Allows business users to edit an existing event. Includes detailed form data validation.
    Ensures that only the organizer of the event can edit it.
    """
    event = Event.query.get_or_404(event_id)

    # Check if the logged-in user is the organizer of the event
    if session["user_id"] != event.organizer_id:
        flash("Only the organizer can edit this event.", "danger")
        return redirect(url_for("business_profile"))

    if request.method == "POST":
        event.title = request.form["title"]
        event.description = request.form["description"]
        event.location = request.form["location"]

        # Validation for field lengths with error messages
        if len(event.title) > 100:
            flash("Title is too long. Maximum 100 characters allowed.", "danger")
            return render_template("edit_event.html", event=event)
        if len(event.description) > 1000:
            flash("Description is too long. Maximum 1000 characters allowed.", "danger")
            return render_template("edit_event.html", event=event)
        if len(event.location) > 120:
            flash("Location is too long. Maximum 120 characters allowed.", "danger")
            return render_template("edit_event.html", event=event)

        # Extract and parse date and time
        event_date_str = request.form["event_date"]
        start_time_str = request.form["start_time"]
        event.event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
        event.start_time = datetime.strptime(start_time_str, "%H:%M").time()

        # Extract other event details and update the event
        event.capacity = int(request.form["capacity"])
        event.duration = int(request.form["duration"])

        # Update the event in the database
        db.session.commit()

        flash("Event updated successfully.", "success")
        return redirect(url_for("business_profile"))

    return render_template("edit_event.html", event=event)


# Route for display events
@app.route("/events")
def events():
    """
    Displays the list of events. Includes filters for event type, start and end dates, and a search term.
    Implements pagination for displaying the events.
    """
    search = request.args.get("search", "")
    event_type = request.args.get("event_type", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    # Build the query based on filters
    query = Event.query
    if event_type:
        query = query.filter(Event.event_type == event_type)
    if start_date:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(Event.event_date >= start_date_obj)
    if end_date:
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(Event.event_date <= end_date_obj)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(Event.title.like(search_term), Event.description.like(search_term))
        )

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 8, type=int)
    events_paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    # Retrieve distinct event types for the filter dropdown
    event_types = [
        type[0] for type in Event.query.with_entities(Event.event_type).distinct().all()
    ]

    # Calculate available seats for each event
    for event in events_paginated.items:
        total_reserved_seats = sum(
            reservation.seats for reservation in event.reservations
        )
        event.available_seats = event.capacity - total_reserved_seats

    return render_template(
        "events.html",
        events=events_paginated.items,
        pagination=events_paginated,
        event_types=event_types,
    )


# Route for user profile
@app.route("/user_profile")
@login_required
def user_profile():
    """
    Displays the user profile page with the user's reservations.
    Implements pagination for the reservations list.
    """
    user_id = session["user_id"]

    # Pagination setup for reservations
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 8, type=int)
    reservations_paginated = Reservation.query.filter_by(user_id=user_id).paginate(
        page=page, per_page=per_page, error_out=False
    )

    user = User.query.get(user_id)

    return render_template(
        "user_profile.html",
        user=user,
        reservations=reservations_paginated.items,
        pagination=reservations_paginated,
    )


# Route for reserves
@app.route("/reserve/<int:event_id>", methods=["GET", "POST"])
@login_required
def reserve(event_id):
    """
    Handles reservation creation for a specific event. Includes checks for event existence,
    user authentication, and seat availability.
    """
    # Fetch the event or return 404 if not found
    event = Event.query.get_or_404(event_id)

    # Check if the user is a business user (business users can't make reservations)
    if is_business_user():
        flash("Business users cannot make reservations.", "danger")
        return redirect(url_for("events"))

    if request.method == "POST":
        try:
            seats = int(request.form["seats"])
        except ValueError:
            flash("Invalid number of seats.", "danger")
            return redirect(url_for("reserve", event_id=event_id))

        # Calculate available seats
        total_reserved_seats = sum(
            reservation.seats for reservation in event.reservations
        )
        available_seats = event.capacity - total_reserved_seats

        # Check if there are enough seats available
        if seats <= available_seats:
            # Create and save the new reservation
            new_reservation = Reservation(
                user_id=session["user_id"], event_id=event.id, seats=seats
            )
            db.session.add(new_reservation)
            db.session.commit()
            flash("Reservation successful.", "success")
        else:
            flash("Not enough seats available.", "danger")

        return redirect(url_for("events"))

    return render_template("reserve.html", event=event)


# 
# Route for edit reservations
@app.route("/edit_reservation/<int:reservation_id>", methods=["GET", "POST"])
@login_required
def edit_reservation(reservation_id):
    """
    Allows users to edit or cancel their existing reservation.
    Checks that the reservation exists and that the logged-in user is the one who made the reservation.
    Handles the update of reservation details.
    """
    # Fetch the reservation and the corresponding event or return 404 if not found
    reservation = Reservation.query.get_or_404(reservation_id)
    event = Event.query.get_or_404(reservation.event_id)

    # Ensure the logged-in user is the one who made the reservation
    if session["user_id"] != reservation.user_id:
        flash("You can only edit your own reservations.", "danger")
        return redirect(url_for("user_profile"))
    
    # Calculate available seats for the specific event
    total_reserved_seats = sum(res.seats for res in event.reservations)
    available_seats = event.capacity - total_reserved_seats
    event.available_seats = available_seats

    if request.method == "POST":
        if "cancel" in request.form:
            # Delete the reservation if the user chooses to cancel it
            db.session.delete(reservation)
            db.session.commit()
            flash("Reservation cancelled successfully.", "success")
            return redirect(url_for("user_profile"))

        # Update the number of seats in the reservation
        seats = int(request.form["seats"])

        # Check if the updated number of seats is available
        if seats <= available_seats:
            reservation.seats = seats
            db.session.commit()
            flash("Reservation updated successfully.", "success")
            return redirect(url_for("user_profile"))
        else:
            flash("Not enough seats available.", "danger")

    return render_template(
        "edit_reservation.html",
        reservation=reservation,
        event=event,
        available_seats=available_seats,
    )



if __name__ == "__main__":
    app.run(debug=True)
