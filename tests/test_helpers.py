"""Tests for the pure helper functions in helpers.py."""

import importlib.util
import os

import pytest

_HELPERS_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "custom_components",
    "sabiana_energy_smart",
    "helpers.py",
)
_spec = importlib.util.spec_from_file_location("sabiana_helpers", _HELPERS_PATH)
helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(helpers)


def test_group_contiguous_merges_runs():
    """Contiguous addresses become one block, gaps start a new one."""
    assert helpers.group_contiguous([0x0100, 0x0101, 0x0102, 0x0105]) == [
        (0x0100, 3),
        (0x0105, 1),
    ]


def test_group_contiguous_empty_and_unsorted():
    """Empty input gives no blocks; order and duplicates do not matter."""
    assert helpers.group_contiguous([]) == []
    assert helpers.group_contiguous([3, 1, 2, 2]) == [(1, 3)]


def test_group_contiguous_respects_max_len():
    """Blocks never exceed max_len registers."""
    blocks = helpers.group_contiguous(range(10), max_len=4)
    assert blocks == [(0, 4), (4, 4), (8, 2)]


def test_group_contiguous_never_splits_pairs():
    """A float32 pair is never split across two blocks."""
    # Without the pair constraint, 3 would end block (0,4) and 4 would
    # start the next block.
    blocks = helpers.group_contiguous(range(6), max_len=4, pairs=[3])
    assert blocks == [(0, 3), (3, 3)]
    for start, count in blocks:
        assert not (start + count - 1 == 3), "pair base must not end a block"


def test_group_contiguous_adds_second_word_of_pairs():
    """The second word of a pair is read even if not listed explicitly."""
    assert helpers.group_contiguous([], pairs=[0x0115]) == [(0x0115, 2)]


def test_group_contiguous_rejects_tiny_max_len():
    """A float32 pair needs at least two registers per block."""
    with pytest.raises(ValueError):
        helpers.group_contiguous([1], max_len=1)


@pytest.mark.parametrize(
    ("raw", "bit", "on", "expected"),
    [
        (0x0012, 3, True, 0x001A),
        (0x001A, 3, False, 0x0012),
        (0x0000, 0, True, 0x0001),
        (0xFFFF, 15, False, 0x7FFF),
        (0x0008, 3, True, 0x0008),
    ],
)
def test_set_bit_only_touches_one_bit(raw, bit, on, expected):
    """set_bit changes exactly one bit and keeps the others."""
    assert helpers.set_bit(raw, bit, on) == expected
