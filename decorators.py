from functools import wraps
from flask import session, redirect, url_for, render_template
import json
import os


def load_role_config():
    current_dir = os.path.dirname(__file__)
    config_path = os.path.join(current_dir, 'data', 'role_config.json')
    with open(config_path) as f:
        return json.load(f)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth_bp.login_handler'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth_bp.login_handler'))

        user_role = session.get('user', {}).get('role')

        if not user_role:
            return redirect(url_for('auth_bp.login_handler'))

        role_config = load_role_config()

        #имя блюпринта из объекта функции
        blueprint = getattr(f, 'blueprint', None)
        if blueprint:
            blueprint_name = blueprint.name
        else:
            #из модуля
            module_parts = f.__module__.split('.')
            blueprint_name = module_parts[1].rstrip('s') + '_bp'

        # print(f"DEBUG ROLE CHECK: user_role = {user_role}")
        # print(f"DEBUG ROLE CHECK: blueprint_name = {blueprint_name}")
        # print(f"DEBUG ROLE CHECK: available for role = {role_config.get(user_role, [])}")
        # print(f"DEBUG ROLE CHECK: access granted = {blueprint_name in role_config.get(user_role, [])}")

        if user_role in role_config and blueprint_name in role_config[user_role]:
            return f(*args, **kwargs)
        else:
            return render_template("error.html",
                                   error_message=f"Доступ запрещен. Недостаточно прав. Роль: {user_role}, требуется доступ к: {blueprint_name}"), 403

    return decorated_function