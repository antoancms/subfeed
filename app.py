from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from flask_cors import CORS
import os, json, shutil
from datetime import datetime
from github import Github, GithubException
from urllib.parse import urlparse, urlunparse

# Configuration
REPO_NAME   = 'antoancms/subfeed'
APP_BRANCH  = 'main'
TOKEN_ENV   = 'GITHUB_TOKEN'   # set in Render env vars
PASSWORD    = '8855'

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.urandom(24)
CORS(app)

# Paths
base_dir      = app.root_path
data_file     = os.path.join(base_dir, 'data.json')
template_file = os.path.join(base_dir, 'data_template.json')

# Bootstrap data.json if missing
if not os.path.exists(data_file):
    if os.path.exists(template_file):
        shutil.copyfile(template_file, data_file)
    else:
        with open(data_file, 'w') as f:
            json.dump({}, f)

# GitHub push helper
def commit_data_json(msg="Update data.json"):
    token = os.environ.get(TOKEN_ENV)
    if not token:
        return
    gh   = Github(token)
    repo = gh.get_repo(REPO_NAME)
    path = 'data.json'
    content = open(data_file, 'r').read()
    try:
        file = repo.get_contents(path, ref=APP_BRANCH)
        repo.update_file(path, msg, content, file.sha, branch=APP_BRANCH)
    except GithubException as e:
        if e.status == 404:
            repo.create_file(path, msg, content, branch=APP_BRANCH)
        else:
            raise

# Save & commit
def save_data(d):
    with open(data_file, 'w') as f:
        json.dump(d, f)
    commit_data_json()

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
    with open(data_file, 'r') as f:
        data = json.load(f)
    links = []
    for utm, info in data.items():
        links.append({
            'id':      utm,
            'url':     info.get('url',''),
            'title':   info.get('title',''),
            'desc':    info.get('desc',''),
            'popup':   bool(info.get('popup','')),
            'image':   info.get('image',''),
            'clicks':  info.get('clicks',0),
            'log':     info.get('log',{})
        })
    total_links  = len(links)
    total_clicks = sum(l['clicks'] for l in links)
    per_page     = request.args.get('per_page', 10, type=int)
    if per_page not in [10,50,100,500]:
        per_page = 10
    page         = request.args.get('page', 1, type=int)
    total_pages  = (total_links + per_page - 1) // per_page
    start, end   = (page-1)*per_page, page*per_page
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
    with open(data_file, 'r') as f:
        data = json.load(f)
    cid       = request.form['custom_id'].strip()
    target    = request.form['url'].strip()
    title     = request.form.get('title','').strip()
    desc      = request.form.get('description','').strip()
    popup     = request.form.get('popup_text','').strip()
    image_url = request.form.get('image','').strip()
    if not cid:
        return "UTM Source required", 400
    if '?utm_source=' not in target:
        target += f"?utm_source={cid}"
    prev = data.get(cid, {})
    data[cid] = {
        'url':    target,
        'title':  title,
        'desc':   desc,
        'popup':  popup,
        'image':  image_url,
        'clicks': prev.get('clicks',0),
        'log':    prev.get('log',{})
    }
    save_data(data)
    full_url = request.url_root.rstrip('/') + url_for('preview', id=cid)
    return render_template('result.html', full_url=full_url)

@app.route('/edit/<custom_id>', methods=['GET','POST'])
def edit(custom_id):
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    with open(data_file, 'r') as f:
        data = json.load(f)
    if request.method == 'POST':
        new_id    = request.form['custom_id'].strip()
        new_url   = request.form['url'].strip()
        new_title = request.form.get('title','').strip()
        new_desc  = request.form.get('description','').strip()
        new_popup = request.form.get('popup_text','').strip()
        new_image = request.form.get('image','').strip()
        old = data.pop(custom_id, {})
        # append utm to base URL
        if '?utm_source=' not in new_url:
            new_url += f"?utm_source={new_id}"
        data[new_id] = {
            'url':    new_url,
            'title':  new_title,
            'desc':   new_desc,
            'popup':  new_popup,
            'image':  new_image,
            'clicks': old.get('clicks',0),
            'log':    old.get('log',{})
        }
        save_data(data)
        # redirect to copy-link page
        full_url = request.url_root.rstrip('/') + url_for('preview', id=new_id)
        return render_template('result.html', full_url=full_url)
    # GET: load edit form
    if custom_id not in data:
        return "Not found", 404
    rec = data[custom_id]
    # strip existing utm from URL for editing
    parsed = urlparse(rec.get('url',''))
    base_url = urlunparse(parsed._replace(query=''))
    rec['url'] = base_url
    all_links = [{ 'id':u, **info } for u,info in data.items()]
    return render_template('index.html',
                           links=all_links[:10],
                           page=1,
                           per_page=10,
                           total_pages=(len(all_links)+9)//10,
                           total_links=len(all_links),
                           total_clicks=sum(l['clicks'] for l in all_links),
                           edit_data={'custom_id':custom_id, **rec})

@app.route('/delete/<custom_id>', methods=['POST'])
def delete(custom_id):
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    with open(data_file, 'r') as f:
        data = json.load(f)
    data.pop(custom_id, None)
    save_data(data)
    return redirect(url_for('home'))

@app.route('/p/<path:id>')
def preview(id):
    utm = id
    with open(data_file, 'r') as f:
        data = json.load(f)
    if utm in data:
        info = data[utm]
        info['clicks'] = info.get('clicks',0) + 1
        today = datetime.now().strftime('%Y-%m-%d')
        log = info.get('log', {})
        log[today] = log.get(today,0) + 1
        info['log'] = log
        data[utm] = info
        save_data(data)
        return render_template('og_page.html', **info, request=request)
    return redirect(url_for('index'))

@app.route('/api/popup/<path:utm>')
def popup(utm):
    with open(data_file, 'r') as f:
        data = json.load(f)
    return jsonify({ 'text': data.get(utm, {}).get('popup','') })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
