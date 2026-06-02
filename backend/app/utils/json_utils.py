import math
import numpy as np


def sanitize_number(
    value,
    default=0.0,
):

    try:

        if value is None:
            return default

        if isinstance(
            value,
            np.generic,
        ):

            value = value.item()

        value = float(value)

        if math.isnan(value):
            return default

        if math.isinf(value):
            return default

        return value

    except:

        return default


def sanitize_for_json(obj):

    if isinstance(obj, dict):

        return {
            str(k): sanitize_for_json(v)
            for k, v in obj.items()
        }

    elif isinstance(obj, list):

        return [
            sanitize_for_json(v)
            for v in obj
        ]

    elif isinstance(obj, tuple):

        return tuple(
            sanitize_for_json(v)
            for v in obj
        )

    elif isinstance(
        obj,
        (
            float,
            int,
            np.generic,
        ),
    ):

        return sanitize_number(obj)

    return obj