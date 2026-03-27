from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Servidor funcionando"

import os

app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))