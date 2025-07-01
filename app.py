import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secret_key_1234'

# Vartotojų kodai ir vardai
users = {
    "A7g4M2k": "Aina_Jankūnaitė",
    "x9T2bLq": "Titas_Graževičius",
    "R3n7Yp5": "Simonas_Pileckas",
    "m6C1vXe": "Adrijus_Jankūnas",
    "K2w8Tz9": "Kipras_Šikšnelis"
}

admin_password = "Administrator"
admin_name = "By Arijus Photography"

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit per file

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        if code in users:
            session['user_code'] = code
            session['user_name'] = users[code]
            return redirect(url_for('upload'))
        elif code == admin_password:
            session['admin'] = True
            session['user_name'] = admin_name
            return redirect(url_for('admin'))
        else:
            flash('Neteisingas kodas.')
            return redirect(url_for('index'))
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_code' not in session and 'admin' not in session:
        return redirect(url_for('index'))

    if 'admin' in session:
        return redirect(url_for('admin'))

    user_name = session.get('user_name')
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], user_name)

    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    # Skaičiuojame jau įkeltas nuotraukas
    existing_files = os.listdir(user_folder)
    if request.method == 'POST':
        files = request.files.getlist('photos')
        if len(existing_files) + len(files) > 30:
            flash(f'Negalima įkelti daugiau kaip 30 nuotraukų. Šiuo metu turi {len(existing_files)}.')
            return redirect(request.url)

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(user_folder, filename))
        flash('Nuotraukos įkeltos sėkmingai.')
        return redirect(request.url)

    return render_template('upload.html', user_name=user_name, existing_files=existing_files)


@app.route('/admin')
def admin():
    if 'admin' not in session:
        return redirect(url_for('index'))

    user_folders = os.listdir(app.config['UPLOAD_FOLDER'])
    all_photos = {}
    for folder in user_folders:
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        photos = os.listdir(folder_path)
        all_photos[folder] = photos

    user_name = session.get('user_name')
    return render_template('admin.html', all_photos=all_photos, user_name=user_name)


@app.route('/uploads/<user>/<filename>')
def uploaded_file(user, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], user), filename)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
