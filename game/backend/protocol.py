
ALLOWED_ACTIONS = {"check", "fold", "call", "bet", "raise"}
WAGER_ACTIONS = {"bet", "raise"}


class ProtocolError(ValueError):
    pass


def parse_action_message(message: object) -> dict:
    if type(message) is not dict:
        raise ProtocolError()

    required = {"type", "action"}
    allowed = {"type", "action", "amount"}

    keys = set(message)

    if not required <= keys <= allowed:
        raise ProtocolError()

    if message["type"] != "action":
        raise ProtocolError()

    action = message["action"]

    if type(action) is not str or action not in ALLOWED_ACTIONS:
        raise ProtocolError()

    amount = message.get("amount")

    if action in WAGER_ACTIONS:
        if type(amount) is not int or amount <= 0:
            raise ProtocolError()

        return {
            "action": action,
            "amount": amount,
        }

    if amount is not None:
        raise ProtocolError()

    return {"action": action}
