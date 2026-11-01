from game.backend.seat_registry import SeatRegistry
import pytest


def test_registry():
    registry = SeatRegistry(max_seats=2)

    assert registry.reserve_seat() == 0
    assert registry.reserve_seat() == 1
    assert registry.reserve_seat() is None

    registry.release_seat(0)
    assert registry.reserve_seat() == 0

    registry.release_seat(0)
    registry.release_seat(0)  # Should not raise