from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = 'super_secret_vibevault_key_123' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vibevault.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# User Table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)

# NEW: Top Songs Table
class TopSong(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    artist = db.Column(db.String(100), nullable=False)
    # This links the song to a specific user's ID
    user_id = db.Column(db.Integer, nullable=False) 

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        
        new_user = User(username=username, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        else:
            flash('Incorrect username or password. Please try again.')
            
    return render_template('login.html')

# UPDATED: Fetch the user's songs when loading the dashboard
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    user = User.query.filter_by(username=session['username']).first()
    # Grab only the songs that belong to this logged-in user
    user_songs = TopSong.query.filter_by(user_id=user.id).all()
    
    return render_template('dashboard.html', username=user.username, top_songs=user_songs)

# NEW: Route to Add a Song
@app.route('/add_song', methods=['POST'])
def add_song():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        title = request.form.get('title')
        artist = request.form.get('artist')
        
        if title and artist:
            new_song = TopSong(title=title, artist=artist, user_id=user.id)
            db.session.add(new_song)
            db.session.commit()
            
    return redirect(url_for('dashboard'))

# NEW: Route to Delete a Song
@app.route('/delete_song/<int:song_id>', methods=['POST'])
def delete_song(song_id):
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        song = TopSong.query.get(song_id)
        
        # Security check: Make sure the song belongs to the person trying to delete it!
        if song and song.user_id == user.id:
            db.session.delete(song)
            db.session.commit()
            
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)