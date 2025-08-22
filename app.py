from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
import openai
from datetime import date, datetime, timedelta

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecret"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///safe_space.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# OpenAI Integration
openai.api_key = os.getenv("OPENAI_API_KEY")

import os
from openai import OpenAI

client = OpenAI(api_key="sk-mnopabcd1234efghmnopabcd1234efghmnopabcd")

def get_openai_reply(message):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a kind and supportive mental health assistant. Keep responses short and compassionate."},
            {"role": "user", "content": message}
        ],
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()



# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(10))  # 'user', 'listener', 'admin'

class ListenerApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    status = db.Column(db.String(10), default='pending')

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer)
    receiver_id = db.Column(db.Integer)
    message = db.Column(db.Text)

class MoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    mood = db.Column(db.String(20))  # happy, okay, sad, etc.
    date = db.Column(db.Date, default=date.today)

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HabitEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'))
    date = db.Column(db.Date, default=date.today)

@app.route('/')
def home():
    print("Rendering home route")
    links = []
    links.append({'url': url_for('helpline'), 'label': 'Emergency Helpline'})  # <-- Add this line
    if 'user_id' in session:
        links.append({'url': url_for('journal'), 'label': 'Journal'})
        links.append({'url': url_for('habit_tracker'), 'label': 'Habit Tracker'})
        links.append({'url': url_for('apply_listener'), 'label': 'Apply to be Listener'})
        links.append({'url': url_for('chat_inbox'), 'label': 'Inbox'})
        bot_user = User.query.filter_by(username='Bot').first()
        if bot_user:
            links.append({'url': url_for('chat', receiver_id=bot_user.id), 'label': 'Chat with Bot'})
        if session['role'] == 'user':
            links.append({'url': url_for('select_listener'), 'label': 'Chat with Listener'})
        if session['role'] == 'listener':
            links.append({'url': url_for('select_listener_for_listener'), 'label': 'Chat with Listener'})
        if session['role'] == 'admin':
            links.append({'url': url_for('admin_panel'), 'label': 'Admin Panel'})
    else:
        links.append({'url': url_for('login'), 'label': 'Login'})
        links.append({'url': url_for('register'), 'label': 'Register'})
    return render_template('home.html', links=links)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or len(username) < 3:
            return "Username must be at least 3 characters long"
        if not password or len(password) < 6:
            return "Password must be at least 6 characters long"
        try:
            if User.query.filter_by(username=username).first():
                return "Username already exists"
            hashed = generate_password_hash(password)
            user = User(username=username, password=hashed, role='user')
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            return f"Registration failed: {str(e)}"
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or not password:
            return "Please enter both username and password"
        try:
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['role'] = user.role
                return redirect(url_for('home'))
            return "Invalid credentials"
        except Exception as e:
            return f"Login failed: {str(e)}"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/create-admin', methods=['GET', 'POST'])
def create_admin():
    if User.query.filter_by(role='admin').first():
        return "Admin already exists"
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or len(username) < 3:
            return "Username must be at least 3 characters long"
        if not password or len(password) < 6:
            return "Password must be at least 6 characters long"
        try:
            if User.query.filter_by(username=username).first():
                return "Username already exists"
            hashed = generate_password_hash(password)
            admin = User(username=username, password=hashed, role='admin')
            db.session.add(admin)
            db.session.commit()
            return "Admin created! <a href='/login'>Login</a>"
        except Exception as e:
            db.session.rollback()
            return f"Admin creation failed: {str(e)}"
    return render_template('create_admin.html')

@app.route('/apply-listener')
def apply_listener():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        existing = ListenerApplication.query.filter_by(user_id=session['user_id']).first()
        if not existing:
            new_app = ListenerApplication(user_id=session['user_id'])
            db.session.add(new_app)
            db.session.commit()
        # No form, just show confirmation
        return render_template('apply_listener.html', confirmation=True)
    except Exception as e:
        db.session.rollback()
        return render_template('apply_listener.html', error=str(e))

@app.route('/admin/listener-apps')
def admin_panel():
    if session.get('role') != 'admin':
        return "Access denied"
    try:
        apps = ListenerApplication.query.all()
        app_list = []
        for app in apps:
            user = User.query.get(app.user_id)
            if user:
                app_list.append({
                    'username': user.username,
                    'status': app.status,
                    'approve_url': url_for('approve_listener', app_id=app.id),
                    'reject_url': url_for('reject_listener', app_id=app.id)
                })
        return render_template('admin_panel.html', app_list=app_list)
    except Exception as e:
        return render_template('admin_panel.html', app_list=[], error=str(e))

