from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

# =================== MODELS ===================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(10))  # 'student' or 'teacher'

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    student_id = db.Column(db.Integer)
    assignment_id = db.Column(db.Integer)

# =================== AUTH ===================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        if User.query.filter_by(username=username).first():
            flash("Username already exists.")
            return redirect(url_for('signup'))

        user = User(username=username, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please login.")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash("Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# =================== DASHBOARD ===================

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'teacher':
        return redirect(url_for('create_assignment'))
    else:
        return redirect(url_for('submit_assignment'))

# =================== TEACHER ROUTES ===================

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_assignment():
    if current_user.role != 'teacher':
        return "Unauthorized"

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        assignment = Assignment(title=title, description=description, teacher_id=current_user.id)
        db.session.add(assignment)
        db.session.commit()
        flash("Assignment Created!")

    return render_template('create_assignment.html')

@app.route('/submissions')
@login_required
def view_submissions():
    if current_user.role != 'teacher':
        return "Unauthorized"
    submissions = Submission.query.all()
    return render_template('view_submissions.html', submissions=submissions)

# =================== STUDENT ROUTES ===================

@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_assignment():
    if current_user.role != 'student':
        return "Unauthorized"

    assignments = Assignment.query.all()

    if request.method == 'POST':
        assignment_id = request.form['assignment_id']
        content = request.form['content']

        if not assignment_id:
            flash("Please select an assignment!")
            return render_template('submit_assignment.html', assignments=assignments)

        submission = Submission(
            content=content,
            student_id=current_user.id,
            assignment_id=assignment_id
        )
        db.session.add(submission)
        db.session.commit()
        flash("Assignment Submitted!")

    return render_template('submit_assignment.html', assignments=assignments)

# =================== MAIN ===================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
