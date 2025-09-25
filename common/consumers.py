from functools import reduce
from operator import or_
import base64
import orjson

from django.core.paginator import EmptyPage, Paginator
from django.db.models import Q, QuerySet
from djangochannelsrestframework.decorators import action
from djangochannelsrestframework.mixins import ListModelMixin
from rest_framework import status


def _b64e(obj: dict) -> str:
    return base64.urlsafe_b64encode(orjson.dumps(obj)).decode().rstrip("=")


def _b64d(s: str) -> dict:
    # re-adiciona padding se necessário
    pad = "=" * (-len(s) % 4)
    return orjson.loads(base64.urlsafe_b64decode((s + pad).encode()))


class BaseConsumer:
    @classmethod
    async def decode_json(cls, text_data):
        try:
            return orjson.loads(text_data)
        except TypeError:
            import pprint

            pprint.pprint(text_data)
            raise

    @classmethod
    async def encode_json(cls, content):
        try:
            return orjson.dumps(content).decode()
        except TypeError:
            import pprint

            pprint.pprint(content)
            raise


class PaginatedListModelMixin(ListModelMixin):
    """
    Mantém seu comportamento atual (LIMIT/OFFSET),
    e ativa keyset quando pager.useKeyset = True.
    """

    def set_exclude_queryset(self, queryset, **kwargs):
        qs = queryset
        data = kwargs.get("data", {})
        exclude = data.get("exclude", {})

        if exclude:
            exclude = dict(
                filter(
                    lambda elem: not isinstance(elem[1], list) or len(elem[1]) > 0,
                    exclude.items(),
                )
            )
            return qs.exclude(**exclude)
        return qs

    def filter_queryset(self, queryset, **kwargs):
        qs = super().filter_queryset(queryset, **kwargs)
        data = kwargs.get("data", {})
        filters = data.get("filters", {})
        filters = dict(
            filter(
                lambda elem: not isinstance(elem[1], list) or len(elem[1]) > 0,
                filters.items(),
            )
        )
        return qs.filter(**filters)

    def set_search_lookups(self, queryset, **kwargs):
        qs = queryset
        data = kwargs.get("data", {})
        search = data.get("search", {})
        lookups = search.get("lookups", [])
        query = search.get("query", "")

        if query and query.strip() and lookups:
            lookups = reduce(or_, (Q((lookup, query)) for lookup in lookups))
            if lookups:
                return qs.filter(lookups)
        return qs

    def set_order_by(self, queryset, **kwargs):
        qs = queryset
        data = kwargs.get("data", {})
        order = data.get("order", ["-id"])
        return qs.order_by(*order)

    def _get_page_object_list(self, queryset, **kwargs):
        """
        Hook teu original (mantido).
        ATENÇÃO: nesse ponto, em keyset, o queryset já está limitado.
        """
        return queryset

    # ===================== utilidades para keyset =====================
    def _normalize_order(self, order_list):
        """
        Converte, p.ex., ["-created_at","status","-score"] em:
        [("created_at","desc"), ("status","asc"), ("score","desc"), ("id","asc?")]
        Garante 'id' no fim como tie-breaker se não estiver presente.
        """
        norm = []
        for f in order_list or []:
            if f.startswith("-"):
                norm.append((f[1:], "desc"))
            else:
                norm.append((f, "asc"))

        # garante 'id' como último campo para desempate determinístico
        has_id = any(name == "id" for name, _ in norm)
        if not has_id:
            norm.append(("id", "asc"))  # pode trocar para "desc" se preferir

        # remove duplicatas preservando a última intenção (ex.: veio "id" e depois "-id")
        seen = {}
        for name, dir_ in norm:
            seen[name] = dir_
        norm = [(name, seen[name]) for name in dict.fromkeys(seen.keys())]

        return norm

    def _build_seek_filter(self, norm_order, cursor_values: dict, direction: str):
        """
        Gera o Q de seek para N colunas (lexicográfico):
        (c1 > v1) OR (c1 = v1 AND c2 > v2) OR ... (c1 = v1 AND ... AND cN > vN)
        Operador > ou < depende de asc/desc e do 'direction' (after/before).
        """
        if not cursor_values:
            return Q()

        def op(field_name: str, asc: bool, want_after: bool) -> str:
            # want_after=True => lado "seguinte" na ordenação efetiva
            if asc:
                return "gt" if want_after else "lt"
            else:
                return "lt" if want_after else "gt"

        want_after = direction == "after"

        # constrói a disjunção incremental
        disj = Q()
        prefix_equals = Q()
        for idx, (field_name, dir_) in enumerate(norm_order):
            asc = dir_ == "asc"
            # campo inexistente no cursor? para robustez, ignora comparador desse nível
            if field_name not in cursor_values:
                break

            cmp_lookup = f"{field_name}__{op(field_name, asc, want_after)}"
            # (prefixo de igualdade até coluna anterior) AND (coluna atual >/< valor)
            clause = prefix_equals & Q(**{cmp_lookup: cursor_values[field_name]})
            disj = disj | clause

            # atualiza prefixo: (c1 = v1 AND c2 = v2 AND ... ci = vi)
            prefix_equals = prefix_equals & Q(**{field_name: cursor_values[field_name]})

        return disj

    def _extract_cursor_values(self, obj, fields):
        # salva valores na mesma ordem das colunas de ordenação
        # (orjson lida bem com datetimes/ints/strings)
        values = {}
        for f in fields:
            if "__" in f:
                # Navegar pelos relacionamentos (ex: last_message__created_at)
                value = obj
                for part in f.split("__"):
                    if value is None:
                        break
                    value = getattr(value, part, None)
                values[f] = value
            else:
                # Campo direto
                values[f] = getattr(obj, f)
        return values

    # ===================== keyset core =====================
    def _perform_keyset_paginate(self, base_qs: QuerySet, **kwargs):
        data = kwargs.get("data", {}) or {}
        pager = data.get("pager", {}) or {}

        order_list = data.get("order") or ["-id"]
        norm_order = self._normalize_order(order_list)
        fields = [f for f, _ in norm_order]

        # aplica order_by como strings mesmo (rápido e genérico)
        qs = base_qs.order_by(*order_list if order_list else ["id"])

        after_cursor = pager.get("afterCursor")
        before_cursor = pager.get("beforeCursor")
        page_size = int(pager.get("pageSize") or 20)
        reverse_client = bool(pager.get("reverse") or False)

        cursor_values = {}
        direction = None
        if after_cursor and before_cursor:
            try:
                cursor_values = _b64d(after_cursor)
                direction = "after"
            except Exception:
                cursor_values = _b64d(before_cursor)
                direction = "before"
        elif after_cursor:
            cursor_values = _b64d(after_cursor)
            direction = "after"
        elif before_cursor:
            cursor_values = _b64d(before_cursor)
            direction = "before"

        if direction:
            qs = qs.filter(
                self._build_seek_filter(norm_order, cursor_values, direction)
            )

        limit = page_size + 1
        items = list(self._get_page_object_list(qs[:limit], **kwargs))
        has_more = len(items) > page_size
        if has_more:
            items = items[:page_size]

        if reverse_client:
            items = list(items)[::-1]

        next_cursor = prev_cursor = None
        if items:
            first_vals = self._extract_cursor_values(items[0], fields)
            last_vals = self._extract_cursor_values(items[-1], fields)
            prev_cursor = _b64e(first_vals)
            next_cursor = _b64e(last_vals)

        result = {
            "pager": {
                "pageSize": page_size,
                "hasPrevious": bool(before_cursor),
                "hasNext": has_more,
                "afterCursor": next_cursor,
                "beforeCursor": prev_cursor,
                "order": order_list,
                "useKeyset": True,
            },
            "list": self.get_serializer(
                instance=items, many=True, action_kwargs=kwargs
            ).data,
        }
        return result, status.HTTP_200_OK

    # ===================== dispatcher: keyset vs offset =====================
    def _perform_paginate(self, **kwargs):
        data = kwargs.get("data", {}) or {}
        pager = data.get("pager", {}) or {}

        # monta queryset comum (teu pipeline atual)
        queryset = self.filter_queryset(self.get_queryset(**kwargs), **kwargs)
        queryset = self.set_exclude_queryset(queryset, **kwargs)
        queryset = self.set_search_lookups(queryset, **kwargs)
        queryset = self.set_order_by(queryset, **kwargs)

        # se pedir keyset, usamos o fluxo acima
        if pager.get("useKeyset"):
            return self._perform_keyset_paginate(queryset, **kwargs)

        # ===== fluxo original: LIMIT/OFFSET =====
        page_size = int(pager.get("pageSize") or 20)
        page_number = int(pager.get("page") or 1)
        reverse = bool(pager.get("reverse") or False)

        paginator = Paginator(queryset, page_size)
        try:
            page = paginator.page(page_number)
            serializer = self.get_serializer(
                instance=self._get_page_object_list(page.object_list, **kwargs),
                many=True,
                action_kwargs=kwargs,
            )
            lst = serializer.data
            if reverse:
                lst = lst[::-1]

            data_resp = {
                "pager": {
                    "count": paginator.count,
                    "page": page_number,
                    "pageSize": page_size,
                    "hasPrevious": page.has_previous(),
                    "hasNext": page.has_next(),
                    "order": data.get("order", ["-id"]),
                    "useKeyset": False,
                },
                "list": lst,
            }
        except EmptyPage:
            data_resp = {
                "pager": {
                    "count": 0,
                    "page": page_number,
                    "pageSize": page_size,
                    "hasPrevious": False,
                    "hasNext": False,
                    "order": data.get("order", ["-id"]),
                    "useKeyset": False,
                },
                "list": [],
            }
        return data_resp, status.HTTP_200_OK

    @action()
    def paginate(self, **kwargs):
        return self._perform_paginate(**kwargs)
