from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from flask_cors import CORS
import os, json, base64
from datetime import datetime
from github import Github, GithubException

# Configuration
REPO_NAME   = 'antoancms/subfeed'
APP_BRANCH  = 'main'
TOKEN_ENV   = 'GITHUB_TOKEN'
PASSWORD     = '8855'

# Initialize GitHub client
TOKEN = os.environ.get(TOKEN_ENV)
if not TOKEN:
    raise RuntimeError('GITHUB_TOKEN not set')
gh   = Github(TOKEN)
repo = gh.get_repo(REPO_NAME)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.urandom(24)
CORS(app)

# Load data.json from GitHub
def load_data():
    try:
        contents = repo.get_contents('data.json', ref=APP_BRANCH)
        raw = base64.b64decode(contents.content)
        return json.loads(raw)
    except GithubException as e:
        if e.status == 404:
            repo.create_file('data.json', 'Init data.json', json.dumps({}), branch=APP_BRANCH)
            return {}
        raise

# Save data.json back to GitHub
def save_data(data):
    content = json.dumps(data)
    try:
        contents = repo.get_contents('data.json', ref=APP_BRANCH)
        repo.update_file('data.json', 'Update data.json', content, contents.sha, branch=APP_BRANCH)
    except GithubException as e:
        if e.status == 404:
            repo.create_file('data.json', 'Create data.json', content, branch=APP_BRANCH)
        else:
            raise

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        if request.form.get('password') == PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('home'))
        return render_template('login.html', error="Incorrect password")
    return render_template('login.html')

@app.route('/home')
def home():
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    data = load_data()
    links = [{
        'id': u,
        'url': info['url'],
        'title': info.get('title',''),
        'desc': info.get('desc',''),
        'popup': bool(info.get('popup','')),
        'clicks': info.get('clicks',0),
        'log': info.get('log',{})
    } for u,info in data.items()]
    total_links  = len(links)
    total_clicks = sum(l['clicks'] for l in links)
    per_page     = request.args.get('per_page',10,type=int)
    if per_page not in [10,50,100,500]: per_page = 10
    page         = request.args.get('page',1,type=int)
    total_pages  = (total_links + per_page -1)//per_page
    start,end    = (page-1)*per_page, page*per_page
    return render_template('index.html',
                           links=links[start:end],
                           page=page,
                           per_page=per_page,
                           total_pages=total_pages,
                           total_links=total_links,
                           total_clicks=total_clicks,
                           edit_data=None)

@app.route('/create', methods=['GET','POST'])
def create():
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    if request.method == 'GET':
        return redirect(url_for('home'))
    data = load_data()
    cid = request.form['custom_id'].strip()
    if not cid:
        return "UTM Source required",400
    url = request.form['url'].strip()
    if '?utm_source=' not in url:
        url += f"?utm_source={cid}"
    prev = data.get(cid,{})
    data[cid] = {
        'url': url,
        'title': request.form.get('title',''),
        'desc': request.form.get('description',''),
        'popup': request.form.get('popup_text',''),
        'clicks': prev.get('clicks',0),
        'log': prev.get('log',{})
    }
    save_data(data)
    full_url = request.url_root.rstrip('/') + url_for('preview', id=cid)
    return render_template('result.html', full_url=full_url)

@app.route('/edit/<custom_id>', methods=['GET','POST'])
def edit(custom_id):
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    data = load_data()
    if request.method == 'POST':
        new_id  = request.form['custom_id'].strip()
        new_url = request.form['url'].strip()
        if '?utm_source=' not in new_url:
            new_url += f"?utm_source={new_id}"
        old = data.pop(custom_id,{})
        data[new_id] = {
            'url': new_url,
            'title': request.form.get('title',''),
            'desc': request.form.get('description',''),
            'popup': request.form.get('popup_text',''),
            'clicks': old.get('clicks',0),
            'log': old.get('log',{})
        }
        save_data(data)
        full_url = request.url_root.rstrip('/') + url_for('preview', id=new_id)
        return render_template('result.html', full_url=full_url)
    rec = data.get(custom_id)
    if not rec:
        return "Not found",404
    all_links = [{'id':u,**info} for u,info in data.items()]
    return render_template('index.html',
                           links=all_links[:10],
                           page=1,
                           per_page=10,
                           total_pages=(len(all_links)+9)//10,
                           total_links=len(all_links),
                           total_clicks=sum(i['clicks'] for i in all_links),
                           edit_data={'custom_id':custom_id, **rec})

@app.route('/delete/<custom_id>', methods=['POST'])
def delete(custom_id):
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    data = load_data()
    data.pop(custom_id,None)
    save_data(data)
    return redirect(url_for('home'))

@app.route('/p/<path:id>')
def preview(id):
    utm = id
    data = load_data()
    if utm in data:
        info = data[utm]
        info['clicks'] += 1
        today = datetime.now().strftime('%Y-%m-%d')
        info['log'][today] = info['log'].get(today,0) + 1
        save_data(data)
        return render_template('og_page.html', **info, request=request)
    return redirect(url_for('index'))

@app.route('/api/popup/<path:utm>')
def popup(utm):
    data = load_data()
    return jsonify({'text': data.get(utm, {}).get('popup','')})

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)))
