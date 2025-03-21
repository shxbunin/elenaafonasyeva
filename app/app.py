from flask import Flask, render_template
import json

app = Flask(__name__)

@app.route('/')
def index():
    with open('static/d.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    return render_template("index.html", a=data)

if __name__ == '__main__':
    app.run()