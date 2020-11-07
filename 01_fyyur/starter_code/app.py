#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form

from forms import *
import sys
from datetime import datetime
from models import Venue, Show, Artist, app, db

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#


app.config.from_object('config')
moment = Moment(app)
db.init_app(app)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

    venues = Venue.query.order_by(Venue.state, Venue.city).all()

    data = []
    prev_state = ''
    prev_city = ''
    venue_obj = {}
    for venue in venues:
        print(venue.city)
        shows = len(Show.query.filter_by(venue_id=venue.id).filter(Show.start_time > datetime.now()).all())
        if prev_city != venue.city and venue_obj:
            print('here')
            data.append(venue_obj)
            venue_obj = {}
        elif prev_state != venue.state and venue_obj:
            data.append(venue_obj)
            venue_obj = {}

        if not venue_obj:
            venue_obj['city'] = venue.city
            venue_obj['state'] = venue.state
        if 'venues' not in venue_obj:
            venue_obj['venues'] = [{'id': venue.id, 'name': venue.name,
                                   'num_upcoming_shows': shows}]
        else:
            venue_obj['venues'].append({'id': venue.id, 'name': venue.name,
                                        'num_upcoming_shows': shows})
        prev_city = venue.city
        prev_state = venue.state
    data.append(venue_obj)

    return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():

    search_term = request.form.get('search_term', '')
    search_result = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()
    data = []
    for result in search_result:
      data.append({
          "id": result.id,
          "name": result.name,
          "num_upcoming_shows": len(
              db.session.query(Show).filter(Show.venue_id == result.id).filter(Show.start_time > datetime.now()).all()),
      })
    response = {
      "count": len(search_result),
      "data": data
    }

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    venue = Venue.query.get(venue_id)
    upcoming_shows = Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all()
    past_shows = Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time < datetime.now()).all()

    data = {
        'id': venue.id,
        'name': venue.name,
        'genres': list(venue.genres[1:-1].split(",")),
        'address': venue.address,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'website': venue.website,
        'facebook_link': venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'image_link': venue.image_link,
        'past_shows': [],
        'upcoming_shows': []
    }
    for upcoming_show in upcoming_shows:
        artist = Artist.query.get(upcoming_show.artist_id)
        data['upcoming_shows'].append({
            'artist_id': artist.id,
            'artist_name': artist.name,
            'artist_image_link': artist.image_link,
            'start_time': upcoming_show.start_time.strftime('%Y-%m-%d, %H:%M')
        })

    for past_show in past_shows:
        print(past_show.artist_id, venue_id)
        artist = Artist.query.get(past_show.artist_id)
        data['past_shows'].append({
            'artist_id': artist.id,
            'artist_name': artist.name,
            'artist_image_link': artist.image_link,
            'start_time': past_show.start_time.strftime('%Y-%m-%d, %H:%M')
        })

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    genres = request.form.getlist('genres')
    website = request.form['website']
    seeking_talent = False
    if 'seeking_talent' in request.form:
        seeking_talent = True
    seeking_description = request.form['seeking_description']
    venue = Venue(
        name=name, city=city, state=state, address=address, phone=phone, image_link=image_link,
        facebook_link=facebook_link, genres=genres, website=website, seeking_talent=seeking_talent,
        seeking_description=seeking_description
    )
    try:

        db.session.add(venue)
        db.session.commit()

    except Exception as e:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        print(e)
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue ' + name + ' could not be listed.')
    if not error:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({'sucess': True})

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artist = Artist.query.all()
  d = []
  for artist in artist:
      d.append({
          'id': artist.id,
          'name': artist.name
      })
  return render_template('pages/artists.html', artists=d)

