from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from config import Config

# Инициализация приложения
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Контекстный процессор для добавления datetime во все шаблоны
@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

# Модели базы данных
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(200), default='default-avatar.jpg')
    notes = db.relationship('Note', backref='author', lazy=True)
    wishes = db.relationship('Wish', backref='author', lazy=True)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    is_private = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Wish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    is_fulfilled = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Finance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    is_income = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Инициализация базы данных
with app.app_context():
    db.create_all()
    if not User.query.first():
        users = [
            User(
                username='azamat',
                password=generate_password_hash('azamat123'),
                name='Азамат',
                avatar='azamat.jpg'
            ),
            User(
                username='inkara',
                password=generate_password_hash('inkara123'),
                name='Инкара',
                avatar='inkara.jpg'
            )
        ]
        db.session.add_all(users)
        db.session.commit()

# Главная страница
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    partner = User.query.filter(User.id != session['user_id']).first()
    
    data = {
        'user': user,
        'partner': partner,
        'shared_notes': Note.query.filter_by(is_private=False).order_by(Note.date_created.desc()).all(),
        'personal_notes': Note.query.filter_by(user_id=session['user_id'], is_private=True).order_by(Note.date_created.desc()).all(),
        'wishes': Wish.query.filter_by(user_id=session['user_id']).order_by(Wish.date_created.desc()).all(),
        'goals': Goal.query.order_by(Goal.deadline).all(),
        'upcoming_events': Event.query.filter(Event.date >= datetime.now()).order_by(Event.date).limit(5).all(),
        'finances': Finance.query.order_by(Finance.date.desc()).limit(5).all(),
        'memories': Memory.query.order_by(Memory.date_created.desc()).limit(4).all(),  # Добавлено
        'days_together': (datetime.now() - datetime(2023, 1, 1)).days
    }
    
    return render_template('home.html', **data)

# Аутентификация
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        
        if user and check_password_hash(user.password, request.form['password']):
            session.update({
                'user_id': user.id,
                'username': user.username,
                'name': user.name
            })
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('home'))
        
        flash('Неверное имя пользователя или пароль', 'danger')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Пользователь с таким именем уже существует', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            username=request.form['username'],
            password=generate_password_hash(request.form['password']),
            name=request.form['name']
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

# Заметки
@app.route('/notes/shared')
def shared_notes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    notes = Note.query.filter_by(is_private=False).order_by(Note.date_created.desc()).all()
    return render_template('notes/shared.html', notes=notes)

@app.route('/notes/personal')
def personal_notes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    notes = Note.query.filter_by(user_id=session['user_id'], is_private=True).order_by(Note.date_created.desc()).all()
    return render_template('notes/personal.html', notes=notes)

@app.route('/notes/add', methods=['GET', 'POST'])
def add_note():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        is_private = request.form.get('is_private') == 'on'
        
        if not title or not content:
            flash('Пожалуйста, заполните все обязательные поля', 'danger')
            return redirect(url_for('add_note'))
        
        note = Note(
            title=title,
            content=content,
            is_private=is_private,
            user_id=session['user_id']
        )
        db.session.add(note)
        db.session.commit()
        flash('Заметка успешно добавлена!', 'success')
        return redirect(url_for('personal_notes' if is_private else 'shared_notes'))
    
    return render_template('notes/add.html')

