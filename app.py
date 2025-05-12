from flask import Flask, request, render_template, redirect, url_for, session
import json, uuid, os

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = 'your_secret_key_here'  # Replace with a secure secret key

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
        custom_id = uuid.uuid4().hex[:6]

    # Create or update existing entry
    data[custom_id] = {
        "url": request.form['url'],
        "title": request.form['title'],
        "desc": request.form['description'],
        "image": request.form['image'],
        "clicks": data.get(custom_id, {}).get("clicks", 0)
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
        with open(data_file, 'w') as f:
            json.dump(data, f)
        return render_template("og_page.html", **data[id], request=request)
    else:
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
