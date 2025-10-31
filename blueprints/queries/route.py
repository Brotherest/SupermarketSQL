from flask import Blueprint, render_template, request
import json
import os
from database.select import select_dict
from database.sql_provider import SQLProvider
from model_route import model_route
from decorators import login_required, role_required

queries_bp = Blueprint('queries_bp', __name__, template_folder="templates")


@queries_bp.route('/queries', methods=['GET'])
@login_required
@role_required
def queries_handler():
    return render_template("input_queries.html")


@queries_bp.route("/queries", methods=['POST'])
@login_required
@role_required
def queries_result_handler():
    user_data = request.form
    print("User data: ", user_data)
    search_type = user_data.get("search_type")

    # Получаем конфигурацию БД и провайдер SQL
    with open("data/dbconfig.json") as f:
        db_config = json.load(f)

    provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

    try:
        res_info = model_route(db_config, user_data, provider)
        print("res_info.result = ", res_info.result)

        if res_info.status:
            if res_info.result:
                search_type = user_data.get("search_type")
                search_value = user_data.get("search_value")
                if search_type == "price":
                    search_value = user_data.get("user_price")
                    prod_title = f'Стоимость {search_value}'
                    for row in res_info.result:
                        row['Название продукта'] = row.pop('prod_name', '')
                        row['Стоимость'] = row.pop('prod_price', '')
                elif search_type == "bonus":
                    search_value = user_data.get("user_bonus")
                    prod_title = f'Бонусы пользователя {search_value}'
                    for row in res_info.result:
                        row['ID товара'] = row.pop('prod_id', '')
                        row['Название продукта'] = row.pop('prod_name', '')
                        row['Мера'] = row.pop('prod_measure', '')
                        row['Стоимость'] = row.pop('prod_price', '')
                        row['Категория товара'] = row.pop('prod_category', '')
                else:
                    prod_title = 'Результаты поиска'

                return render_template("dynamic.html",
                                       prod_title=prod_title,
                                       products=res_info.result)
            else:
                return render_template("error.html",
                                       error_message="По вашему запросу ничего не найдено")
        else:
            return render_template("error.html",
                                   error_message=f"Ошибка: {res_info.error_message}")

    except Exception as e:
        print(f"Error: {e}")
        return render_template("error.html",
                               error_message=f"Системная ошибка: {str(e)}")