@app.route('/notes/<int:id>')
def view_note(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    note = Note.query.get_or_404(id)
    
    if note.is_private and note.user_id != session['user_id']:
        flash('У вас нет доступа к этой заметке', 'danger')
        return redirect(url_for('home'))
    
    return render_template('notes/view.html', note=note)

@app.route('/notes/edit/<int:id>', methods=['GET', 'POST'])
def edit_note(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    note = Note.query.get_or_404(id)
    
    if note.user_id != session['user_id']:
        flash('Вы не можете редактировать эту заметку', 'danger')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        note.title = request.form.get('title')
        note.content = request.form.get('content')
        note.is_private = request.form.get('is_private') == 'on'
        db.session.commit()
        flash('Заметка успешно обновлена!', 'success')
        return redirect(url_for('view_note', id=note.id))
    
    return render_template('notes/edit.html', note=note)

@app.route('/notes/delete/<int:id>')
def delete_note(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    note = Note.query.get_or_404(id)
    
    if note.user_id != session['user_id']:
        flash('Вы не можете удалить эту заметку', 'danger')
        return redirect(url_for('home'))
    
    db.session.delete(note)
    db.session.commit()
    flash('Заметка успешно удалена!', 'success')
    return redirect(url_for('personal_notes' if note.is_private else 'shared_notes'))
# Желания
@app.route('/wishes')
def list_wishes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    wishes = Wish.query.filter_by(user_id=session['user_id']).order_by(Wish.date_created.desc()).all()
    return render_template('wishes/list.html', wishes=wishes)

@app.route('/wishes/add', methods=['GET', 'POST'])
def add_wish():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        content = request.form['content']
        
        new_wish = Wish(
            content=content,
            user_id=session['user_id']
        )
        
        db.session.add(new_wish)
        db.session.commit()
        
        flash('Желание успешно добавлено!', 'success')
        return redirect(url_for('list_wishes'))
    
    return render_template('wishes/add.html')

@app.route('/wishes/toggle/<int:id>')
def toggle_wish(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    wish = Wish.query.get_or_404(id)
    
    if wish.user_id != session['user_id']:
        flash('Вы не можете изменить это желание', 'danger')
        return redirect(url_for('list_wishes'))
    
    wish.is_fulfilled = not wish.is_fulfilled
    db.session.commit()
    
    flash('Статус желания обновлен!', 'success')
    return redirect(url_for('list_wishes'))

@app.route('/wishes/delete/<int:id>')
def delete_wish(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    wish = Wish.query.get_or_404(id)
    
    if wish.user_id != session['user_id']:
        flash('Вы не можете удалить это желание', 'danger')
        return redirect(url_for('list_wishes'))
    
    db.session.delete(wish)
    db.session.commit()
    
    flash('Желание успешно удалено!', 'success')
    return redirect(url_for('list_wishes'))

# Цели
@app.route('/goals')
def list_goals():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    goals = Goal.query.order_by(Goal.deadline).all()
    return render_template('goals/list.html', goals=goals)

@app.route('/goals/add', methods=['GET', 'POST'])
def add_goal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        deadline_str = request.form['deadline']
        
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
        except ValueError:
            deadline = None
        
        new_goal = Goal(
            title=title,
            description=description,
            deadline=deadline,
            user_id=session['user_id']
        )
        
        db.session.add(new_goal)
        db.session.commit()
        
        flash('Цель успешно добавлена!', 'success')
        return redirect(url_for('list_goals'))
    
    return render_template('goals/add.html')

@app.route('/goals/toggle/<int:id>')
def toggle_goal(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    goal = Goal.query.get_or_404(id)
    
    if goal.user_id != session['user_id']:
        flash('Вы не можете изменить эту цель', 'danger')
        return redirect(url_for('list_goals'))
    
    goal.is_completed = not goal.is_completed
    db.session.commit()
    
    flash('Статус цели обновлен!', 'success')
    return redirect(url_for('list_goals'))

@app.route('/goals/delete/<int:id>')
def delete_goal(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    goal = Goal.query.get_or_404(id)
    
    if goal.user_id != session['user_id']:
        flash('Вы не можете удалить эту цель', 'danger')
        return redirect(url_for('list_goals'))
    
    db.session.delete(goal)
    db.session.commit()
    
    flash('Цель успешно удалена!', 'success')
    return redirect(url_for('list_goals'))

# Календарь
@app.route('/calendar')
def view_calendar():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    events = Event.query.order_by(Event.date).all()
    return render_template('calendar/view.html', events=events)

@app.route('/calendar/add', methods=['GET', 'POST'])
def add_event():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date_str = request.form['date']
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
        except ValueError:
            flash('Неверный формат даты и времени', 'danger')
            return redirect(url_for('add_event'))
        
        new_event = Event(
            title=title,
            description=description,
            date=date,
            user_id=session['user_id']
        )
        
        db.session.add(new_event)
        db.session.commit()
        
        flash('Событие успешно добавлено!', 'success')
        return redirect(url_for('view_calendar'))
    
    return render_template('calendar/add.html')

@app.route('/calendar/delete/<int:id>')
def delete_event(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    event = Event.query.get_or_404(id)
    
    if event.user_id != session['user_id']:
        flash('Вы не можете удалить это событие', 'danger')
        return redirect(url_for('view_calendar'))
    
    db.session.delete(event)
    db.session.commit()
    
    flash('Событие успешно удалено!', 'success')
    return redirect(url_for('view_calendar'))

# Галерея
@app.route('/gallery')
def view_gallery():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    memories = Memory.query.order_by(Memory.date_created.desc()).all()
    return render_template('gallery/view.html', memories=memories)

@app.route('/gallery/add', methods=['GET', 'POST'])
def add_memory():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files['file']
        
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            new_memory = Memory(
                title=title,
                description=description,
                file_path=filename,
                user_id=session['user_id']
            )
            
            db.session.add(new_memory)
            db.session.commit()
            
            flash('Воспоминание успешно добавлено!', 'success')
            return redirect(url_for('view_gallery'))
    
    return render_template('gallery/add.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Финансы
@app.route('/finance')
def finance_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    finances = Finance.query.order_by(Finance.date.desc()).all()
    
    total_income = sum(f.amount for f in finances if f.is_income)
    total_expenses = sum(f.amount for f in finances if not f.is_income)
    balance = total_income - total_expenses
    
    return render_template('finance/dashboard.html', 
                         finances=finances,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         balance=balance)

@app.route('/finance/add', methods=['GET', 'POST'])
def add_finance():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        description = request.form['description']
        category = request.form['category']
        is_income = 'is_income' in request.form
        
        new_finance = Finance(
            amount=amount,
            description=description,
            category=category,
            is_income=is_income,
            user_id=session['user_id']
        )
        
        db.session.add(new_finance)
        db.session.commit()
        
        flash('Запись успешно добавлена!', 'success')
        return redirect(url_for('finance_dashboard'))
    
    return render_template('finance/add.html')

@app.route('/finance/delete/<int:id>')
def delete_finance(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    finance = Finance.query.get_or_404(id)
    
    if finance.user_id != session['user_id']:
        flash('Вы не можете удалить эту запись', 'danger')
        return redirect(url_for('finance_dashboard'))
    
    db.session.delete(finance)
    db.session.commit()
    
    flash('Запись успешно удалена!', 'success')
    return redirect(url_for('finance_dashboard'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
