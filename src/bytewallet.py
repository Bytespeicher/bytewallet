# all the imports
import os
import sqlite3

from flask import Flask, request, session, g, url_for, render_template, \
    redirect, flash, send_from_directory

from flask.ext.babel import Babel, gettext
from passlib.apps import custom_app_context as pwd_context
from config import LANGUAGES, UPLOAD_FOLDER, ALLOWED_FILE_EXTENSIONS
from werkzeug import secure_filename

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'bytewallet.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    BABEL_DEFAULT_LOCALE='de',
    UPLOAD_FOLDER=UPLOAD_FOLDER
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
    cur = db.execute('SELECT id, name, money, photo ' +
                     'FROM wallet ' +
                     'ORDER BY last_update DESC')
    wallets = cur.fetchall()

    return render_template('show_wallets.html', wallets=wallets)


@app.route('/wallet/<wallet_id>')
def wallet(wallet_id):
    db = get_db()
    cur = db.execute('SELECT id, name, money, photo FROM wallet WHERE id = ?',
                     [wallet_id])

    wallet = cur.fetchone()

    if wallet is None:
        flash(gettext('Requested wallet not found'))
        return redirect(url_for('show_wallets'))

    return render_template('edit_wallet.html', wallet=wallet)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/update_wallet', methods=['POST'])
def update_wallet():
    error = None
    if request.method == 'POST':
        db = get_db()
        cur = db.execute('SELECT pin FROM wallet WHERE id = ?',
                         [request.form['id']])

        res = cur.fetchone()

        error = False
        if res is None:
            error = gettext('Could not find user entry')
        elif pwd_context.verify(request.form['password'],
                                res['password']) is not True:
            error = gettext('Invalid PIN')
        else:
            session['logged_in'] = True
    return redirect(url_for('show_wallets'), error=error)


@app.route('/new_wallet', methods=['GET'])
def new_wallet():
    return render_template('new_wallet.html')


@app.route('/create_wallet', methods=['POST'])
def create_wallet():
    if 'name' not in request.form:
        flash(gettext('You need to specify a name'))
        return redirect(url_for('new_wallet'))

    if 'pin' not in request.form:
        flash(_('You need to specify a pin'))
        return redirect(url_for('new_wallet'))

    db = get_db()
    cur = db.execute('SELECT id FROM wallet WHERE name = ?',
                     [request.form['name']])

    if cur.fetchone() is not None:
        flash(gettext('That name is already taken'))
        return redirect(url_for('new_wallet'))

    if 'photo' in request.files:
        print(request.files['photo'])

        def allowed_file(filename):
            return '.' in filename and \
                filename.rsplit('.', 1)[1] in ALLOWED_FILE_EXTENSIONS

        file = request.files['photo']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        filename = ''

    password = pwd_context.encrypt(request.form['pin'])

    db.execute('INSERT INTO wallet (name, pin, photo) VALUES (?, ?, ?)',
               [request.form['name'], password, filename])

    try:
        db.commit()
        flash(gettext('Your wallet was added successfully'), 'success')
    except:
        flash(gettext('An error occured'), 'error')

    return redirect(url_for('show_wallets'))


@app.route('/install')
def install():
    init_db()
    return render_template('install.html')


if __name__ == '__main__':
    app.run()
