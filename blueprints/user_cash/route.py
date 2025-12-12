from logging.config import dictConfig

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import json
import os
from database.sql_provider import SQLProvider
from decorators import login_required, role_required
from .model_route import model_flight_route, model_update_stock     # здесь он выдаёт товары
from cache.redis_cache import RedisCache

user_shop_bp = Blueprint('user_shop_bp', __name__, template_folder='templates')

# -------------------------------
# Конфиги
# -------------------------------
with open("data/dbconfig.json") as f:
    db_config = json.load(f)
with open("data/cache_config.json") as f:
    cache_config = json.load(f)

provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))
redis_conn = RedisCache(cache_config["redis"])
TTL = cache_config.get("ttl", 300)


# -------------------------------
# Страница поиска товаров
# -------------------------------
@user_shop_bp.route('/products_input', methods=['GET'])
@login_required
@role_required
def products_get():
    return render_template("product_search.html")


@user_shop_bp.route('/products_input', methods=['POST'])
@login_required
@role_required
def products_post():
    user_data = request.form.to_dict()
    if not user_data or not user_data.get('product_category'):
        flash("Введите категорию товара")
        return redirect(url_for("user_shop_bp.products_get"))

    session['last_search'] = {
        'product_category': user_data.get('product_category')
    }

    return redirect(url_for("user_shop_bp.product_result_get"))


# -------------------------------
# Результаты поиска
# -------------------------------
@user_shop_bp.route('/products_input/result', methods=['GET'])
@login_required
@role_required
def product_result_get():
    user_data = session.get('last_search')
    if not user_data or not user_data.get('product_category'):
        return redirect(url_for("user_shop_bp.products_get"))

    try:
        res_info = model_flight_route(db_config, user_data, provider, cache_config)

        if not res_info.status:
            return render_template("error.html", error_message=res_info.error_message)

        products = res_info.result

        user_info = session.get("user")
        user_id = user_info["user_id"]
        cart = redis_conn.get_cart(user_id)

        return render_template("product_list.html", products=products, cart=cart)

    except Exception as e:
        return render_template("error.html", error_message=f"Ошибка: {str(e)}")


# -------------------------------
# Добавление товара в корзину
# -------------------------------
@user_shop_bp.route("/add_to_cart/<int:prod_id>", methods=["POST"])
@login_required
@role_required
def add_to_cart(prod_id):
    user_info = session.get("user")
    user_id = user_info["user_id"]

    # Достаем данные товара
    info_key = f"product:{prod_id}:info"
    product_info = redis_conn.get_value(info_key)

    if not product_info:
        return render_template("error.html", error_message="Товар не найден")

    cart = redis_conn.get_cart(user_id)

    # считаем сколько данного товара уже лежит в корзине
    already = sum(1 for item in cart if item["product_id"] == prod_id)

    # максимальное количество со склада
    max_available = product_info["prod_max"]

    if already >= max_available:
        flash(f"❌ Нельзя добавить больше {max_available} шт. — столько есть на складе")
        return redirect(url_for("user_shop_bp.product_result_get"))

    cart.append({
        "product_id": prod_id,
        "info": product_info
    })

    redis_conn.set_cart(user_id, cart, TTL)
    flash("🛒 Товар добавлен в корзину!")

    return redirect(url_for("user_shop_bp.product_result_get"))


# -------------------------------
# Оформление покупки
# -------------------------------
@user_shop_bp.route("/checkout", methods=["POST"])
@login_required
@role_required
def checkout():
    user_info = session.get("user")
    user_id = user_info["user_id"]

    cart = redis_conn.get_cart(user_id)
    if not cart:
        flash("❌ Корзина пустая")
        return redirect(url_for("user_shop_bp.product_result_get"))

    # Считаем количество каждого товара
    count_by_prod = {}
    for item in cart:
        pid = item["product_id"]
        count_by_prod[pid] = count_by_prod.get(pid, 0) + 1

    # Проверяем наличие на складе
    for prod_id, count in count_by_prod.items():
        info_key = f"product:{prod_id}:info"
        product_info = redis_conn.get_value(info_key)

        if not product_info:
            flash(f"❌ Ошибка: товар {prod_id} не найден в кэше")
            return redirect(url_for("user_shop_bp.product_result_get"))

        if count > product_info["prod_max"]:
            flash(f"❌ На складе только {product_info['prod_max']} шт. товара {product_info['name']}")
            return redirect(url_for("user_shop_bp.product_result_get"))

    # Если все OK — вычитаем из БД
    for prod_id, count in count_by_prod.items():
        params = {
            "prod_id": prod_id,
            "amount": count
        }
        result = model_update_stock(db_config, params, provider)

        if not result:
            flash(f"❌ Ошибка обновления товара {prod_id} на складе")
            return redirect(url_for("user_shop_bp.product_result_get"))
        else:
            flash("🎉 Покупка успешно оформлена!")
            # Чистим корзину
            redis_conn.set_cart(user_id, [])
    return redirect(url_for("user_shop_bp.product_result_get"))


# -------------------------------
# Очистка корзины
# -------------------------------
@user_shop_bp.route("/clear_cart", methods=["POST"])
@login_required
@role_required
def clear_cart():
    user_info = session.get("user")
    if not user_info:
        flash("❌ Пользователь не найден")
        return redirect(url_for("user_shop_bp.product_result_get"))

    user_id = user_info["user_id"]
    redis_conn.set_cart(user_id, [])

    flash("🗑 Корзина очищена")
    return redirect(url_for("user_shop_bp.product_result_get"))
