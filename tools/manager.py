from random import random

from django.db import connection
from django.db import connections
from psycopg2.extras import NamedTupleCursor
from pymongo import MongoClient

from core import settings
from report.models import Nomenclature
from tools.data import prepare_where


class TransactionManager:
    def __init__(self, start_date, end_date, code_1c, branch):
        self.start_date = start_date
        self.end_date = end_date
        self.code_1c = code_1c
        self.branch = branch

    def _prepare_sql_transaction_full(self):
        where = f"where tr.date between '{self.start_date}' and '{self.end_date}' and tr.code_1c in {prepare_where(self.code_1c)} "
        if self.branch:
            where += f"AND rp.branch in (select id from report_branch where code in {prepare_where(self.branch)} ) "
        return f"""
               select rp.phone, rr.name as region, coalesce(nullif(rb.name ,''),'Не определено') as filial,
               rp.name, rp.entity, sum(bonuses) as bonuses, sum(count) as count, tr.code_1c
               from report_transaction as tr
               join report_person rp on rp.id = tr.user_id
               join report_branch rb on rp.branch= rb.id
               join report_region rr on rp.region  = cast(rr.id AS INTEGER)
               {where}
               group by rp.phone, rr.name, rb.name, rp.name, rp.entity, tr.code_1c;
               """

    def _prepare_sql_transaction_short(self):
        where = f"where tr.date between '{self.start_date}' and '{self.end_date}' and tr.code_1c in {prepare_where(self.code_1c)} and tr.currency = '001' "
        if self.branch:
            where += f"AND rp.branch in (select id from report_branch where code in {prepare_where(self.branch)} ) "
        query = f"""
                    select tr.code_1c, sum(bonuses) as bonuses, sum(count) as count, count(DISTINCT(tr.user_id)) as entity
                    from report_transaction as tr
                    join report_person rp on rp.id = tr.user_id
                    left join report_branch rb on rp.branch= rb.id
                    left join report_region rr on rp.region  = cast(rr.id AS INTEGER)
                    {where}
                    group by tr.code_1c;
                    """
        return query

    def _prepare_sql_transaction_chart(self):
        where = f"where tr.date between '{self.start_date}' and '{self.end_date}' and tr.code_1c in {prepare_where(self.code_1c)} and tr.currency = '001' "

        if self.branch:
            where += f"AND rp.branch in (select id from report_branch where code in {prepare_where(self.branch)} ) "
        query = f"""
        select tr.code_1c, sum(bonuses) as bonuses, sum(count) as count, tr.date
        from report_transaction as tr
        join report_person rp on rp.id = tr.user_id
        join report_nomenclature as rn on rn.code = tr.code_1c
        {where}
        group by tr.code_1c, tr.date
        order by tr.code_1c, tr.date ASC;
        """
        return query

    @staticmethod
    def _fetch_data(query):
        with connection.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_transaction_full(self):
        data = {}
        query = self._prepare_sql_transaction_full()
        rows = self._fetch_data(query=query)
        for trn in rows:
            itm = {
                "key":      trn[0],
                "data":     {
                    "phone":        trn[0],
                    "branch":       trn[2],
                    "region":       trn[1],
                    "name":         trn[3],
                    "organisation": trn[4],
                    "bonus":        trn[5],
                    "count":        trn[6],
                    "articles":     [],
                },
                "children": []
            }
            if trn[0] in data.keys():
                data[trn[0]]['data']['bonus'] += trn[5]
                data[trn[0]]['data']['count'] += trn[6]
            else:
                data[trn[0]] = itm

            data[trn[0]]['data']['articles'].append(trn[7] + " ")
            data[trn[0]]["children"].append({
                "key":  random(),
                "data": {
                    "count":    trn[6],
                    "articles": trn[7],
                    "bonus":    trn[5]
                }
            })
        return data

    def get_transaction_short(self):
        data = []
        query = self._prepare_sql_transaction_short()
        for trn in self._fetch_data(query=query):
            data.append(
                {
                    "code_1c": trn[0],
                    "count":   trn[1],
                    "bonuses": trn[2],
                    "entity":  trn[3]
                }
            )
        return data

    def get_transaction_chart(self):
        query = self._prepare_sql_transaction_chart()
        rows = self._fetch_data(query=query)
        labels = sorted(list(set([i[3] for i in rows])))
        nomenclatures = Nomenclature.objects.filter(code__in=self.code_1c)
        data = {
            'total':  sum([i[2] for i in rows]),
            # 'model':  'free' if len(labels) < 7 else choose_model(self.start_date, self.end_date),
            'model':  'free',
            'labels': labels,
            'items':  []
        }
        items = {}
        for nmk in nomenclatures:
            items[nmk.code] = {
                'label': nmk.code,
                'name':  nmk.name,
                'data':  [0 for i in range(len(labels))],
                'sum': 0
            }
        for row in rows:
            ind = labels.index(row[3])
            items[row[0]]['data'][ind] = row[2]
            items[row[0]]['sum'] += row[2]

        data['items'] = sorted(list(items.values()), key=lambda d: d['sum'], reverse=True)
        return data


