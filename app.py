from flask import Flask, render_template, request, redirect, url_for, session, flash
import os, json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Pakeisk į kažką saugaus

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def user_upload_folder(username):
    path = os.path.join(app.config['UPLOAD_FOLDER'], username)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def load_users():
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_users(users):
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)

def load_participants():
    try:
        with open('participants.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_participants(participants):
    with open('participants.json', 'w', encoding='utf-8') as f:
        json.dump(participants, f, indent=4)

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    participants = load_participants()

    if username == 'admin':
        # Adminui rodom visų dalyvių nuotraukas
        all_photos = {}
        for participant in participants:
            user_folder = user_upload_folder(participant['code'])
            photos = os.listdir(user_folder) if os.path.exists(user_folder) else []
            all_photos[participant['code']] = photos
        return render_template('index.html', all_photos=all_photos, participants=participants, username=username)
    else:
        # Dalyviui rodom tik jo nuotraukos
        user_folder = user_upload_folder(username)
        photos = os.listdir(user_folder) if os.path.exists(user_folder) else []
        return render_template('index.html', photos=photos, username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        for user in users:
            if user['username'] == username and user['password'] == password:
                session['username'] = username
                flash('Prisijungėte sėkmingai!', 'success')
                return redirect(url_for('index'))
        flash('Neteisingas vartotojo vardas arba slaptažodis', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Atsijungėte', 'info')
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))

    file = request.files.get('photo')
    if not file or file.filename == '':
        flash('Nepasirinkta nuotrauka', 'warning')
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        flash('Netinkamas failo formatas', 'danger')
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    user_folder = user_upload_folder(session['username'])
    file.save(os.path.join(user_folder, filename))
    flash(f'Nuotrauka {filename} įkelta sėkmingai!', 'success')
    return redirect(url_for('index'))

@app.route('/delete_photo/<filename>', methods=['POST'])
def delete_photo(filename):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    user_folder = user_upload_folder(username)
    filepath = os.path.join(user_folder, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash('Nuotrauka ištrinta', 'success')
    else:
        flash('Nuotrauka nerasta', 'danger')
    return redirect(url_for('index'))

@app.route('/add_participant', methods=['POST'])
def add_participant():
    if 'username' not in session:
        return redirect(url_for('login'))

    if session['username'] != 'admin':
        flash('Neturite teisės pridėti dalyvių', 'danger')
        return redirect(url_for('index'))

    name = request.form.get('name')
    code = request.form.get('code')

    if not name or not code:
        flash('Vardas ir kodas būtini', 'warning')
        return redirect(url_for('index'))

    participants = load_participants()
    users = load_users()

    # Patikriname, ar dalyvis jau yra
    if any(p['code'] == code for p in participants):
        flash('Toks dalyvis jau egzistuoja', 'danger')
        return redirect(url_for('index'))

    # Pridedame dalyvį
    participants.append({'name': name, 'code': code})
    save_participants(participants)

    # Taip pat pridedame kaip vartotoją su slaptažodžiu (pats kodas yra ir username, slaptažodis toks pat)
    if not any(u['username'] == code for u in users):
        users.append({'username': code, 'password': code})
        save_users(users)

    flash(f'Dalyvis "{name}" pridėtas ir vartotojas sukurtas', 'success')
    return redirect(url_for('index'))

@app.route('/delete_participant/<code>', methods=['POST'])
def delete_participant(code):
    if 'username' not in session:
        return redirect(url_for('login'))

    if session['username'] != 'admin':
        flash('Neturite teisės šalinti dalyvių', 'danger')
        return redirect(url_for('index'))

    participants = load_participants()
    users = load_users()

    participants = [p for p in participants if p['code'] != code]
    users = [u for u in users if u['username'] != code]

    save_participants(participants)
    save_users(users)

    # Pašaliname dalyvio nuotraukų aplanką, jei egzistuoja
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], code)
    if os.path.exists(user_folder):
        import shutil
        shutil.rmtree(user_folder)

    flash('Dalyvis pašalintas kartu su vartotoju ir nuotraukomis', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
