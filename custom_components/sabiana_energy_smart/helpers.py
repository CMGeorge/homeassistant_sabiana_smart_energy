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


# --- Device clock (Modbus Block 8: Time and Day) -----------------------------
# 0x0800: MSB = hour (0..23), LSB = minutes (0..59)
# 0x0801: day of week, 1 = Monday ... 7 = Sunday
#
# The unit only stores hour, minute and weekday. It has no calendar date, so it
# cannot know when daylight saving time starts or ends: the clock has to be
# corrected from outside (Home Assistant) twice a year.

MINUTES_PER_WEEK = 7 * 24 * 60
WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def encode_device_clock(hour: int, minute: int, isoweekday: int) -> list[int]:
    """Return the raw values for registers 0x0800 and 0x0801."""
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 1 <= isoweekday <= 7):
        raise ValueError(f"Invalid clock value {isoweekday=} {hour=} {minute=}")
    return [(hour << 8) | minute, isoweekday]


def decode_device_clock(
    time_raw: int | None, day_raw: int | None
) -> tuple[int, int, int] | None:
    """Decode registers 0x0800/0x0801 into (isoweekday, hour, minute).

    Returns None when a value is missing or out of range.
    """
    if time_raw is None or day_raw is None:
        return None
    hour = (time_raw >> 8) & 0xFF
    minute = time_raw & 0xFF
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 1 <= day_raw <= 7):
        return None
    return day_raw, hour, minute


def clock_drift_minutes(
    device: tuple[int, int, int], reference: tuple[int, int, int]
) -> int:
    """Return device minus reference clock in minutes, wrapped to +/- half a week.

    Both arguments are (isoweekday, hour, minute) tuples. A positive result
    means the device clock is ahead (e.g. +60 after DST ended).
    """

    def _minute_of_week(value: tuple[int, int, int]) -> int:
        day, hour, minute = value
        return (day - 1) * 24 * 60 + hour * 60 + minute

    diff = (_minute_of_week(device) - _minute_of_week(reference)) % MINUTES_PER_WEEK
    if diff > MINUTES_PER_WEEK // 2:
        diff -= MINUTES_PER_WEEK
    return diff


def format_device_clock(value: tuple[int, int, int]) -> str:
    """Format (isoweekday, hour, minute) as e.g. 'Mon 14:05'."""
    day, hour, minute = value
    return f"{WEEKDAY_NAMES[day - 1]} {hour:02d}:{minute:02d}"
