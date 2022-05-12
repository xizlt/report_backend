import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django

django.setup()

from datetime import datetime, timedelta, date
from random import randrange

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from pymongo import MongoClient

from core import settings
from report.models import Region, Branch, Person, Nomenclature, Transaction, Gifts, GiftsName, DifferenceData
from tools.date import date_range
from tools.manager import TaskManager


@shared_task
def get_region():
    try:
        regions = TaskManager.get_region()
        for region in regions:
            Region.objects.get_or_create(
                id=region.region_id, name=region.name, alias=region.designation_name
            )
            print(region)
    except Exception as _:
        print(_.__str__())


@shared_task
def get_branch():
    branches = TaskManager.get_branch()
    for branch in branches:
        obj, created = Branch.objects.update_or_create(id=branch.branch_id, name=branch.name, code=branch.code_1c,
                                                       region=branch.region_id)


@shared_task
def get_person():
    counter_konkurs = 0
    counter_cashback = 0
    persons = TaskManager.get_person()
    for person in persons:
        _person, created = Person.objects.update_or_create(phone=person.phone_number,
                                                           loyalty_program=person.loyalty_program,
                                                           defaults=dict(user_id=person.customer_id,
                                                                         branch=person.branch_id if person.branch_id else 00,
                                                                         region=person.region_id if person.region_id else 00,
                                                                         name=f"{person.last_name} {person.first_name} {person.middle_name}",
                                                                         active=person.status == 'true',
                                                                         entity=person.entity))
        if created:
            if person.loyalty_program == "k":
                counter_konkurs += 1
            else:
                counter_cashback += 1

    DifferenceData.objects.create(models='person_k', difference=counter_konkurs, end_date=datetime.now().date())
    DifferenceData.objects.create(models='person_c', difference=counter_cashback, end_date=datetime.now().date())


@shared_task
def get_nomenclature():
    counter = 0
    nomenclatures = TaskManager.get_nomenclature()
    for nomenclature in nomenclatures:
        odj, created = Nomenclature.objects.update_or_create(code=nomenclature.code_1c,
                                                             defaults=dict(
                                                                 name=nomenclature.nom_name,
                                                                 price=nomenclature.price)
                                                             )
        if created:
            counter += 1

    DifferenceData.objects.create(models='nomenclature', difference=counter, end_date=datetime.now())


@shared_task
def get_gift_names():
    """
    Get all gifts name from api
    @return: None
    """
    names = TaskManager.get_gift_name()
    for i in names:
        GiftsName.objects.update_or_create(
            code=i.get('id', ''),
            defaults={
                'name': i.get('title', '')
            }
        )
    try:
        for i in MongoClient(settings.MONGO_URL, tz_aware=True).gifts.removed.find():
            GiftsName.objects.update_or_create(
                code=i.get('id', ''),
                defaults={
                    'name': i.get('title', '')
                },
                status=False
            )
    except Exception as _:
        pass


@shared_task
def get_gifts():
    end_date = datetime.now().date() - timedelta(days=1)
    begin_date = datetime.now().date()

    if not Gifts.objects.count():
        begin_date = date(2020, 3, 30)

    data_first = DifferenceData.objects.filter(models='gifts').order_by('-end_date').first()

    if data_first:
        begin_date = data_first.end_date + timedelta(days=1)

    if end_date < begin_date:
        end_date, begin_date = begin_date, end_date

    if not begin_date or not end_date:
        print("Ошибка")
        return "Ошибка"

    gifts = TaskManager.get_gifts(begin_date=begin_date, end_date=end_date)

    for gift in gifts:
        print(gift)
        person, created = Person.objects.get_or_create(phone=gift.phone_number,
                                                       loyalty_program=gift.loyalty_program,
                                                       defaults={
                                                           "phone":  gift.phone_number,
                                                           "name":   "",
                                                           "entity": "Удален",
                                                           "active": False,
                                                           "branch": 0,
                                                           "region": 0
                                                       })

        Gifts.objects.create(count=gift.count,
                             phone=gift.phone_number,
                             gift_id=gift.gift_id,
                             nominal=gift.nominal,
                             created=gift.date,
                             loyalty_program=gift.loyalty_program,
                             user=person
                             )

    DifferenceData.objects.create(models='gifts', difference=len(gifts), end_date=end_date)


@shared_task
def get_transactions_list(begin_date=None, end_date=None):
    """
    OPERATION_TYPE = {
    "expense": 0,
    "receipt": 1
    }

    EVENT_TYPE = {
    "scanning":      1,
    "canceling":     2,
    "buying":        3,
    "manual":        4,
    "transfer":      5,
    "cash_buying":   13,
    "cash_manual":   14,
    "cash_transfer": 15,
    }
    """
    counter = 0

    if not begin_date or not end_date:
        pass

    end_date = datetime.now().date() - timedelta(days=1)
    begin_date = datetime.now().date()

    if not Transaction.objects.first():
        begin_date = date(2020, 3, 30)

    data_first = DifferenceData.objects.filter(models='transaction').order_by('-end_date').first()

    if data_first:
        begin_date = data_first.end_date + timedelta(days=1)

    if end_date < begin_date:
        end_date, begin_date = begin_date - timedelta(days=1), end_date

    if not begin_date or not end_date:
        print("Ошибка")
        return "Ошибка"

    for dt in date_range(begin_date, end_date):
        transactions = TaskManager.get_transaction(begin_date=dt, end_date=dt)
        for i in transactions:
            print(i)
            if i['currency'] == '001':
                loyalty_program = 'k'
            else:
                loyalty_program = 'c'

            try:
                Person.objects.get(phone=int(i['_id']['phone_number']), loyalty_program=loyalty_program)
            except ObjectDoesNotExist as _:
                Person.objects.create(user_id=randrange(111111111, 999999999),
                                      phone=int(i['_id']['phone_number']),
                                      branch=00,
                                      region=Region.objects.get(alias=i['_id']['region']).id,
                                      name='',
                                      loyalty_program=loyalty_program,
                                      active=False,
                                      entity='Удален')

            Transaction.objects.create(
                date=i['_id']['date'],
                phone=i['_id']['phone_number'],
                code_1c=i['_id']['code_1c'],
                operation_type=i['_id']['operation_type'],
                region=i['_id']['region'],
                event_type=i['_id']['event_type'],
                bonuses=i['bonuses'],
                count=i['num_transactions'],
                currency=i['currency'],
                user=Person.objects.get(phone=int(i['_id']['phone_number']), loyalty_program=loyalty_program)
            )
            counter += 1

    DifferenceData.objects.create(models='transaction', difference=counter, end_date=end_date)
