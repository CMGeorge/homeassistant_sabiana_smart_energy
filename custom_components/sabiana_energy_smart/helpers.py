"""Pure helper functions for the Sabiana Smart Energy integration.

Nothing in this module imports Home Assistant, so it can be unit tested
without a Home Assistant installation.
"""

from __future__ import annotations

from collections.abc import Iterable

# Modbus allows up to 125 holding registers per read; stay well below it.
MAX_BLOCK_LENGTH = 60


def decode_modbus_value(
    *,
    raw: list[int] | None,
    type_: str = "uns16",
    data_length: int = 1,
    scale: float = 1.0,
    precision: int = 0,
) -> str | float | None:
    """Decode raw register values into a scaled value or a string."""
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


def group_contiguous(
    addresses: Iterable[int],
    max_len: int = MAX_BLOCK_LENGTH,
    pairs: Iterable[int] = (),
) -> list[tuple[int, int]]:
    """Group register addresses into contiguous ``(start, count)`` blocks.

    ``pairs`` lists base addresses of two-register values (e.g. float32).
    A pair ``(addr, addr + 1)`` is never split across two blocks, so both
    words of the value always come from the same Modbus transaction.
    """
    pair_set = set(pairs)
    all_addresses = set(addresses)
    for base in pair_set:
        all_addresses.update((base, base + 1))

    ordered = sorted(all_addresses)
    if max_len < 2:
        raise ValueError("max_len must be at least 2")

    blocks: list[tuple[int, int]] = []
    index = 0
    while index < len(ordered):
        start = ordered[index]
        end = start  # inclusive
        index += 1
        while index < len(ordered) and ordered[index] == end + 1:
            candidate = ordered[index]
            # Adding `candidate` would exceed the block length.
            if candidate - start + 1 > max_len:
                break
            # `candidate` starts a pair whose second word would not fit.
            if candidate in pair_set and candidate + 1 - start + 1 > max_len:
                break
            end = candidate
            index += 1
        blocks.append((start, end - start + 1))
    return blocks


def set_bit(raw: int, bit: int, on: bool) -> int:
    """Return ``raw`` with ``bit`` set or cleared, limited to 16 bits."""
    if on:
        return (raw | (1 << bit)) & 0xFFFF
    return raw & ~(1 << bit) & 0xFFFF
