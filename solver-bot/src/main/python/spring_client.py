import asyncio
import json
import os

from aiohttp import ClientError, ClientTimeout, ClientSession

REQUEST_TIMEOUT = 60
MAX_RETRIES = 3
RETRY_DELAY = 1
MAX_DELAY = 10


async def set_parameters(
    user_id,
    method,
    order,
    user_equation,
    formatted_equation,
    initial_x,
    initial_y,
    reach_point,
    step_size,
):
    method_mapping = {
        "euler": "euler",
        "midpoint": "midpoint",
        "heun": "heun",
        "runge_kutta": "rungeKutta",
        "dormand_prince": "dormandPrince",
    }

    payload = {
        "method": method_mapping.get(method, "euler"),
        "order": int(order),
        "userEquation": user_equation,
        "formattedEquation": formatted_equation,
        "initialX": float(initial_x),
        "initialY": list(map(float, initial_y)),
        "reachPoint": float(reach_point),
        "stepSize": float(step_size),
    }

    for attempt in range(MAX_RETRIES):
        try:
            timeout = ClientTimeout(total=REQUEST_TIMEOUT)
            async with ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{os.getenv('CLIENT_API_URL')}/users/{user_id}/solve", json=payload
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except (ClientError, asyncio.TimeoutError) as e:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
                continue
            raise e


async def set_user_settings(user_id, method, rounding, language, hints):
    payload = {
        "method": method,
        "rounding": rounding,
        "language": language,
        "hints": hints,
    }

    timeout = ClientTimeout(total=REQUEST_TIMEOUT)
    async with ClientSession(timeout=timeout) as session:
        async with session.post(
            f"{os.getenv('CLIENT_API_URL')}/users/{user_id}/settings", params=payload
        ) as response:
            response.raise_for_status()
            return await response.text()


async def get_user_settings(user_id, method, rounding, language, hints):
    timeout = ClientTimeout(total=REQUEST_TIMEOUT)
    async with ClientSession(timeout=timeout) as session:
        async with session.get(
            f"{os.getenv('CLIENT_API_URL')}/users/{user_id}/settings"
        ) as response:
            if response.status == 404:
                return {
                    "method": method,
                    "rounding": rounding,
                    "language": language,
                    "hints": hints,
                }

            response.raise_for_status()
            text = await response.text()
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                return text
            return data


async def get_recent_applications(user_id):
    timeout = ClientTimeout(total=REQUEST_TIMEOUT)
    async with ClientSession(timeout=timeout) as session:
        async with session.get(
            f"{os.getenv('CLIENT_API_URL')}/users/{user_id}/applications"
        ) as response:
            if response.status == 404:
                return []

            response.raise_for_status()
            text = await response.text()
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                return text
            return data


async def get_results(application_id):
    timeout = ClientTimeout(total=REQUEST_TIMEOUT)
    async with ClientSession(timeout=timeout) as session:
        async with session.get(
            f"{os.getenv('CLIENT_API_URL')}/applications/{application_id}/results"
        ) as response:
            response.raise_for_status()
            text = await response.text()
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                return text
            return data


async def get_application_status(application_id):
    timeout = ClientTimeout(total=REQUEST_TIMEOUT)
    async with ClientSession(timeout=timeout) as session:
        async with session.get(
            f"{os.getenv('CLIENT_API_URL')}/applications/{application_id}/status"
        ) as response:
            response.raise_for_status()
            return await response.text()


async def wait_for_application_completion(application_id):
    current_delay = RETRY_DELAY

    for _ in range(REQUEST_TIMEOUT):
        try:
            status = await get_application_status(application_id)
            if status == "completed":
                return True
            elif status == "in_progress":
                current_delay = min(current_delay * 1.5, MAX_DELAY)
            elif status == "error":
                return False
            await asyncio.sleep(current_delay)
        except Exception:
            await asyncio.sleep(current_delay)

    return False
