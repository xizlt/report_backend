from django.db.models import Sum
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from report.models import Region, Person, Branch, Nomenclature, Transaction, Gifts, DifferenceData
from report.serializers import NomenclatureSerializer

from tools.data import transaction_validate
from tools.manager import TransactionManager


@api_view(('GET', 'OPTIONS'))
def articles_group(request):
    data = [{
        "id":       1,
        "name":     "Группа",
        "articles": ["00000", "00001"]
    }]
    return JsonResponse({"data": data})


class ArticlesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Nomenclature.objects.all()
    serializer_class = NomenclatureSerializer


@api_view(('GET',))
def get_branches(request):
    branches = [
        {"label":    r.name,
         "key":      r.id,
         "data":     r.name,
         "children": [{
             "label":     b.name,
             "key":       b.code,
             "region_id": b.region,
         } for b in Branch.objects.all() if b.region == r.id]
         } for r in Region.objects.filter().exclude(id=8)
    ]
    return JsonResponse({"data": branches})


@api_view(('GET', 'OPTIONS'))
@transaction_validate
def get_transactions(request, start_date, end_date, code_1c, branch):
    data = TransactionManager(start_date=start_date, end_date=end_date, code_1c=code_1c,
                              branch=branch).get_transaction_full()
    if not data:
        return JsonResponse({"data": [], "status": True, "error": ""})
    return JsonResponse({"data": list(data.values())})


@api_view(('GET', 'OPTIONS'))
def main_data_dashboard(request):

    diff = DifferenceData.objects.order_by('-end_date').all()
    gift = Gifts.objects.aggregate(count=Sum('count'))
    data = [
        {
            'title':       'Подарочные карты',
            'data':        gift["count"] or 0,
            'icon':        'pi-shopping-cart',
            'information': diff.filter(models='gifts').first().difference
        }, {
            'title':       'Участники F',
            'data':        Person.objects.filter(loyalty_program='k', active=True).count(),
            'icon':        'pi-android',
            'information': diff.filter(models='person_cashback').first().difference
        }, {
            'title':       'Участники C',
            'data':        Person.objects.filter(loyalty_program='c', active=True).count(),
            'icon':        'pi-euro',
            'information': diff.filter(models='person_konkurs').first().difference
            # 'information': diff.filter(models='cashback').aggregate(cnt=Coalesce(Sum('difference'), 0))['cnt']
        }, {
            'title':       'Всего отсканировано товаров',
            'data':        Transaction.objects.aggregate(count=Sum('count'))["count"] or 0,
            'icon':        'pi-qrcode',
            'information': diff.filter(models='transaction').first().difference
        }
    ]

    return JsonResponse({"data": data})


@api_view(('GET',))
@transaction_validate
def get_transactions_short(request, start_date, end_date, code_1c, branch):
    data = TransactionManager(start_date=start_date, end_date=end_date, code_1c=code_1c,
                              branch=branch).get_transaction_short()
    if not data:
        return JsonResponse({"data": [], "status": True, "error": ""})
    return JsonResponse({"data": data})


@api_view(('GET', 'OPTIONS'))
@transaction_validate
def get_transactions_chart(request, start_date, end_date, code_1c, branch):
    data = TransactionManager(start_date=start_date, end_date=end_date, code_1c=code_1c,
                              branch=branch).get_transaction_chart()
    if not data:
        return JsonResponse({"data": [], "status": True, "error": ""})
    return JsonResponse({"data": data})


@api_view(('POST',))
def black_list_refresh_view(request):
    token = RefreshToken(request.data.get('refresh_token'))
    token.blacklist()
    return Response("Successful Logout", status=status.HTTP_200_OK)
