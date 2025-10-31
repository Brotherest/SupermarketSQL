import json
import os
from flask import Flask, render_template
from blueprints.menu.route import menu_bp
from blueprints.queries.route import queries_bp
from blueprints.auth.route import auth_bp

app = Flask(__name__)
app.secret_key = 'secret'

app.register_blueprint(menu_bp)
app.register_blueprint(queries_bp)
app.register_blueprint(auth_bp)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('main_menu.html'), 404

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5001, debug=True)