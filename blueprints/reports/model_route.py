from dataclasses import dataclass
from database.select import select_dict
from database.DBcm import DBContextManager
from pymysql.err import OperationalError, ProgrammingError
import decimal
from datetime import datetime


@dataclass
class ReportInfoResponse:
    result: list
    error_message: str
    status: bool


def model_report_route(db_config, user_input_data, sql_provider):
    error_message = ''

    if 'report_date' not in user_input_data:
        result = []
        return ReportInfoResponse(result, error_message=error_message, status=False)

    try:
        # Парсим дату и извлекаем год и месяц
        from datetime import datetime
        date_obj = datetime.strptime(user_input_data['report_date'], '%Y-%m-%d')
        year = date_obj.year
        month = date_obj.month

        _sql = sql_provider.get('report_by_month.sql')
        params = (year, month)
        result = select_dict(db_config, _sql, params)

        if result:
            return ReportInfoResponse(result, error_message=error_message, status=True)
        else:
            return ReportInfoResponse([], error_message=error_message, status=True)

    except ValueError as e:
        return ReportInfoResponse([], error_message="Некорректный формат даты", status=False)
    except Exception as e:
        print(f"Error in model_report_route: {e}")
        return ReportInfoResponse([], error_message=str(e), status=False)

def validate_report_data(supply_date, total_amount):
    """Валидация данных перед добавлением"""
    errors = []

    if not supply_date:
        errors.append("Дата поставки обязательна для заполнения")
    else:
        try:
            # Проверяем корректность даты
            datetime.strptime(supply_date, '%Y-%m-%d')
        except ValueError:
            errors.append("Некорректный формат даты")

    if not total_amount:
        errors.append("Сумма обязательна для заполнения")
    else:
        try:
            amount = decimal.Decimal(total_amount)
            if amount < 0:
                errors.append("Сумма не может быть отрицательной")
            if amount > 1000000000:  # 1 миллиард
                errors.append("Сумма слишком большая")
        except (ValueError, decimal.InvalidOperation):
            errors.append("Некорректный формат суммы")

    return errors


def get_existing_reports_for_month(db_config, supply_date):
    """Получаем существующие отчеты за указанный месяц"""
    try:
        # Получаем год-месяц из даты (YYYY-MM)
        year_month = supply_date[:7]

        _sql = """
        SELECT report_id, supply_date, total_amount 
        FROM reports 
        WHERE DATE_FORMAT(supply_date, '%%Y-%%m') = %s
        ORDER BY supply_date DESC
        """

        result = select_dict(db_config, _sql, (year_month,))
        return result
    except Exception as e:
        print(f"Error getting existing reports: {e}")
        return []


def model_add_report(db_config, user_input_data, sql_provider):
    supply_date = user_input_data.get('supply_date')
    total_amount = user_input_data.get('total_amount')

    # Валидация данных
    validation_errors = validate_report_data(supply_date, total_amount)
    if validation_errors:
        return False, " | ".join(validation_errors)

    try:
        _sql = sql_provider.get('call_add_report.sql')
        params = (supply_date, decimal.Decimal(total_amount))

        with DBContextManager(db_config) as cursor:
            if cursor is None:
                return False, "Ошибка подключения к БД"

            # Выполняем процедуру
            cursor.execute(_sql, params)

            # Получаем результат процедуры отдельным запросом
            cursor.execute("SELECT @result as procedure_result")
            procedure_result = cursor.fetchone()

            if procedure_result and procedure_result[0]:
                result_message = procedure_result[0]

                # Проверяем, содержит ли результат сообщение об ошибке
                if 'Ошибка:' in result_message:
                    # Если это ошибка о существующем отчете, получаем детали
                    if 'уже существует' in result_message:
                        existing_reports = get_existing_reports_for_month(db_config, supply_date)
                        if existing_reports:
                            details = f" Найден отчет ID: {existing_reports[0]['report_id']} от {existing_reports[0]['supply_date']}"
                            result_message += details

                    return False, result_message
                else:
                    return True, result_message
            else:
                return False, "Не удалось получить результат выполнения процедуры"

    except ProgrammingError as e:
        error_code = e.args[0] if e.args else 'Unknown'
        error_msg = e.args[1] if len(e.args) > 1 else str(e)

        # Обработка ошибок процедуры
        if error_code == 1305:  # PROCEDURE does not exist
            return False, "Ошибка: Хранимая процедура 'AddReport' не найдена. Обратитесь к администратору."
        elif error_code == 1064:  # Syntax error
            return False, f"Ошибка синтаксиса в процедуре: {error_msg}"
        else:
            return False, f"Ошибка базы данных [{error_code}]: {error_msg}"

    except OperationalError as e:
        error_code = e.args[0] if e.args else 'Unknown'
        error_msg = e.args[1] if len(e.args) > 1 else str(e)
        return False, f"Ошибка подключения к базе данных [{error_code}]: {error_msg}"

    except decimal.InvalidOperation as e:
        return False, "Некорректный формат суммы"

    except ValueError as e:
        return False, f"Ошибка в данных: {str(e)}"

    except Exception as e:
        return False, f"Системная ошибка: {str(e)}"