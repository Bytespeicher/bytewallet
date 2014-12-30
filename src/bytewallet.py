# all the imports
import os
import sqlite3
import datetime

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

from flask.ext.babel    import Babel, gettext
from passlib.apps       import custom_app_context as pwd_context
from config             import LANGUAGES

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'bytewallet.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    BABEL_DEFAULT_LOCALE='de',
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

babel = Babel(app)

@babel.localeselector
def get_locale():
    # if a user is logged in, use the locale from the user settings
    user = getattr(g, 'user', None)
    if user is not None:
        return user.locale
    return request.accept_languages.best_match(LANGUAGES.keys())

@babel.timezoneselector
def get_timezone():
    user = getattr(g, 'user', None)
    if user is not None:
        return user.timezone

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema/schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def show_wallets():
    db = get_db()
    cur = db.execute('SELECT id, name, money ' +
                     'FROM wallet ' +
                     'ORDER BY last_update DESC')
    keys = cur.fetchall()

    return render_template('show_wallets.html', keys=keys)

@app.route('/check-pin', methods=['POST'])
def check_ping():
    error = None
    if request.method == 'POST':
        db = get_db()
        cur = db.execute('SELECT pin FROM wallet WHERE id = ?',
                         [request.form['userid']])

        res = cur.fetchone()

        error = false
        if res == None:
            error = gettext('Could not find user entry')
        elif pwd_context.verify(request.form['password'], res['password']) != True:
            error = gettext('Invalid PIN')
        else:
            session['logged_in'] = True
    return render_template('check_pin.json', error=error)

@app.route('/save-user', methods=['POST'])
def save_admin():
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    password = pwd_context.encrypt(request.form['pin'])

    db.execute('INSERT INTO admins (name, mail, password) VALUES (?, ?, ?)',
                [request.form['name'], request.form['mail'],
                 password])

    try:
        db.commit()
        message = gettext('Changes saved successfully')
    except:
        message = gettext('An error occured')

    return render_template('save_user.json', message = message)

@app.route('/install')
def install():
    init_db()
    return render_template('install.html')


if __name__ == '__main__':
    app.run()
