# gui_validation.py

import math


class GUIValidationError(ValueError):
    pass

def mark_validation_failed(widget):
    setattr(widget.winfo_toplevel(), "_warpsimlab_validation_failed", True)

def parse_finite_float(raw_value, *, allow_commas=False, allow_scientific=True,
                       minimum=None, maximum=None, allow_blank=False):
    text = str(raw_value).strip()

    if allow_commas:
        text = text.replace(",", "")

    if text == "":
        if allow_blank:
            return None
        raise GUIValidationError("Value is required.")

    if not allow_scientific and "e" in text.lower():
        raise GUIValidationError("Scientific notation is not allowed.")

    try:
        value = float(text)
    except (TypeError, ValueError) as exc:
        raise GUIValidationError("Must be a valid number.") from exc

    if not math.isfinite(value):
        raise GUIValidationError("Must be a finite number.")

    if minimum is not None and value < minimum:
        raise GUIValidationError(f"Must be at least {minimum}.")

    if maximum is not None and value > maximum:
        raise GUIValidationError(f"Must be no more than {maximum}.")

    return value


def parse_integer(raw_value, *, allow_commas=False, minimum=None, maximum=None, allow_blank=False):
    text = str(raw_value).strip()

    if allow_commas:
        text = text.replace(",", "")

    if text == "":
        if allow_blank:
            return None
        raise GUIValidationError("Value is required.")

    try:
        value = int(text)
    except (TypeError, ValueError) as exc:
        raise GUIValidationError("Must be a valid integer.") from exc

    if minimum is not None and value < minimum:
        raise GUIValidationError(f"Must be at least {minimum}.")

    if maximum is not None and value > maximum:
        raise GUIValidationError(f"Must be no more than {maximum}.")

    return value