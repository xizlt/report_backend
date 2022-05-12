from django.db import models

CHOICES = [
    ('k', 'Конкурс'),
    ('c', 'Кэшбэк')
]

MODELNAME = [
    ('region', 'Регион'),
    ('branch', 'Филиал'),
    ('person', 'Пользователи'),
    ('transaction', 'Транзакции'),
    ('nomenclature', 'Товар'),
    ('gifts', 'Подарки'),
    ('giftsName', 'Название подарков')
]


class Person(models.Model):
    user_id = models.BigIntegerField()
    phone = models.BigIntegerField()
    entity = models.CharField(max_length=250)
    name = models.CharField(max_length=250)
    loyalty_program = models.CharField(max_length=250, choices=CHOICES)
    active = models.BooleanField()
    branch = models.SmallIntegerField()
    region = models.SmallIntegerField()

    def __str__(self):
        return str(self.phone)


class Region(models.Model):
    id = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    alias = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class Branch(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    region = models.CharField(max_length=3)

    def __str__(self):
        return self.name


class Nomenclature(models.Model):
    name = models.CharField(max_length=250)
    code = models.CharField(unique=True, max_length=20)
    price = models.IntegerField()

    def __str__(self):
        return self.name


class Transaction(models.Model):
    phone = models.CharField(max_length=11)
    code_1c = models.CharField(max_length=11)
    region = models.CharField(max_length=7)
    bonuses = models.IntegerField()
    date = models.DateField()
    operation_type = models.PositiveSmallIntegerField()
    event_type = models.PositiveSmallIntegerField()
    currency = models.CharField(max_length=3)
    count = models.PositiveSmallIntegerField()
    user = models.ForeignKey(Person, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.phone} - {self.code_1c} - {self.bonuses}"


class Gifts(models.Model):
    phone = models.CharField(max_length=11)
    count = models.PositiveSmallIntegerField()
    gift_id = models.CharField(max_length=36)
    nominal = models.IntegerField()
    created = models.DateField()
    loyalty_program = models.CharField(max_length=250, choices=CHOICES)
    user = models.ForeignKey(Person, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.gift_id}"


class GiftsName(models.Model):
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=250)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class DifferenceData(models.Model):
    start_date = models.DateField(auto_now=True)
    end_date = models.DateField()
    difference = models.IntegerField()
    models = models.CharField(max_length=50)

    def __str__(self):
        return self.models

    class Meta:
        ordering = ["-end_date"]
