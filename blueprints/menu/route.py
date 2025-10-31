from flask import Blueprint, render_template, session

from decorators import login_required, role_required

menu_bp = Blueprint('menu_bp', __name__, template_folder= "templates")

@menu_bp.route('/')
@login_required
@role_required
def main_menu():
    return render_template('main_menu.html')