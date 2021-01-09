# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import logging
from logging import Formatter, FileHandler

import babel
import dateutil.parser
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)



# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500), )
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(20)))
    website = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))

    shows = db.relationship('Shows', backref='venue', lazy=True)



class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(20)))
    website = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Shows', backref='artist', lazy=True)



class Shows(db.Model):
    __table__name = 'Shows'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False, default=1)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False, default=1)
    start_time = db.Column(db.DateTime, nullable=False)



# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en_IN')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    city_data = {}
    venues_list = Venue.query.all()
    data = []
    if venues_list:
        for venue in venues_list:
            key = venue.city + "__" + venue.state
            shows = Shows.query.filter(Shows.start_time > datetime.now()).count()
            app.logger.info("shows - {0}".format(shows))

            if key in city_data:
                data[city_data.get(key)] = data[city_data.get(key)].get('venues').append({
                    'id': venue.id,
                    'name': venue.name,
                    'num_upcoming_shows': shows
                })
            else:
                city_data[key] = len(data)
                data.append({
                    'city': venue.city,
                    'state': venue.state,
                    'venues': [{
                        'id': venue.id,
                        'name': venue.name,
                        'num_upcoming_shows': shows
                    }]
                })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # search for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search = request.form.get('search_term')
    app.logger.info("search term {0}".format(search))
    venues = Venue.query.filter(Venue.name.ilike('%'+search+'%')).all()
    data = []
    count = 0
    if venues:
        for venue in venues:
            count += 1
            shows = Shows.query.filter(Shows.start_time > datetime.now()).count()
            data.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': shows
            })
    return render_template('pages/search_venues.html', results={
        'count': count,
        'data': data}, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get(venue_id)
    past_shows_list = Shows.query.filter(Shows.venue_id == venue_id, Shows.start_time <= datetime.now()).all()
    upcoming_shows_list = Shows.query.filter(Shows.venue_id == venue_id, Shows.start_time > datetime.now()).all()
    past_shows = []
    for show in past_shows_list:
        artist = Artist.query.get(show.artist_id)
        past_shows.append({
            'artist_id': artist.id,
            'artist_name': artist.name,
            'artist_image_link': artist.image_link,
            'start_time': str(show.start_time)
        })

    upcoming_shows = []
    for show in upcoming_shows_list:
        artist = Artist.query.get(show.artist_id)
        upcoming_shows.append({
            'artist_id': artist.id,
            'artist_name': artist.name,
            'artist_image_link': artist.image_link,
            'start_time': str(show.start_time)
        })
    response = venue.__dict__
    response['past_shows'] = past_shows
    response['upcoming_shows'] = upcoming_shows
    response['past_shows_count'] = len(past_shows)
    response['upcoming_shows_count'] = len(upcoming_shows)
    app.logger.info("response = {0}".format(response))
    return render_template('pages/show_venue.html', venue=response)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    session = db.session()
    try:
        venue = Venue()
        venue.name = request.form.get("name")
        venue.city = request.form.get("city")
        venue.state = request.form.get("state")
        venue.image_link = request.form.get("image_link")
        venue.address = request.form.get("address")
        venue.genres = request.form.get("genres").split(",")
        venue.phone = request.form.get("phone")
        venue.seeking_description = request.form.get("description")
        venue.seeking_talent = request.form.get("seeking_talent")
        venue.website = request.form.get("website")
        session.flush()
        session.add(venue)
        session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
        session.rollback()
        app.logger.info("error occurred while creating venue {0}".format(e.args))
        flash('Venue ' + request.form['name'] + ' was failed with error ' + e.args)

    # on successful db insert, flash success

    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except Exception as  e:
        app.logger.info("error occurred while deleting venue {0}".format(e.args))
    return None


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = Artist.query.all()
    data = []
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })
    return render_template("pages/artists.html", artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # search for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search = request.form.get('search_term')
    app.logger.info("search term {0}".format(search))
    artists = Artist.query.filter(Artist.name.ilike('%' + search + '%')).all()
    data = []
    count = 0
    if artists:
        for artist in artists:
            count += 1
            shows = Shows.query.filter(Shows.start_time > datetime.now()).count()
            data.append({
                'id': artist.id,
                'name': artist.name,
                'num_upcoming_shows': shows
            })
    response = {
        "count": count,
        "data": data
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    artist = Artist.query.get(artist_id)
    if artist:
        shows = artist.shows
        data = artist.__dict__
        data['past_shows'] = []
        data['upcoming_shows'] = []
        if shows:
            for show in shows:
                venue = Venue.query.get(show.venue_id)
                if venue:
                    if show.start_time < datetime.now():
                        data['past_shows'].append({
                            'venue_id': venue.id,
                            'venue_name': venue.name,
                            'venue_image_link': venue.image_link,
                            'start_time': str(show.start_time)
                        })
                    else:
                        data['upcoming_shows'].append({
                            'venue_id': venue.id,
                            'venue_name': venue.name,
                            'venue_image_link': venue.image_link,
                            'start_time': str(show.start_time)
                        })

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    try:
        artist = Artist.query.get(artist_id)
        if artist:
            for key in request.form.keys():
                app.logger.error("key = {0} and value =  {1}".format(key, request.form.get(key)))
                setattr(artist, key, request.form.get(key))
            if request.form.__contains__("genres"):
                artist.genres = request.form.get("genres").split(",")
            db.session.commit()
    except Exception as e:
         app.logger.info("artist updating failed with error {0}".format(e.args))
    finally:
        return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    return render_template('forms/edit_venue.html', form=form, venue=venue)



@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue = Venue.query.get(venue_id)
    if venue:
        for key in request.form.keys():
            app.logger.error("key = {0} and value =  {1}".format(key, request.form.get(key)))
            setattr(venue, key, request.form.get(key))
        if request.form.__contains__("genres"):
            venue.genres = request.form.get("genres").split(",")
        db.session.commit()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    try:
        artist = Artist()
        for key in request.form.keys():
            app.logger.info("key = {0} and value =  {1}".format(key, request.form.get(key)))
            setattr(artist, key, request.form.get(key))
        artist.genres = request.form.get("genres").split(",")
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
        app.logger.info("Artist creation failed with error")
        flash('Artist ' + request.form['name'] + ' was failed with error {0}'.format(e.args))

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows

    shows = Shows.query.all()
    data = []
    if shows:
        for show in shows:
            venue = Venue.query.get(show.venue_id)
            artist = Artist.query.get(show.artist_id)
            data.append(
                {'venue_id': venue.id, 'venue_name': venue.name, 'artist_id': artist.id, 'artist_name': artist.name,
                 'artist_image_link': artist.image_link, 'start_time': str(show.start_time)})
    return render_template('pages/shows.html', shows=data)




@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form

    # on successful db insert, flash success
    try:
        show = Shows()
        show.artist_id = request.form.get("artist_id")
        show.venue_id = request.form.get("venue_id")
        show.start_time = request.form.get("start_time")
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except Exception as e:
        app.logger.info('An error occurred. Show could not be listed. and error is {0}'.format(e.args))
        flash('An error occurred. Show could not be listed.')
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
