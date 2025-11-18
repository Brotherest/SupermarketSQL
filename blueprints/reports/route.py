from flask import Blueprint, render_template, request
import json
import os
from database.sql_provider import SQLProvider
from decorators import login_required, role_required
from .model_route import model_report_route, model_add_report

reports_bp = Blueprint('reports_bp', __name__, template_folder='templates')


@reports_bp.route('/reports', methods=['GET'])
@login_required
@role_required
def report_handler():
    return render_template("report_input.html")


@reports_bp.route('/reports', methods=['POST'])
@login_required
@role_required
def report_result_handler():
    user_data = request.form
    print(f"DEBUG: Search request for date: {user_data.get('report_date')}")

    with open("data/dbconfig.json") as f:
        db_config = json.load(f)

    provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

    try:
        res_info = model_report_route(db_config, user_data, provider)
        print(f"DEBUG: Model result - status: {res_info.status}, results: {len(res_info.result)}")

        if res_info.status:
            if res_info.result:
                for row in res_info.result:
                    row['ID отчета'] = row.pop('report_id', '')
                    row['Дата поставки'] = row.pop('supply_date', '')
                    row['Общая сумма'] = f"{row.pop('total_amount', 0)} ₽"

                # Получаем месяц из выбранной даты для заголовка
                selected_date = user_data.get('report_date', '')
                if selected_date:
                    from datetime import datetime
                    try:
                        date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
                        month_name = date_obj.strftime('%B %Y')  # Например: "November 2025"
                    except:
                        month_name = selected_date[:7]  # YYYY-MM
                else:
                    month_name = "неизвестный период"

                return render_template("report_result.html",
                                       reports=res_info.result,
                                       selected_date=month_name)
            else:
                return render_template("error.html",
                                       error_message=f"За выбранный период отчетов не найдено")
        else:
            return render_template("error.html",
                                   error_message=f"Ошибка при поиске: {res_info.error_message}")

    except Exception as e:
        print(f"Error in report_result_handler: {e}")
        return render_template("error.html",
                               error_message=f"Системная ошибка: {str(e)}")
    except Exception as e:
        print(f"Error in report_result_handler: {e}")
        return render_template("error.html",
                               error_message=f"Системная ошибка: {str(e)}")

@reports_bp.route('/reports/add', methods=['GET'])
@login_required
@role_required
def add_report_handler():
    return render_template("add_report.html")


@reports_bp.route('/reports/add', methods=['POST'])
@login_required
@role_required
def add_report_result_handler():
    user_data = request.form

    with open("data/dbconfig.json") as f:
        db_config = json.load(f)

    provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

    try:
        success, message = model_add_report(db_config, user_data, provider)

        if success:
            return render_template("add_report.html",
                                   success_message=message,
                                   form_data={})  # Очищаем форму при успехе
        else:
            # Сохраняем введенные данные для повторного заполнения
            return render_template("add_report.html",
                                   error_message=message,
                                   form_data=user_data)

    except Exception as e:
        print(f"Error in add_report_result_handler: {e}")
        error_msg = f"Критическая ошибка системы: {str(e)}"
        return render_template("add_report.html",
                               error_message=error_msg,
                               form_data=user_data)