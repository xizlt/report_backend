from datetime import datetime
from functools import wraps

from django.http import JsonResponse

from tools.date import is_date


def transaction_validate(func):
    @wraps(func)
    def wrap(request):
        params = {'date': "времени",
                  "code_1c": "кода товара",
                  "branch": "филиал",
                  "phone": "телефон",
                  "entity": "адрес",
                  }
        if not request.query_params.get('date'):
            return JsonResponse({"data": [], "status": False, "error": "Не задан параметр интервал времени"})
        if not request.query_params.get('code_1c') or request.query_params.get('code_1c') == 'null':
            return JsonResponse({"data": [], "status": False, "error": "Не заданы кода товаров"})
        if not request.query_params.get('branch'):
            return JsonResponse({"data": [], "status": False, "error": "Не задан параметр филиал"})
        if not request.query_params.get('phone'):
            return JsonResponse({"data": [], "status": False, "error": "Не задан параметр телефон"})
        if not request.query_params.get('entity'):
            return JsonResponse({"data": [], "status": False, "error": "Не задан параметр адрес"})

        dt = request.query_params.get('date').split(',') if request.query_params.get('date') != 'null' else None
        if dt is None:
            return JsonResponse({"data": [], "status": False, "error": "Не задан интервал времени"})
        if not is_date(dt[0].strip()) or not is_date(dt[1].strip()):
            return JsonResponse({"data": [], "status": False, "error": "Не правильный формат даты"})

        code_1c = request.query_params.get('code_1c').split(',') if request.query_params.get('code_1c') else list(
            request.query_params.get('code_1c'))

        branch = request.query_params.get('branch').split(',') if request.query_params.get('branch') != 'null' else None
        if branch is None:
            return JsonResponse({"data": [], "status": False, "error": "Не заданы филиалы"})

        phone = request.query_params.get('phone').split(',') if request.query_params.get('phone') != 'null' else None
        entity = request.query_params.get('entity').split(',') if request.query_params.get('entity') != 'null' else None

        start_date = dt[0]
        end_date = dt[1]

        return func(request, start_date, end_date, code_1c, branch, )

    return wrap


prepare_where = lambda x: tuple(x) if len(x) > 1 else f"('{x[0]}')"


def choose_model(start, end):
    d1 = datetime.strptime(start, "%Y-%m-%d")
    d2 = datetime.strptime(end, "%Y-%m-%d")
    dlt = (d2 - d1).days

    if 0 < dlt <= 6:
        return 'free'
    elif dlt == 7:
        return 'week'
    elif 0 < dlt <= 31:
        return 'day'
    elif 31 < dlt <= 365:
        return 'month'
    elif 364 < dlt <= 1000:
        return 'year'
