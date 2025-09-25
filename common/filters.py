from rest_framework import filters


class UnaccentSearchFilter(filters.SearchFilter):
    def get_search_fields(self, view, request):
        search_fields = super().get_search_fields(view, request)
        return [f'{field}__unaccent' for field in search_fields]