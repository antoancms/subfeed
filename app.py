from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import json, uuid, os
from datetime import datetime

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = 'your_secret_key_here'

data_file = 'data.json'
if not os.path.exists(data_file):
    with open(data_file, 'w') as f:
        json.dump({}, f)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '8855':
            session['authenticated'] = True
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Incorrect password")
    return render_template('login.html')

@app.route('/home')
def home():
    if not session.get('authenticated'):
        return redirect(url_for('index'))

    with open(data_file, 'r') as f:
        data = json.load(f)

    links = [{"id": key, **value} for key, value in data.items()]
    return render_template('index.html', links=links)

@app.route('/create', methods=['POST'])
def create():
    if not session.get('authenticated'):
        return redirect(url_for('index'))

    with open(data_file, 'r') as f:
        data = json.load(f)

    custom_id = request.form.get('custom_id', '').strip()
    if not custom_id:
        return "❌ UTM Source is required.", 400

    # Append or merge utm_source properly
    url = request.form['url'].strip()
    if url:
        if 'utm_source=' not in url:
            url += ('&' if '?' in url else '?') + f"utm_source={custom_id}"
    else:
        url = data.get(custom_id, {}).get("url", "")

    data[custom_id] = {
        "url": url,
        "title": request.form['title'] or data.get(custom_id, {}).get("title", ""),
        "desc": request.form['description'] or data.get(custom_id, {}).get("desc", ""),
        "image": request.form['image'] or data.get(custom_id, {}).get("image", ""),
        "popup": request.form['popup_text'] or data.get(custom_id, {}).get("popup", ""),
        "clicks": data.get(custom_id, {}).get("clicks", 0),
        "log": data.get(custom_id, {}).get("log", {})
    }

    with open(data_file, 'w') as f:
        json.dump(data, f)

    full_url = request.url_root.rstrip('/') + url_for('preview', id=custom_id)
    return render_template("result.html", full_url=full_url)

@app.route('/edit/<custom_id>')
def edit(custom_id):
    if not session.get('authenticated'):
        return redirect(url_for('index'))

    with open(data_file, 'r') as f:
        data = json.load(f)

    if custom_id not in data:
        return "❌ Link not found.", 404

    return render_template("index.html", edit_data={"custom_id": custom_id, **data[custom_id]})

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

        return render_template("og_page.html", **data[id], request=request)
    else:
        return redirect(url_for('index'))

@app.route('/api/popup/<utm>')
def get_popup_text(utm):
    with open(data_file, 'r') as f:
        data = json.load(f)
    if utm in data:
        return jsonify({"text": data[utm].get("popup", "")})
    return jsonify({"text": ""})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
