import os, json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # pakeisk į saugų

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(f): return '.' in f and f.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS
def user_folder(u):
    path = os.path.join(UPLOAD_FOLDER, u)
    os.makedirs(path, exist_ok=True)
    return path

def load_json(n, default): 
    try: return json.load(open(n,'r',encoding='utf-8')) 
    except: return default
def save_json(n, d): json.dump(d, open(n,'w',encoding='utf-8'), indent=4)

@app.route('/')
def index():
    if 'username' not in session: return redirect(url_for('login'))
    users = load_json('participants.json', [])
    if session['username'] == 'admin':
        photos = {p['code']:os.listdir(user_folder(p['code'])) for p in users}
        return render_template('index.html', username='admin', participants=users, all_photos=photos)
    else:
        mypics = os.listdir(user_folder(session['username']))
        return render_template('index.html', username=session['username'], photos=mypics)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u,p = request.form['username'], request.form['password']
        for usr in load_json('users.json',[]):
            if usr['username']==u and usr['password']==p:
                session['username']=u; flash('Sveiki!','success'); return redirect('/')
        flash('Neteisingi duomenys','danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username',None)
    flash('Atsijungta','info'); return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload():
    if 'username' not in session: return redirect('/')
    f=request.files.get('photo')
    if not f or f.filename=='' or not allowed_file(f.filename):
        flash('Netinkamas failas','warning'); return redirect('/')
    fn=secure_filename(f.filename)
    f.save(os.path.join(user_folder(session['username']), fn))
    flash(f'Įkelta: {fn}','success'); return redirect('/')

@app.route('/delete_photo/<user>/<fn>', methods=['POST'])
def delete_photo(user, fn):
    if 'username' not in session: return redirect('/')
    if session['username']!='admin' and session['username']!=user:
        flash('Neįgalūs','danger'); return redirect('/')
    os.remove(os.path.join(user_folder(user),fn))
    flash('Ištrinta','success'); return redirect('/')

@app.route('/add_participant', methods=['POST'])
def add_participant():
    if session.get('username')!='admin': flash('Neįgalūs','danger'); return redirect('/')
    data=load_json('participants.json',[])
    u= request.form['code']; n=request.form['name']
    if not u or not n or any(p['code']==u for p in data):
        flash('Blogi duomenys','warning'); return redirect('/')
    data.append({'code':u,'name':n}); save_json('participants.json', data)
    us=load_json('users.json',[]); us.append({'username':u,'password':u})
    save_json('users.json',us)
    flash('Pridėta','success'); return redirect('/')

@app.route('/delete_participant/<code>', methods=['POST'])
def delete_participant(code):
    if session.get('username')!='admin': flash('Neįgalūs','danger'); return redirect('/')
    data=[p for p in load_json('participants.json',[]) if p['code']!=code]
    save_json('participants.json',data)
    us=[u for u in load_json('users.json',[]) if u['username']!=code]
    save_json('users.json',us)
    import shutil; shutil.rmtree(user_folder(code),ignore_errors=True)
    flash('Šalinta','success'); return redirect('/')

if __name__ == '__main__':
    port=int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, debug=True)
