from flask import Blueprint, render_template, request, session, redirect, url_for
from .model_route import authenticate_user

auth_bp = Blueprint('auth_bp', __name__, template_folder='templates')


@auth_bp.route('/login', methods=['GET'])
def login_handler():
    if 'user' in session:
        return redirect(url_for('menu_bp.main_menu'))
    return render_template("login.html")


@auth_bp.route('/login', methods=['POST'])
def login_result_handler():
    login = request.form.get('login')
    password = request.form.get('password')

    user = authenticate_user(login, password)

    if user:
        session['user'] = {
            'user_id': user['user_id'],
            'login': user['login'],
            'role': user['role']
        }
        return redirect(url_for('menu_bp.main_menu'))
    else:
        return render_template("login.html",
                               error_message="Неверный логин или пароль")


@auth_bp.route('/logout')
def logout_handler():
    session.pop('user', None)
    return redirect(url_for('auth_bp.login_handler'))