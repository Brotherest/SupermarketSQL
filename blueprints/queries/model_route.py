from dataclasses import dataclass
from database.select import select_dict


@dataclass
class ProductInfoResponse:
    result: list
    error_message: str
    status: bool


def model_product_route(db_config, user_input_data, sql_provider):
    error_message = ''

    if 'prod_category' not in user_input_data:
        print("user_input_data=", user_input_data)
        result = []
        return ProductInfoResponse(result, error_message=error_message, status=False)

    _sql = sql_provider.get('product.sql', prod_category='%s')
    print("sql=", _sql)
    params = (user_input_data['prod_category'],)
    result = select_dict(db_config, _sql, params)

    if result:
        return ProductInfoResponse(result, error_message=error_message, status=True)

    return ProductInfoResponse([], error_message=error_message, status=False)