@app.route('/admin/approve/<int:app_id>')
def approve_listener(app_id):
    if session.get('role') != 'admin':
        return "Access denied"
    try:
        app = ListenerApplication.query.get(app_id)
        if not app:
            return "Application not found"
        app.status = 'approved'
        user = User.query.get(app.user_id)
        if user:
            user.role = 'listener'
        db.session.commit()
        return redirect(url_for('admin_panel'))
    except Exception as e:
        db.session.rollback()
        return f"Approval failed: {str(e)}"

@app.route('/admin/reject/<int:app_id>')
def reject_listener(app_id):
    if session.get('role') != 'admin':
        return "Access denied"
    try:
        app = ListenerApplication.query.get(app_id)
        if not app:
            return "Application not found"
        app.status = 'rejected'
        db.session.commit()
        return redirect(url_for('admin_panel'))
    except Exception as e:
        db.session.rollback()
        return f"Rejection failed: {str(e)}"

@app.route('/chat/select')
def select_listener():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    listeners = User.query.filter_by(role='listener').all()
    return render_template('select_listener.html', listeners=listeners)

@app.route('/chat/inbox')
def chat_inbox():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    contacts = db.session.query(ChatMessage.sender_id, ChatMessage.receiver_id)\
        .filter((ChatMessage.sender_id == user_id) | (ChatMessage.receiver_id == user_id)).all()
    contact_ids = {s if s != user_id else r for s, r in contacts if s != r}
    users = User.query.filter(User.id.in_(contact_ids)).all()
    conversations = []
    for u in users:
        last_msg = ChatMessage.query.filter(
            ((ChatMessage.sender_id == user_id) & (ChatMessage.receiver_id == u.id)) |
            ((ChatMessage.sender_id == u.id) & (ChatMessage.receiver_id == user_id))
        ).order_by(ChatMessage.id.desc()).first()
        last_text = last_msg.message if last_msg else ""
        conversations.append({'username': u.username, 'chat_url': url_for('chat', receiver_id=u.id), 'last_text': last_text})
    return render_template('inbox.html', conversations=conversations)

@app.route('/chat/select-listener')
def select_listener_for_listener():
    if 'user_id' not in session or session.get('role') != 'listener':
        return redirect(url_for('login'))
    current_id = session['user_id']
    listeners = User.query.filter(User.role == 'listener', User.id != current_id).all()
    return render_template('select_listener.html', listeners=listeners)

@app.route('/chat/<int:receiver_id>', methods=['GET', 'POST'])
def chat(receiver_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    sender_id = session['user_id']
    if request.method == 'POST':
        message = request.form['message']
        msg = ChatMessage(sender_id=sender_id, receiver_id=receiver_id, message=message)
        db.session.add(msg)
        db.session.commit()
        bot_user = User.query.filter_by(username='Bot').first()
        if receiver_id == bot_user.id:
            reply = get_openai_reply(message)
            bot_reply = ChatMessage(sender_id=bot_user.id, receiver_id=sender_id, message=reply)
            db.session.add(bot_reply)
            db.session.commit()
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == sender_id) & (ChatMessage.receiver_id == receiver_id)) |
        ((ChatMessage.sender_id == receiver_id) & (ChatMessage.receiver_id == sender_id))
    ).all()
    chat_messages = [
        {'username': User.query.get(msg.sender_id).username, 'message': msg.message}
        for msg in messages
    ]
    return render_template('chat.html', chat_messages=chat_messages, receiver_id=receiver_id)

# Terminal-based Admin Promoter
def make_user_admin(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.role = 'admin'
            db.session.commit()
            print(f"User '{username}' is now an admin!")
        else:
            print(f"User '{username}' not found!")
# Updated app.py additions for Mood Tracker, Streak Counter, and Profile Page

# Helper to get streak
def calculate_streak(user_id):
    entries = MoodEntry.query.filter_by(user_id=user_id).order_by(MoodEntry.date.desc()).all()
    streak = 0
    today = date.today()
    for i, entry in enumerate(entries):
        expected = today - timedelta(days=i)
        if entry.date == expected:
            streak += 1
        else:
            break
    return streak

# Mood Tracker Route
@app.route('/mood', methods=['GET', 'POST'])
def mood_tracker():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    today_entry = MoodEntry.query.filter_by(user_id=user_id, date=date.today()).first()
    if request.method == 'POST':
        mood = request.form['mood']
        if today_entry:
            today_entry.mood = mood
        else:
            new_entry = MoodEntry(user_id=user_id, mood=mood)
            db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for('mood_tracker'))

    streak = calculate_streak(user_id)
    entries = MoodEntry.query.filter_by(user_id=user_id).order_by(MoodEntry.date.desc()).limit(7).all()
    return render_template('mood.html', today_entry=today_entry, streak=streak, moods=entries)

