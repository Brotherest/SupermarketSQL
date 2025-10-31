from dataclasses import dataclass
from database.select import select_dict


@dataclass
class ProductInfoResponse:
    result: list
    error_message: str
    status: bool


def model_route(db_config, user_input_data, sql_provider):
    error_message = ''
    search_type = user_input_data.get("search_type")

    if search_type == "price":  # Запрос на имя
        if "user_price" not in user_input_data:
            result = []
            return ProductInfoResponse(result, error_message="Товар не указан", status=False)

        _sql = sql_provider.get('price.sql')
        params = (user_input_data['user_price'],)
        print("sql=", _sql)

    elif search_type == "type":  # Запрос на категорию
        if "user_type" not in user_input_data:
            result = []
            return ProductInfoResponse(result, error_message="ID товара не указано", status=False)

        _sql = sql_provider.get('type.sql')
        params = (user_input_data['user_type'],)
        print("sql=", _sql)

    else:
        result = []
        return ProductInfoResponse(result, error_message="Неизвестный тип поиска", status=False)

    try:
        result = select_dict(db_config, _sql, params)
        return ProductInfoResponse(result, error_message="", status=True)
    except Exception as e:
        error_message = f"Ошибка базы данных: {str(e)}"
        return ProductInfoResponse([], error_message=error_message, status=False)