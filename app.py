from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from flask_cors import CORS
import json, os, shutil
from datetime import datetime

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = 'your_secret_key_here'
CORS(app)  # Enables cross-origin API access for Blogger

# Use a template on first run, then persist data.json
base_dir     = app.root_path
data_file     = os.path.join(base_dir, 'data.json')
template_file = os.path.join(base_dir, 'data_template.json')
if not os.path.exists(data_file):
    if os.path.exists(template_file):
        shutil.copyfile(template_file, data_file)
    else:
        with open(data_file, 'w') as f:
            json.dump({}, f)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pwd = request.form.get('password')
        if pwd == '8855':
            session['authenticated'] = True
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Incorrect password")
    return render_template('login.html')

@app.route('/home')
def home():
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    # Load data
    with open(data_file, 'r') as f:
        data = json.load(f)
    # Build link records
    links = []
    for utm, info in data.items():
        links.append({
            'id': utm,
            'url': info.get('url'),
            'title': info.get('title',''),
            'desc': info.get('desc',''),
            'popup': bool(info.get('popup','')),
            'clicks': info.get('clicks', 0),
            'log': info.get('log', {})
        })
    # Pagination parameters
    per_page = request.args.get('per_page', default=10, type=int)
    if per_page not in [10, 50, 100, 500]:
        per_page = 10
    page = request.args.get('page', default=1, type=int)
    total = len(links)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    links_page = links[start:end]
    return render_template('index.html', links=links_page, page=page, per_page=per_page, total_pages=total_pages, edit_data=None)

@app.route('/create', methods=['POST'])
def create():
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    with open(data_file, 'r') as f:
        data = json.load(f)

    custom_id = request.form.get('custom_id', '').strip()
    if not custom_id:
        return "❌ UTM Source is required.", 400

    target_url = request.form['url']
    if '?utm_source=' not in target_url:
        target_url += f"?utm_source={custom_id}"

    # Merge new fields, preserve stats/log
    prev = data.get(custom_id, {})
    data[custom_id] = {
        'url': target_url,
        'title': request.form.get('title',''),
        'desc': request.form.get('description',''),
        'image': request.form.get('image',''),
        'popup': request.form.get('popup_text',''),
        'clicks': prev.get('clicks', 0),
        'log': prev.get('log', {})
    }

    with open(data_file, 'w') as f:
        json.dump(data, f)

    full_url = request.url_root.rstrip('/') + url_for('preview', id=custom_id)
    return render_template('result.html', full_url=full_url)

@app.route('/edit/<custom_id>')
def edit(custom_id):
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    # Load and validate record
    with open(data_file, 'r') as f:
        data = json.load(f)
    if custom_id not in data:
        return "❌ Link not found.", 404
    record = data[custom_id]
    # Prepare links with same pagination defaults
    links = []
    for utm, info in data.items():
        links.append({
            'id': utm,
            'url': info.get('url'),
            'title': info.get('title',''),
            'desc': info.get('desc',''),
            'popup': bool(info.get('popup','')),
            'clicks': info.get('clicks', 0),
            'log': info.get('log', {})
        })
    per_page, page = 10, 1
    total = len(links)
    total_pages = (total + per_page - 1) // per_page
    links_page = links[0:per_page]
    return render_template('index.html', links=links_page, page=page, per_page=per_page, total_pages=total_pages,
                           edit_data={
                               'custom_id': custom_id,
                               'url': record.get('url',''),
                               'title': record.get('title',''),
                               'desc': record.get('desc',''),
                               'popup': record.get('popup',''),
                               'clicks': record.get('clicks',0),
                               'log': record.get('log',{})
                           })

@app.route('/delete/<custom_id>', methods=['POST'])
def delete(custom_id):
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    with open(data_file, 'r') as f:
        data = json.load(f)
    if custom_id in data:
        del data[custom_id]
        with open(data_file, 'w') as f:
            json.dump(data, f)
    return redirect(url_for('home'))

@app.route('/p/<id>')
def preview(id):
    with open(data_file, 'r') as f:
        data = json.load(f)
    if id in data:
        data[id]['clicks'] = data[id].get('clicks', 0) + 1
        today = datetime.now().strftime('%Y-%m-%d')
        log = data[id].get('log', {})
        log[today] = log.get(today, 0) + 1
        data[id]['log'] = log
        with open(data_file, 'w') as f:
            json.dump(data, f)
        return render_template('og_page.html', **data[id], request=request)
    return redirect(url_for('index'))

@app.route('/api/popup/<utm>')
def get_popup_text(utm):
    with open(data_file, 'r') as f:
        data = json.load(f)
    return jsonify({ 'text': data.get(utm, {}).get('popup','') })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
