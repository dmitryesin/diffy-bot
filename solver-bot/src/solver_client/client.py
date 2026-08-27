from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout
from src.config import Settings
from src.solver_client.models import SolveParameters, UserSettings

logger = logging.getLogger(__name__)

_METHOD_MAPPING = {
    "euler": "euler",
    "midpoint": "midpoint",
    "heun": "heun",
    "runge_kutta": "rungeKutta",
    "dormand_prince": "dormandPrince",
}


class SolverClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.solver_api_url.rstrip("/")
        self._request_timeout = settings.request_timeout
        self._max_retries = settings.max_retries
        self._retry_delay = settings.retry_delay
        self._max_retry_delay = settings.max_retry_delay
        self._session: ClientSession | None = None

    async def start(self) -> None:
        self._session = ClientSession(timeout=ClientTimeout(total=self._request_timeout))

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> SolverClient:
        await self.start()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()

    @property
    def _http(self) -> ClientSession:
        if self._session is None:
            raise RuntimeError()
        return self._session

    async def set_parameters(self, params: SolveParameters) -> Any:
        payload = {
            "method": _METHOD_MAPPING.get(params.method, "euler"),
            "order": int(params.order),
            "userEquation": params.user_equation,
            "formattedEquation": params.formatted_equation,
            "initialX": float(params.initial_x),
            "initialY": list(map(float, params.initial_y)),
            "reachPoint": float(params.reach_point),
            "stepSize": float(params.step_size),
        }

        for attempt in range(self._max_retries):
            try:
                async with self._http.post(
                    f"{self._base_url}/users/{params.user_id}/solve", json=payload
                ) as response:
                    response.raise_for_status()
                    return await response.json()
            except (TimeoutError, ClientError):
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay)
                    continue
                raise

    async def set_user_settings(self, user_id: int, settings: UserSettings) -> str:
        payload = {
            "method": settings.method,
            "rounding": settings.rounding,
            "language": settings.language,
            "hints": settings.hints,
        }
        async with self._http.post(
            f"{self._base_url}/users/{user_id}/settings", params=payload
        ) as response:
            response.raise_for_status()
            return await response.text()

    async def get_user_settings(self, user_id: int, defaults: UserSettings) -> Any:
        async with self._http.get(f"{self._base_url}/users/{user_id}/settings") as response:
            if response.status == 404:
                return {
                    "method": defaults.method,
                    "rounding": defaults.rounding,
                    "language": defaults.language,
                    "hints": defaults.hints,
                }

            response.raise_for_status()
            return await self._parse_json_or_text(response)

    async def get_recent_applications(self, user_id: int) -> Any:
        async with self._http.get(f"{self._base_url}/users/{user_id}/applications") as response:
            if response.status == 404:
                return []

            response.raise_for_status()
            return await self._parse_json_or_text(response)

    async def get_results(self, application_id: Any) -> Any:
        async with self._http.get(
            f"{self._base_url}/applications/{application_id}/results"
        ) as response:
            response.raise_for_status()
            return await self._parse_json_or_text(response)

    async def get_application_status(self, application_id: Any) -> str:
        async with self._http.get(
            f"{self._base_url}/applications/{application_id}/status"
        ) as response:
            response.raise_for_status()
            return await response.text()

    async def wait_for_application_completion(self, application_id: Any) -> bool:
        current_delay = self._retry_delay

        for _ in range(int(self._request_timeout)):
            try:
                status = await self.get_application_status(application_id)
                if status == "completed":
                    return True
                elif status == "in_progress":
                    current_delay = min(current_delay * 1.5, self._max_retry_delay)
                elif status == "error":
                    return False
                await asyncio.sleep(current_delay)
            except Exception:
                await asyncio.sleep(current_delay)

        return False

    @staticmethod
    async def _parse_json_or_text(response: Any) -> Any:
        text = await response.text()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
