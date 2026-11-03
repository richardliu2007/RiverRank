import asyncio
import json

from websockets.asyncio.client import connect


URL = "ws://127.0.0.1:8000/ws/demo"
RECEIVE_TIMEOUT = 5


async def receive_message(client):
    raw = await asyncio.wait_for(client.recv(), timeout=RECEIVE_TIMEOUT)
    return json.loads(raw)


async def main():
    # Connect Alice
    async with connect(URL) as alice:
        welcome_a = await receive_message(alice)
        assert welcome_a["type"] == "welcome"
        print("Alice connected:", welcome_a["seat_id"])

        # Connect Bob while Alice remains connected
        async with connect(URL) as bob:
            welcome_b = await receive_message(bob)
            assert welcome_b["type"] == "welcome"
            print("Bob connected:", welcome_b["seat_id"])

            assert welcome_a["seat_id"] == 0
            assert welcome_b["seat_id"] == 1
            assert welcome_a["version"] == welcome_b["version"]
            initial_version = welcome_a["version"]
            last_version = initial_version

            # Alice sends malformed JSON without advancing the game.
            await alice.send('{"type": "action", "action": "raise", "amount":')
            response = await receive_message(alice)
            assert response == {
                "type": "error",
                "error": "malformed JSON",
            }

            # Invalid amount types must be rejected without disconnecting Alice.
            await alice.send(json.dumps({
                "type": "action",
                "action": "raise",
                "amount": "100",
            }))
            response = await receive_message(alice)
            assert response == {
                "type": "error",
                "error": "invalid message",
            }

            # The connection should still work: Alice calls the big blind.
            await alice.send(json.dumps({
                "type": "action",
                "action": "call"
            }))

            # Both players receive their own snapshots
            update_a, update_b = await asyncio.gather(
                receive_message(alice), receive_message(bob)
            )

            assert update_a["type"] == "snapshot"
            assert update_b["type"] == "snapshot"
            assert update_a["version"] == update_b["version"]
            assert update_a["version"] == initial_version + 1
            assert update_b["version"] == initial_version + 1
            last_version = update_a["version"]

            print("Malformed JSON recovery passed!")
            print("Invalid amount type recovery passed!")
            print("Alice called:")
            print("  Alice's state:", update_a["state"]["currStreet"])
            print("  Bob's state:", update_b["state"]["currStreet"])

            # Bob checks, completing preflop betting
            await bob.send(json.dumps({
                "type": "action",
                "action": "check"
            }))

            update_a, update_b = await asyncio.gather(
                receive_message(alice), receive_message(bob)
            )

            assert update_a["type"] == "snapshot"
            assert update_b["type"] == "snapshot"
            assert update_a["version"] == last_version + 1
            assert update_b["version"] == update_a["version"]
            last_version = update_a["version"]

            assert update_a["state"]["currStreet"] == "flop"
            assert update_b["state"]["currStreet"] == "flop"
            assert len(update_a["state"]["board"]) == 3

            print("Bob checked.")
            print("New street:", update_a["state"]["currStreet"])
            print("Community cards:", update_a["state"]["board"])
            print("Version:", update_a["version"])

            # Bob acts first on the flop, so Alice's check must be rejected.
            await alice.send(json.dumps({"type": "action", "action": "check"}))
            error = await receive_message(alice)
            assert error == {"type": "error", "error": "invalid action"}

            # Keep last_version unchanged: the next valid action must advance
            # it by exactly one, even after the rejected action.
            print("Out-of-turn action rejected.")

            # Both players check through flop, turn, and river.
            for street in ("flop", "turn", "river"):
                assert update_a["state"]["currStreet"] == street
                assert update_b["state"]["currStreet"] == street
                for client in (bob, alice):
                    await client.send(json.dumps({
                        "type": "action",
                        "action": "check"
                    }))

                    update_a, update_b = await asyncio.gather(
                        receive_message(alice),
                        receive_message(bob)
                    )

                    assert update_a["type"] == "snapshot"
                    assert update_b["type"] == "snapshot"

                    # Both clients observe the same authoritative version.
                    assert update_a["version"] == update_b["version"]
                    assert update_a["version"] == last_version + 1
                    last_version = update_a["version"]

                    # Public game state must agree.
                    assert (
                        update_a["state"]["board"]
                        == update_b["state"]["board"]
                    )
                    assert (
                        update_a["state"]["pot"]
                        == update_b["state"]["pot"]
                    )

                print(f"Completed {street}")

            # After the final river check, showdown occurs.
            state_a = update_a["state"]
            state_b = update_b["state"]

            assert state_a["currStreet"] == "showdown"
            assert state_b["currStreet"] == "showdown"
            assert state_a["pot"] == 0
            assert len(state_a["board"]) == 5

            # Check chip conservation.
            assert sum(
                player["stack"]
                for player in state_a["players"]
            ) == 4000

            # Verify private cards remain player-specific
            assert state_a["hand"] == welcome_a["state"]["hand"]
            assert state_b["hand"] == welcome_b["state"]["hand"]

            assert all(
                "hand" not in player and "cards" not in player
                for state in (state_a, state_b)
                for player in state["players"]
            )

            print("Full-hand integration test passed!")


if __name__ == "__main__":
    asyncio.run(main())

