from dataclasses import dataclass
from itertools import product

from database.select import select_dict
from cache.redis_cache import RedisCache

@dataclass
class TicketInfoResponse:
    result: list
    error_message: str
    status: bool


def model_flight_route(db_config, user_input_data, sql_provider, cache_config):
    """
    Получает товары из БД по категории, кладёт их в Redis.
    Каждый товар хранится под ключом product:<prod_id>:info
    В info сохраняется prod_max (склад), цена, категория и имя.
    """
    error_message = ''

    # Проверка обязательных полей
    required_fields = ['product_category']
    for field in required_fields:
        if not user_input_data.get(field):
            error_message = f"Не заполнено обязательное поле: {field}"
            return TicketInfoResponse([], error_message=error_message, status=False)

    # Получаем SQL
    _sql = sql_provider.get(
        'user_product.sql',
        product_category='%s'
    )
    params = (user_input_data['product_category'],)

    # Извлекаем данные
    result = select_dict(db_config, _sql, params)
    if not result:
        return TicketInfoResponse([], error_message="Товары не найдены", status=False)

    # Redis
    redis_conn = RedisCache(cache_config["redis"])
    ttl = cache_config.get("ttl", 300)

    # Сохраняем каждый товар в Redis
    for product in result:
        p_id = product.get("prod_id")
        info_key = f"product:{p_id}:info"

        info_value = {
            "prod_id": p_id,
            "prod_name": product.get("prod_name"),
            "prod_measure": product.get("prod_measure"),
            "prod_price": product.get("prod_price"),
            "prod_category": product.get("prod_category"),
            "prod_max": product.get("prod_max", 0)  # остаток на складе
        }

        redis_conn.set_value(info_key, info_value, ttl)

    return TicketInfoResponse(result, error_message="", status=True)


def model_update_stock(db_config, product_data, sql_provider):
    """
    Вычитает количество товара из prod_max в БД.
    prod_id — id товара
    amount — количество для вычитания
    Возвращает TicketInfoResponse с статусом и сообщением об ошибке.
    """
    error_message = ''
    required_fields = ['prod_id', 'amount']
    for field in required_fields:
        if field not in product_data or product_data[field] is None:
            error_message = f"Не заполнено обязательное поле: {field}"
            print(error_message)
            return TicketInfoResponse([], error_message=error_message, status=False)

    prod_id = product_data['prod_id']
    amount = product_data['amount']
    print(prod_id, amount)
    _sql = sql_provider.get('update_stock.sql',
                            prod_id='%s',
                            amount='%s')
    params = (prod_id, amount)

    print(_sql, params)
    from database.DBcm import DBContextManager

    with DBContextManager(db_config) as cursor:
        if cursor is None:
            return TicketInfoResponse([], error_message="Ошибка подключения к БД", status=False)

        try:
            # UPDATE выполняется только если prod_max >= amount
            cursor.execute(_sql, params)

            cursor.execute("SELECT @p_error_message AS err")
            row = cursor.fetchone()

            if row and row[0]:
                # Здесь p_error_message содержит предупреждения, которые вернула процедура
                warning = row[0]

                return TicketInfoResponse(
                    [],
                    error_message=warning,
                    status=False
                )

                # Если err = NULL → успех
            return TicketInfoResponse(
                [{'message': ''}],
                error_message='',
                status=True
            )


        except Exception as e:

            return TicketInfoResponse(

                [],

                error_message=f"Ошибка БД: {str(e)}",

                status=False

            )