@app.route('/artists/search', methods=['POST'])
def search_artists():

    search_term = request.form.get('search_term', '')
    search_result = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
    data = []
    for result in search_result:
        data.append({
            "id": result.id,
            "name": result.name,
            "num_upcoming_shows": len(
                db.session.query(Show).filter(Show.venue_id == result.id).filter(
                    Show.start_time > datetime.now()).all()),
        })
    response = {
        "count": len(search_result),
        "data": data
    }

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    upcoming_shows = Show.query.filter(Show.artist_id == artist.id).filter(Show.start_time > datetime.now()).all()
    past_shows = Show.query.filter(Show.artist_id == artist.id).filter(Show.start_time < datetime.now()).all()
    data = {
      'id': artist.id,
      'name': artist.name,
      'genres': list(artist.genres[1:-1].split(',')),
      'city': artist.city,
      'state': artist.state,
      'phone': artist.phone,
      'seeking_venue': artist.seeking_venue,
      'seeking_description': artist.seeking_description,
      'website': artist.website,
      'image_link': artist.image_link,
      'facebook_link': artist.facebook_link,
      'upcoming_shows': [],
      'past_shows': [],
      'upcoming_shows_count': len(upcoming_shows),
      'past_shows_count': len(past_shows)
    }

    for upcoming_show in upcoming_shows:
        venue = Venue.query.get(upcoming_show.venue_id)
        data['upcoming_shows'].append({
          'venue_id': venue.id,
          'venue_name': venue.name,
          'venue_image_link': venue.image_link,
          'start_time': upcoming_show.start_time.strftime('%Y-%m-%d %H:%M')
      })

    for past_show in past_shows:
        venue = Venue.query.get(past_show.venue_id)
        data['past_shows'].append({
          'venue_id': venue.id,
          'venue_name': venue.name,
          'venue_image_link': venue.image_link,
          'start_time': past_show.start_time.strftime('%Y-%m-%d, %H:%M')
      })

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()

    artist = Artist.query.get(artist_id)

    form.name.data = artist.name
    form.genres.data = artist.genres
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.website.data = artist.website
    form.facebook_link.data = artist.facebook_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    form.image_link.data = artist.image_link

    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    genres = request.form.getlist('genres')
    website = request.form['website']
    seeking_venue = False
    if 'seeking_venue' in request.form:
        seeking_venue = True
    seeking_description = request.form['seeking_description']
    artist = Artist(
        name=name, city=city, state=state, phone=phone, image_link=image_link,
        facebook_link=facebook_link, genres=genres, website=website, seeking_venue=seeking_venue,
        seeking_description=seeking_description
    )
    try:

        db.session.add(artist)
        db.session.commit()

    except Exception as e:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        print(e)
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist ' + name + ' could not be updated.')
    if not error:
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
    return render_template('pages/home.html')


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()

    venue = Venue.query.get(venue_id)
    form.name.data = venue.name
    form.genres.data = venue.genres
    form.address.data = venue.address
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.website.data = venue.website
    form.facebook_link.data = venue.facebook_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.image_link.data = venue.image_link
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    error = False
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    genres = request.form.getlist('genres')
    website = request.form['website']
    seeking_talent = False
    if 'seeking_talent' in request.form:
        seeking_talent = True
    seeking_description = request.form['seeking_description']
    venue = Venue(
        name=name, city=city, state=state, address=address, phone=phone, image_link=image_link,
        facebook_link=facebook_link, genres=genres, website=website, seeking_talent=seeking_talent,
        seeking_description=seeking_description
    )
    try:

        db.session.add(venue)
        db.session.commit()

    except Exception as e:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        print(e)
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue ' + name + ' could not be updated.')
    if not error:
        flash('Venue ' + request.form['name'] + ' was successfully updated!')

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    genres = request.form.getlist('genres')
    website = request.form['website']
    seeking_venue = False
    if 'seeking_venue' in request.form:
        seeking_venue = True
    seeking_description = request.form['seeking_description']
    artist = Artist(
        name=name, city=city, state=state, phone=phone, image_link=image_link,
        facebook_link=facebook_link, genres=genres, website=website, seeking_venue=seeking_venue,
        seeking_description=seeking_description
    )
    try:

        db.session.add(artist)
        db.session.commit()

    except Exception as e:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        print(e)
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist ' + name + ' could not be listed.')
    if not error:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')



#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    all_shows = Show.query.all()
    d = []
    for show in all_shows:
        print(show.venue_id)
        venue = Venue.query.get(show.venue_id)
        artist = Artist.query.get(show.artist_id)
        data_obj = {
            'venue_id': show.venue_id,
            'venue_name': venue.name,
            'artist_id': show.artist_id,
            'artist_name': artist.name,
            'artist_image_link': artist.image_link,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M')
        }
        d.append(data_obj)
    return render_template('pages/shows.html', shows=d)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False

    artist = request.form['artist_id']
    venue = request.form['venue_id']
    start_time = request.form['start_time']

    show = Show(
        artist_id=artist, venue_id=venue, start_time=start_time
    )

    try:
        db.session.add(show)
        db.session.commit()

    except Exception as e:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        print(e)
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Show could not be listed.')

    if not error:
        flash('Show was successfully listed!')
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

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
