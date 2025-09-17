def decode_modbus_value(
    *,
    raw: list[int] | None,
    type_: str = "uns16",
    data_length: int = 1,
    scale: float = 1.0,
    precision: int = 0,
) -> str | float | None:
    if raw is None:
        return None

    if type_ == "char":
        text = "".join(
            chr(r & 0xFF) + chr((r >> 8) & 0xFF) for r in raw[: data_length // 2]
        )
        return text.strip("\x00")

    if type_ == "uns32" and len(raw) >= 2:
        value = (raw[0] << 16) | raw[1]
        return round(value * scale, precision)

    # Default: uns16
    value = raw[0] if isinstance(raw, list) else raw
    return round(value * scale, precision)
