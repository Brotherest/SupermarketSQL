from flask import Blueprint, render_template, request
import json
import os
from database.sql_provider import SQLProvider
from decorators import login_required, role_required
from .model_route import model_add_report, model_get_report

reports_bp = Blueprint('reports_bp', __name__, template_folder='templates')

provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))


@reports_bp.route('/reports', methods=['GET'])
@login_required
@role_required
def reports_input():
    return render_template("report.html")


@reports_bp.route('/reports', methods=['POST'])
@login_required
@role_required
def reports_handler():
    year = request.form.get('year')
    month = request.form.get('month')
    action = request.form.get('action')

    try:
        year = int(year)
        month = int(month)
    except (TypeError, ValueError):
        return render_template("report.html", error_message="Неверный формат года или месяца")

    with open("data/dbconfig.json") as f:
        db_config = json.load(f)

    if action == 'add':
        result = model_add_report(db_config, year, month, provider)
        if result['status']:
            return render_template("report.html", success_message='Отчет успешно сформирован')
        else:
            return render_template("report.html", error_message=result['error'])

    elif action == 'get':
        result = model_get_report(db_config, year, month, provider)
        if result['status'] and result['data']:
            # Переименовываем ключи для отображения
            for row in result['data']:
                row['ID товара'] = row.pop('product_id', '')
                row['Название'] = row.pop('prod_name', '')
                row['Продано (шт)'] = row.pop('total_amount', '')
                row['Месяц'] = row.pop('report_month', '')
                row['Год'] = row.pop('report_year', '')

            return render_template("dynamic.html",
                                   prod_title=f"📊 Отчет по продажам за {month}/{year}",
                                   products=result['data'])
        else:
            return render_template("report.html", error_message="Данные за этот период не найдены")

    return render_template("report.html", error_message="Неизвестное действие")

