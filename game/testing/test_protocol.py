import pytest

from game.backend.protocol import ProtocolError, parse_action_message


@pytest.mark.parametrize("message", [
    {"type": "action", "action": ["raise"]},
    {"type": "action", "action": "raise", "amount": "100"},
    {"type": "action", "action": "raise", "amount": True},
    {"type": "action", "action": "raise", "amount": 10.5},
    {"type": "action", "action": "raise", "amount": -10},
    {"type": "action", "action": "dance"},
    ["action", "call"],
])
def test_invalid_protocol_messages(message):
    with pytest.raises(ProtocolError):
        parse_action_message(message)