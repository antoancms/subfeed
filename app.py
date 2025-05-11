from flask import Flask, request, render_template, redirect, url_for
import json, uuid, os

app = Flask(__name__)

data_file = 'data.json'
if not os.path.exists(data_file):
    with open(data_file, 'w') as f:
        json.dump({}, f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods=['POST'])
def create():
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    short_id = uuid.uuid4().hex[:6]
    data[short_id] = {
        "url": request.form['url'],
        "title": request.form['title'],
        "desc": request.form['description'],
        "image": request.form['image']
    }

    with open(data_file, 'w') as f:
        json.dump(data, f)

    return f"Link created: <a href='/p/{short_id}'>/p/{short_id}</a>"

@app.route('/p/<id>')
def preview(id):
    with open(data_file, 'r') as f:
        data = json.load(f)

    if id in data:
        return render_template("og_page.html", **data[id])
    else:
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
