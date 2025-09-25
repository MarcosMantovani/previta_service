from typing import Any, Callable

class NOT_PROVIDED: ...

class Field:
    def __init__(
        self,
        *args: Any,
        default: Any | Callable[[], Any] | NOT_PROVIDED = ...,
        **kwargs: Any,
    ) -> None: ...

class BooleanField(Field): ...

class FileField(Field):
    def __init__(
        self,
        *args: Any,
        upload_to: str | Callable[[], str] | None = None,
        **kwargs: Any,
    ) -> None: ...
