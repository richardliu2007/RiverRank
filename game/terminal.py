"""Interactive terminal client for the RiverRank WebSocket backend.

Usage:
    pip install websockets
    python riverrank_terminal.py

Run two instances in separate terminals, with the FastAPI server running.
"""

import asyncio
import json
import sys
import threading

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

URL = sys.argv[1] if len(sys.argv) > 1 else "ws://127.0.0.1:8000/ws/demo"


def format_card(card):
    if not isinstance(card, dict):
        return str(card)

    ranks = {11: "J", 12: "Q", 13: "K", 14: "A"}
    suits = {"s": "♠", "h": "♥", "d": "♦", "c": "♣"}

    rank = card.get("rank", "?")
    suit = card.get("suit", "?")

    return f"[{ranks.get(rank, rank)}{suits.get(suit, suit)}]"


def format_cards(cards):
    return " ".join(format_card(card) for card in (cards or [])) or "(none)"


def show_state(state, version=None):
    if not isinstance(state, dict):
        print("State:", state)
        return
    print("\n" + "=" * 50)
    print(f"Version: {version}  |  Street: {state.get('currStreet', '?')}")
    print(f"Pot: {state.get('pot', '?')}  |  Current actor: {state.get('actionID', '?')}")
    print(f"Board: {format_cards(state.get('board'))}")
    print(f"Your hand: {format_cards(state.get('hand'))}")
    print("Players:")
    for p in state.get("players", []):
        flags = [flag for flag, key in (("folded", "folded"), ("all-in", "allIn")) if p.get(key)]
        suffix = f"  ({', '.join(flags)})" if flags else ""
        print(f"  Seat {p.get('id', '?')}: {p.get('name', '?')}"
              f" | stack={p.get('stack', '?')}"
              f" | street bet={p.get('streetBet', '?')}{suffix}")
    print("=" * 50)


def console_reader(loop, lines):
    """Daemon thread keeps blocking input() off the asyncio event loop."""
    while True:
        try:
            line = input("riverrank> ")
        except (EOFError, KeyboardInterrupt):
            line = "quit"
        try:
            loop.call_soon_threadsafe(lines.put_nowait, line)
        except RuntimeError:  # Event loop has already closed.
            return
        if line.strip().lower() in {"quit", "exit"}:
            return


def print_help():
    print("Commands: fold | check | call | bet N | raise N | state | help | quit")
    print("N is the wager amount passed directly to your game engine.")


async def run_client(websocket):
    lines = asyncio.Queue()
    latest = {"state": None, "version": None}
    loop = asyncio.get_running_loop()
    threading.Thread(target=console_reader, args=(loop, lines), daemon=True).start()

    async def receive_updates():
        try:
            async for raw in websocket:
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    print("\nReceived non-JSON server message:", raw)
                    continue

                kind = message.get("type") if isinstance(message, dict) else None
                if kind == "welcome":
                    print(f"\nConnected! Assigned seat {message.get('seat_id')}.")
                    latest.update(state=message.get("state"), version=message.get("version"))
                    show_state(latest["state"], latest["version"])
                elif kind == "snapshot":
                    latest.update(state=message.get("state"), version=message.get("version"))
                    show_state(latest["state"], latest["version"])
                elif kind == "error":
                    print(f"\nServer rejected request: {message.get('error', 'unknown error')}")
                else:
                    print("\nServer message:", json.dumps(message, indent=2))
        except ConnectionClosed as exc:
            print(f"\nServer connection closed: {exc}")
        finally:
            print("\nReceiver stopped.")

    async def send_commands():
        while True:
            line = (await lines.get()).strip()
            if not line:
                continue
            parts = line.lower().split()
            command = parts[0]

            if command in {"quit", "exit"}:
                print("Disconnecting...")
                return
            if command == "help":
                print_help()
                continue
            if command == "state":
                if latest["state"] is None:
                    print("No state received yet.")
                else:
                    show_state(latest["state"], latest["version"])
                continue

            if command in {"fold", "check", "call"} and len(parts) == 1:
                payload = {"type": "action", "action": command}
            elif command in {"bet", "raise"} and len(parts) == 2:
                try:
                    amount = int(parts[1])
                except ValueError:
                    print("Wager must be a positive integer.")
                    continue
                if amount <= 0:
                    print("Wager must be a positive integer.")
                    continue
                payload = {"type": "action", "action": command, "amount": amount}
            else:
                print("Unknown command or wrong number of arguments.")
                print_help()
                continue

            try:
                await websocket.send(json.dumps(payload))
            except ConnectionClosed as exc:
                print(f"Unable to send; connection closed: {exc}")
                return

    print_help()
    receiver = asyncio.create_task(receive_updates())
    sender = asyncio.create_task(send_commands())
    done, pending = await asyncio.wait({receiver, sender}, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)
    for task in done:
        if not task.cancelled():
            error = task.exception()
            if error is not None:
                raise error


async def main():
    try:
        async with connect(URL) as websocket:
            await run_client(websocket)
    except (OSError, ConnectionClosed) as exc:
        print(f"Could not use {URL}: {exc}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
