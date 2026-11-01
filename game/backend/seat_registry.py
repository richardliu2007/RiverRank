
class SeatRegistry:
    def __init__(self, max_seats: int = 2):
        self.max_seats = max_seats
        self.reserved: set[int] = set()

    def reserve_seat(self) -> int | None:
        # Find the first available seat
        # Reserve it before returning
        # Return None if full
        if len(self.reserved) == self.max_seats: return None
        for seat in range(self.max_seats):
            if seat not in self.reserved:
                self.reserved.add(seat)
                return seat

    def release_seat(self, seat_id: int) -> None:
        self.reserved.discard(seat_id)
