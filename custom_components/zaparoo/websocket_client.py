"""Websocket Api For Zaparoo."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import uuid
from typing import TYPE_CHECKING, Any

import websockets
from homeassistant.exceptions import HomeAssistantError
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

if TYPE_CHECKING:
    from .coordinator import ZaparooCoordinator

_LOGGER = logging.getLogger(__name__)

API_PATH = "/api/v0.1"


class ZaparooWebSocket:
    """Manage a persistent WebSocket connection to a Zaparoo device."""

    def __init__(self, host: str, port: int, coordinator: ZaparooCoordinator) -> None:
        """Init the web socket."""
        self.host = host
        self.port = port
        self.coordinator = coordinator

        self._ws = None  # intentionally untyped (HA style)
        self._task: asyncio.Task | None = None
        self._stop = False

        # Pending JSON-RPC requests: id -> Future
        self._pending: dict[str, asyncio.Future] = {}

    async def start(self) -> None:
        """Start the websocket connection loop."""
        self._stop = False
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop websocket loop and close connection."""
        self._stop = True

        if self._ws:
            with contextlib.suppress(Exception):
                await self._ws.close()

        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

        self._fail_pending(HomeAssistantError("WebSocket stopped"))

    async def _run(self) -> None:
        """Loop reconnect."""
        url = f"ws://{self.host}:{self.port}{API_PATH}"
        while not self._stop:
            try:
                _LOGGER.debug("Connecting to Zaparoo WS: %s", url)
                async with websockets.connect(
                    url,
                    ping_interval=30,
                    ping_timeout=10,
                ) as ws:
                    self._ws = ws
                    self.coordinator.connected()
                    _LOGGER.info("Zaparoo WS connected")

                    await self._listen()
            except (ConnectionClosedOK, ConnectionClosedError):
                _LOGGER.debug("Zaparoo WS closed")
            except asyncio.CancelledError:
                _LOGGER.debug("Zaparoo WS task cancelled")
                break
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Zaparoo WS error: %s", err)

            self._ws = None
            self.coordinator.disconnected()
            self._fail_pending(RuntimeError("WebSocket disconnected"))

            if not self._stop:
                await asyncio.sleep(30)

        _LOGGER.debug("Zaparoo WS loop stopped")

    async def _listen(self) -> None:
        """Listen for incoming websocket messages."""
        ws = self._ws
        if ws is None:
            return

        try:
            async for message in ws:
                self._handle_message(message)

        except (ConnectionClosedOK, ConnectionClosedError):
            pass

        except Exception:
            _LOGGER.exception("Unexpected error in WS listener")

    def _handle_message(self, message: websockets.Data) -> None:
        """Websocket message handling."""
        try:
            data = json.loads(message)

            # JSON-RPC response
            if "id" in data:
                fut = self._pending.get(data["id"])
                _LOGGER.info(message)
                if fut and not fut.done():
                    fut.set_result(data)

            # Server-side event
            if "method" in data:
                self.coordinator.handle_ws_event(
                    data["method"],
                    data.get("params"),
                )
        except Exception:
            _LOGGER.exception("Failed to process Zaparoo WS message")

    async def send_jsonrpc(self, method: str, params: Any | None = None) -> Any:
        """Send a JSON-RPC request and wait for its response."""
        if self._ws is None:
            msg = "Zaparoo WebSocket is not connected"
            raise HomeAssistantError(msg)

        rpc_id = str(uuid.uuid4())

        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "method": method,
        }

        if params is not None:
            payload["params"] = params

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending[rpc_id] = future

        await self._ws.send(json.dumps(payload))

        try:
            return await asyncio.wait_for(future, timeout=10)
        finally:
            self._pending.pop(rpc_id, None)

    def _fail_pending(self, exc: Exception) -> None:
        """Fail all pending RPC futures."""
        for future in self._pending.values():
            if not future.done():
                future.set_exception(exc)
        self._pending.clear()
