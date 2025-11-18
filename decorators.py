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

        blueprint = getattr(f, 'blueprint', None)
        if blueprint:
            blueprint_name = blueprint.name
        else:
            module_parts = f.__module__.split('.')
            if len(module_parts) > 1:
                blueprint_name = module_parts[1] + '_bp'
            else:
                blueprint_name = module_parts[0] + '_bp'

        print(f"🔍 DEBUG ROLE CHECK:")
        print(f"   User role: {user_role}")
        print(f"   Blueprint name: {blueprint_name}")
        print(f"   Available for role: {role_config.get(user_role, [])}")
        print(f"   Access granted: {blueprint_name in role_config.get(user_role, [])}")

        if user_role in role_config and blueprint_name in role_config[user_role]:
            return f(*args, **kwargs)
        else:
            return render_template("error.html",
                                   error_message=f"Доступ запрещен. Недостаточно прав. Ваша роль: {user_role}"), 403

    return decorated_function