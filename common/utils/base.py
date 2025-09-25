import json
import monthdelta
from dataclasses import asdict
from typing import Type, TypeVar, Union
from bizdays import Calendar

# Configurações globais
calendar = Calendar.load("ANBIMA")
T = TypeVar("T")


def is_business_day(date):
    return calendar.isbizday(date)


def get_next_business_day(date):
    if is_business_day(date):
        return date
    return calendar.offset(date, 1)


def get_next_month_day(date, preffered_day=None):
    next_date = date + monthdelta.monthdelta(1)

    try:
        if preffered_day:
            next_date = next_date.replace(day=preffered_day)
    except ValueError:
        pass

    return get_next_business_day(next_date)


def to_dict(data_class_instance):
    return asdict(data_class_instance)


def from_dict(data_class, data):
    # If data is None, return None
    if not data:
        return None

    # Get the dataclass fields
    dataclass_fields = data_class.__dataclass_fields__.values()

    # Initialize an empty dictionary to hold the field names and their types
    fields = {}

    # Iterate over each field in the dataclass fields
    for field in dataclass_fields:
        # Add the field name and type to the fields dictionary
        fields[field.name] = field.type

    # Initialize an empty dictionary to hold the transformed data
    inner = {}

    # Iterate over each item in the data dictionary
    for f in data:
        # If the value is a dictionary and corresponds to a field in the data_class
        if isinstance(data.get(f, {}), dict) and f in fields and fields[f] is not None:
            # Recursively call from_dict on the value
            inner[f] = from_dict(fields[f], data.get(f, {}))
        else:
            # Otherwise, just copy the value as is
            inner[f] = data.get(f, {})

    # Create an instance of data_class using the transformed data
    return data_class(**inner)


def to_dataclass(payload: Union[str, dict, bytes], data_class: Type[T]) -> T:
    if isinstance(payload, str) or isinstance(payload, bytes):
        data = json.loads(payload)
    elif isinstance(payload, dict):
        data = payload
    else:
        raise Exception("Invalid payload type (%s)" % type(payload))
    return from_dict(data_class, data)
