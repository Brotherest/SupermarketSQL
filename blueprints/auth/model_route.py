import json
import os
from database.select import select_dict
from database.sql_provider import SQLProvider


def load_role_config():
    current_dir = os.path.dirname(__file__)
    config_path = os.path.join(current_dir, '..', '..', 'data', 'role_config.json')
    with open(config_path) as f:
        return json.load(f)


def authenticate_user(login, password):
    current_dir = os.path.dirname(__file__)
    db_config_path = os.path.join(current_dir, '..', '..', 'data', 'dbconfig.json')
    with open(db_config_path) as f:
        db_config = json.load(f)

    sql_path = os.path.join(current_dir, 'sql')
    provider = SQLProvider(sql_path)

    _sql = provider.get('user_auth.sql')
    users = select_dict(db_config, _sql, (login, password))

    return users[0] if users else None