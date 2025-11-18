from flask import Blueprint, render_template, request
import json
import os
from database.sql_provider import SQLProvider
from decorators import login_required, role_required
from .model_route import model_product_route

products_bp = Blueprint('products_bp', __name__, template_folder='templates')


@products_bp.route('/products', methods=['GET'])
@login_required
@role_required
def product_handler():
    return render_template("input_category.html")


@products_bp.route("/products", methods=['POST'])
@login_required
@role_required
def product_result_handler():
    user_data = request.form
    print("User data: ", user_data)

    with open("data/dbconfig.json") as f:
        db_config = json.load(f)

    provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

    try:
        res_info = model_product_route(db_config, user_data, provider)
        print("res_info.result = ", res_info.result)
        for row in res_info.result:
            row['Название товара'] = row.pop('prod_name', '')
            row['Единица измерения'] = row.pop('prod_measure', '')
            row['Цена'] = f"{row.pop('prod_price', 0)} ₽"

        if res_info.status:
            if res_info.result:
                prod_title = f'📦 Товары категории {user_data.get("prod_category", "N/A")}'

                return render_template("dynamic.html",
                                       prod_title=prod_title,
                                       products=res_info.result)
            else:
                return render_template("error.html",
                                       error_message="По вашему запросу товаров не найдено")
        else:
            return render_template("error.html",
                                   error_message="При выполнении произошла ошибка. Проверьте правильность введенных данных.")

    except Exception as e:
        print(f"Error: {e}")
        return render_template("error.html",
                               error_message=f"Системная ошибка: {str(e)}")