# Profile Page
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    mood_entries = MoodEntry.query.filter_by(user_id=user.id).order_by(MoodEntry.date.desc()).limit(7).all()
    streak = calculate_streak(user.id)
    return render_template('profile.html', user=user, entries=mood_entries, streak=streak)

@app.route('/journal', methods=['GET', 'POST'])
def journal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    if request.method == 'POST':
        content = request.form['content'].strip()
        if content:
            entry = JournalEntry(user_id=user_id, content=content)
            db.session.add(entry)
            db.session.commit()
            flash("Journal entry added!")
        return redirect(url_for('journal'))
    entries = JournalEntry.query.filter_by(user_id=user_id).order_by(JournalEntry.created_at.desc()).all()
    return render_template('journal.html', entries=entries)

@app.route('/habits', methods=['GET', 'POST'])
def habit_tracker():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    if request.method == 'POST':
        # Add new habit
        if 'habit_name' in request.form:
            name = request.form['habit_name'].strip()
            if name:
                db.session.add(Habit(user_id=user_id, name=name))
                db.session.commit()
                flash("Habit added!")
        # Mark habit as done for a specific date
        elif 'done_habit_id' in request.form and 'done_date' in request.form:
            habit_id = int(request.form['done_habit_id'])
            done_date_str = request.form['done_date']
            # Convert string to date object
            done_date = datetime.strptime(done_date_str, "%Y-%m-%d").date()
            if not HabitEntry.query.filter_by(habit_id=habit_id, date=done_date).first():
                db.session.add(HabitEntry(habit_id=habit_id, date=done_date))
                db.session.commit()
                flash("Habit marked as done!")
        return redirect(url_for('habit_tracker'))
    habits = Habit.query.filter_by(user_id=user_id).all()
    from datetime import date, timedelta
    week_dates = [(date.today() - timedelta(days=(date.today().weekday() - i) % 7)) for i in range(7)]
    week_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    habit_done = {}
    for habit in habits:
        done_map = {}
        for d in week_dates:
            done_map[d.isoformat()] = HabitEntry.query.filter_by(habit_id=habit.id, date=d).first() is not None
        habit_done[habit.id] = done_map
    return render_template(
        'habit_tracker.html',
        habits=habits,
        habit_done=habit_done,
        week_dates=week_dates,
        week_days=week_days
    )

@app.route('/helpline')
def helpline():
    helplines = [
        {"name": "National Emergency Number", "number": "999"},
        {"name": "Suicide Prevention Helpline", "number": "+8801779554391"},
        {"name": "Kaan Pete Roi", "number": "+8809612119911", "website": "https://kaanpeteroi.org/"},
        {"name": "Vent by Mindspace", "number": "+8809678678778", "website": "https://www.mindspacebd.com/"},
        {"name": "Tele-Mental Health Support (SHOJON)", "number": "09606119900"},
        {"name": "National Institute of Mental Health (NIMH)", "number": "+8802-223374409", "website": "https://nimh.gov.bd/"},
    ]
    return render_template('helpline.html', helplines=helplines)

@app.context_processor
def inject_links():
    links = []
    links.append({'url': url_for('helpline'), 'label': 'Emergency Helpline'})
    if 'user_id' in session:
        links.append({'url': url_for('journal'), 'label': 'Journal'})
        links.append({'url': url_for('habit_tracker'), 'label': 'Habit Tracker'})
        links.append({'url': url_for('apply_listener'), 'label': 'Apply to be Listener'})
        links.append({'url': url_for('chat_inbox'), 'label': 'Inbox'})
        bot_user = User.query.filter_by(username='Bot').first()
        if bot_user:
            links.append({'url': url_for('chat', receiver_id=bot_user.id), 'label': 'Chat with Bot'})
        if session['role'] == 'user':
            links.append({'url': url_for('select_listener'), 'label': 'Chat with Listener'})
        if session['role'] == 'listener':
            links.append({'url': url_for('select_listener_for_listener'), 'label': 'Chat with Listener'})
        if session['role'] == 'admin':
            links.append({'url': url_for('admin_panel'), 'label': 'Admin Panel'})
    else:
        links.append({'url': url_for('login'), 'label': 'Login'})
        links.append({'url': url_for('register'), 'label': 'Register'})
    return dict(links=links)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='Bot').first():
            db.session.add(User(username='Bot', password='', role='bot'))
            db.session.commit()
        if not User.query.filter_by(role='admin').first():
            print("No admin user found. Visit /create-admin or run this file directly to promote a user.")
        # Promote Afra to admin if exists
        make_user_admin('Afra')

    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'makeadmin':
        username = input("Enter username to make admin: ")
        make_user_admin(username)
    else:
        app.run(debug=True)
