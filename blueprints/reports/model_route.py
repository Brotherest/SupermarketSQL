from database.select import select_dict
from database.DBcm import DBContextManager


def model_add_report(db_config, year, month, sql_provider):
    _sql = sql_provider.get('add_report.sql', year='%s', month='%s')

    with DBContextManager(db_config) as cursor:
        if cursor is None:
            return {'status': False, 'error': 'Ошибка подключения к БД'}

        try:
            cursor.execute(_sql, (year, month))
            return {'status': True, 'error': ''}
        except Exception as e:
            return {'status': False, 'error': f'Ошибка БД: {str(e)}'}


def model_get_report(db_config, year, month, sql_provider):
    _sql = sql_provider.get('get_report.sql', year='%s', month='%s')
    result = select_dict(db_config, _sql, (year, month))

    if result:
        return {'status': True, 'data': result, 'error': ''}
    return {'status': False, 'data': [], 'error': 'Данные не найдены'}

