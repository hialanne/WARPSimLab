# utilities.py

# utilities.py

def parse_money_strict(value, field_name="value"):
    """
    Convert a string or StringVar to a float.
    Works with plain strings, numbers, or Tkinter StringVar.
    Raises ValueError if conversion fails.
    """
    # If value is a StringVar, get the string
    if hasattr(value, "get"):
        text = value.get()
    else:
        text = str(value)  # convert plain value to string

    text = text.replace(",", "").strip()

    if text == "":
        raise ValueError(f"{field_name} cannot be empty")

    try:
        return float(text)
    except ValueError:
        raise ValueError(f"Invalid {field_name}: '{text}'")
