from rest_framework import serializers
from report.models import *


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = "__all__"


class NomenclatureSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="code")

    class Meta:
        model = Nomenclature
        fields = ("code", "name",)


class TransactionSerializer(serializers.ModelSerializer):
    users1 = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Transaction
        # depth=1
        fields = ("code_1c", 'date', 'users1', 'user')
