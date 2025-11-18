import json
import os
from flask import Flask, render_template

from blueprints.auth.route import auth_bp
from blueprints.menu.route import menu_bp
from blueprints.queries.route import products_bp
from blueprints.reports.route import reports_bp

app = Flask(__name__)

app.config.update(
    SECRET_KEY=os.urandom(24),
    SESSION_PERMANENT=False,
    PERMANENT_SESSION_LIFETIME=1800
)

app.register_blueprint(menu_bp)
app.register_blueprint(products_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(reports_bp)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('main_menu.html'), 404

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8080, debug=True)