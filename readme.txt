 # EventSphere App

This is a event management app that allows users to register as a user or business, login, create and modify events only for business, and make and edit bookings only for regular users. It is built using Flask, and SQLAlchemy and SQLite3 for the data management. This project is the module 4 Databases assesment for the course "Full Stack Software Development" of UCDPA.
The web app and server is deploy it in render.com:

https://eventsphere.onrender.com

## Setup

To set up the app, clone the repository and install the dependencies:

```
git clone https://github.com/your-username/events.git

In the terminal install all the requirements:
pip install -r requirements.txt
```

## Usage

To run the app, simply run:

```
python app.py
```

## Features

The app has the following features:

* User registration and login,
* Business registration and login,
* Creating events with a title, description, location, date, time,
* View, edit o cancel any event or any booking of an this business event
* Dashboard with a list of events,
* Events listing with filtering by date, location, or category,
* Searching for an event using keywords,
* Book spaces for an event
* View, edit o cancel the bookings


## Code Structure

The app is structured as follows:

* `app.py`: The main Flask app file.
* `config.py`: Contains the configuration used by the app.
* `models.py`: Contains the databases models.
* `templates`: The Jinja2 templates used by the app.
* `static`: The static files used by the app.