class TaskManager:
    @staticmethod
    def _prepare_sql_region():
        return """SELECT region_id, name, designation FROM tradearea_r"""

    @staticmethod
    def _prepare_sql_branch():
        return """SELECT name, code_1c, region_id, branch_id FROM tradearea_b"""

    @staticmethod
    def _prepare_sql_person():
        return """
       SELECT cc.phone_number, cc.first_name, cc.middle_name, cc.last_name, cc.boolean_flags #> '{enable,value}' as status,
        'konk' AS loyalty_program, tm.branch_id, tm.region_id, tc.name AS entity, cc.customer_id, cc.create_date
        FROM customer_customer as cc
        LEFT JOIN customer_addr_mtm_customer camc on cc.customer_id = camc.customer_id
        LEFT JOIN shipments_address sa on sa.address_id = camc.address_id
        LEFT JOIN tradearea_counterparty tc on tc.counterparty_id = sa.counterparty_id
        LEFT JOIN tradearea_manager tm on tm.manager_id = tc.manager_id
        WHERE camc.main = True and cc.boolean_flags #>> '{active,value}' = 'true'

        UNION ALL

        SELECT c.phone_number, '' as first_name, '' as middle_name, '' as last_name, cc.boolean_flags #> '{enable,value}' as status,
               'cashback' AS loyalty_program, tm.branch_id, tm.region_id, tc.name as entity, cc.customer_id, Date(now()) as create_date
        FROM cashback_cashbackprofile as cc
        LEFT JOIN customer_customer c on c.customer_id = cc.customer_id
        LEFT JOIN customer_addr_mtm_customer camc on c.customer_id = camc.customer_id
        LEFT JOIN shipments_address sa on sa.address_id = camc.address_id
        LEFT JOIN tradearea_counterparty tc on tc.counterparty_id = sa.counterparty_id
        LEFT JOIN tradearea_manager tm on tm.manager_id = tc.manager_id
        WHERE camc.main = True and cc.boolean_flags #>> '{enable,value}' = 'true'
        ORDER BY create_date DESC;
        """

    @staticmethod
    def _prepare_sql_nomenclature():
        return """SELECT nom_name, code_1c, price
        FROM shipments_nomenclature
        WHERE konk = true;"""

    @staticmethod
    def _prepare_sql_gifts(begin_date, end_date):
        if not begin_date or not end_date:
            exit(0)
        return f"""
        SELECT cc.phone_number, cg.nominal, gift_id, count(gift_id) AS count, DATE(created_at), 'konk' AS loyalty_program, cc.customer_id
        FROM customer_gif AS cg
        LEFT JOIN customer_customer cc ON cc.customer_id = cg.customer_id
        WHERE cg.customer_id IS NOT NULL AND cg.status='0' AND DATE(created_at) between '{begin_date}' AND '{end_date}' 
        GROUP BY cc.phone_number, gift_id, DATE(created_at), cg.nominal, cc.customer_id

        UNION ALL

        SELECT cc3.phone_number, cg.nominal, gift_id, count(gift_id), DATE(created_at), 'cashback' AS loyalty_program, cc3.customer_id
        FROM cashback_gif AS cg
        LEFT JOIN cashback_c c ON c.profile_id = cg.customer_id
        JOIN customer_customer cc3 ON cc3.customer_id = c.customer_id
        WHERE cg.customer_id IS NOT NULL AND cg.status='0' AND DATE(created_at) BETWEEN '{begin_date}' AND '{end_date}'
        GROUP BY cc3.phone_number, gift_id, DATE(created_at), cg.nominal, cc3.customer_id

        UNION ALL

        SELECT cc.phone_number,co.nominal, 'OZON' AS gift_id, count(date_order_create), DATE(date_order_create) AS created_at, 'k', cc.customer_id
        FROM customer_ozon AS co
        LEFT JOIN customer_customer cc ON cc.customer_id = co.customer_id
        WHERE co.customer_id IS NOT NULL AND co.status_order='3' AND DATE(date_order_create) BETWEEN '{begin_date}' AND '{end_date}'
        GROUP BY cc.phone_number, gift_id, DATE(date_order_create),co.nominal, cc.customer_id

        UNION ALL

        SELECT cc4.phone_number,co.nominal, 'OZON' AS gift_id, count(date_order_create), DATE(date_order_create) AS created_at, 'c', cc4.customer_id
        FROM cashback_ozong AS co
        LEFT JOIN cashback_c cc2 ON cc2.profile_id = co.customer_id
        JOIN customer_customer cc4 ON cc4.customer_id = cc2.customer_id
        WHERE co.customer_id IS NOT NULL AND co.status_order='3' AND  DATE(date_order_create) BETWEEN '{begin_date}' AND '{end_date}'
        GROUP BY cc4.phone_number, gift_id, DATE(date_order_create), co.nominal, cc4.customer_id

        ORDER BY count DESC;
        """

    @staticmethod
    def _prepare_data_transaction(begin_date, end_date):
        if not begin_date or not end_date:
            exit(0)
        return [
            {'$match': {'$and': [
                {'date': {'$gte': begin_date}, },
                {'date': {'$lte': end_date}, },
            ]}},
            {
                '$group': {
                    '_id':              {
                        'date':           '$date',
                        'phone':          '$phone_number',
                        'code':           '$code_1c',
                        'operation_type': '$operation_type',
                        'event_type':     '$event_type',
                        'region':         '$region',
                    },
                    'bonuses':          {'$sum': '$bonuses'},
                    'num_transactions': {'$sum': 1},
                    'currency':         {'$first': '$currency'},
                }
            },
        ]

    @staticmethod
    def __mongo_connect():
        return MongoClient(settings.MONGO_URL, tz_aware=True)

    @classmethod
    def get_transaction(cls, begin_date, end_date):
        conn = cls.__mongo_connect()
        result = conn.reports.transactions_list.aggregate(
            cls._prepare_data_transaction(
                begin_date=begin_date.isoformat(),
                end_date=end_date.isoformat()
            )
        )
        return result

    @classmethod
    def get_gift_name(cls):
        result = cls.__mongo_connect().gifts.products_list.find()
        return result

    @staticmethod
    def _fetch_data(query):
        conn = connections['data']
        conn.ensure_connection()
        with conn.connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    @classmethod
    def get_gifts(cls, begin_date, end_date):
        result = cls._fetch_data(query=cls._prepare_sql_gifts(begin_date, end_date))
        return result

    @classmethod
    def get_nomenclature(cls):
        result = cls._fetch_data(query=cls._prepare_sql_nomenclature())
        return result

    @classmethod
    def get_person(cls):
        result = cls._fetch_data(query=cls._prepare_sql_person())
        return result

    @classmethod
    def get_branch(cls):
        result = cls._fetch_data(query=cls._prepare_sql_branch())
        return result

    @classmethod
    def get_region(cls):
        result = cls._fetch_data(query=cls._prepare_sql_region())
        return result
