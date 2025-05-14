from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from flask_cors import CORS
import json, os, shutil
from datetime import datetime

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = 'your_secret_key_here'
CORS(app)

# DATA STORAGE SETUP
data_file = os.path.join(app.root_path, 'data.json')
template_file = os.path.join(app.root_path, 'data_template.json')
if not os.path.exists(data_file):
    if os.path.exists(template_file): shutil.copyfile(template_file, data_file)
    else:
        with open(data_file, 'w') as f:
            json.dump({}, f)

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        if request.form.get('password') == '8855':
            session['authenticated'] = True
            return redirect(url_for('home'))
        return render_template('login.html', error="Incorrect password")
    return render_template('login.html')

@app.route('/home')
def home():
    if not session.get('authenticated'): return redirect(url_for('index'))
    with open(data_file) as f: data = json.load(f)
    links = []
    for utm, info in data.items():
        links.append({
            'id': utm,
            'url': info.get('url'),
            'title': info.get('title',''),
            'desc': info.get('desc',''),
            'popup': bool(info.get('popup','')),
            'clicks': info.get('clicks',0),
            'log': info.get('log',{})
        })
    per_page = request.args.get('per_page',10,type=int)
    if per_page not in [10,50,100,500]: per_page=10
    page = request.args.get('page',1,type=int)
    total = len(links)
    total_pages = (total + per_page -1)//per_page
    start,end = (page-1)*per_page, page*per_page
    return render_template('index.html', links=links[start:end], page=page,
                           per_page=per_page, total_pages=total_pages, edit_data=None)

@app.route('/create', methods=['POST'])
def create():
    if not session.get('authenticated'): return redirect(url_for('index'))
    with open(data_file) as f: data = json.load(f)
    custom_id = request.form.get('custom_id','').strip()
    if not custom_id: return "UTM Source required",400
    url = request.form['url']
    if '?utm_source=' not in url: url += f"?utm_source={custom_id}"
    prev = data.get(custom_id,{})
    data[custom_id] = {
        'url':url,
        'title':request.form.get('title',''),
        'desc':request.form.get('description',''),
        'popup':request.form.get('popup_text',''),
        'clicks':prev.get('clicks',0),
        'log':prev.get('log',{})
    }
    with open(data_file,'w') as f: json.dump(data,f)
    return render_template('result.html', full_url=request.url_root+url_for('preview', id=custom_id))

@app.route('/edit/<custom_id>')
def edit(custom_id):
    if not session.get('authenticated'): return redirect(url_for('index'))
    with open(data_file) as f: data = json.load(f)
    if custom_id not in data: return "Not found",404
    record=data[custom_id]
    links=[{'id':u, 'url':i['url'], 'title':i.get('title',''),'desc':i.get('desc',''),'popup':bool(i.get('popup','')),'clicks':i.get('clicks',0),'log':i.get('log',{})} for u,i in data.items()]
    return render_template('index.html', links=links[:10], page=1, per_page=10, total_pages=(len(links)+9)//10,
                           edit_data={**record,'custom_id':custom_id})

@app.route('/delete/<custom_id>', methods=['POST'])
def delete(custom_id):
    if not session.get('authenticated'): return redirect(url_for('index'))
    with open(data_file) as f: data = json.load(f)
    data.pop(custom_id,None)
    with open(data_file,'w') as f: json.dump(data,f)
    return redirect(url_for('home'))

@app.route('/p/<id>')
def preview(id):
    with open(data_file) as f: data = json.load(f)
    if id in data:
        data[id]['clicks']=data[id].get('clicks',0)+1
        d=datetime.now().strftime('%Y-%m-%d')
        log=data[id].get('log',{})
        log[d]=log.get(d,0)+1
        data[id]['log']=log
        with open(data_file,'w') as f: json.dump(data,f)
        return render_template('og_page.html',**data[id],request=request)
    return redirect(url_for('index'))

@app.route('/api/popup/<utm>')
def get_popup_text(utm):
    with open(data_file) as f: data=json.load(f)
    return jsonify({'text':data.get(utm,{}).get('popup','')})

if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
