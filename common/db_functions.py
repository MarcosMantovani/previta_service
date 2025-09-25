from django.contrib.postgres.functions import Func

class Unaccent(Func):
    function = "immutable_unaccent"

class TrigramSimilar(Func):
    function = "similarity"
    template = "%(expressions)s"