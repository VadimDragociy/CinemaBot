from aiohttp import ClientTimeout, ClientSession, ClientError
from typing import List, Dict, Optional, Any
import asyncio

DEFAULT_TIMEOUT = ClientTimeout(total=10)

async def _http_get_json(
    session: ClientSession,
    url: str, params: Optional[dict],
    headers: Optional[dict]
) -> Optional[dict]:
    try:
        async with session.get(url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT) as resp:
            resp.raise_for_status()
            return await resp.json()
    except Exception:
        return None


async def search_vk_video(session: ClientSession, title: str, vk_token: Optional[str] = None,
                          vk_api_version: str = "5.199", max_results: int = 3) -> List[Dict]:
    """
    Поиск видео ВКонтакте
    используем метод video.search API
    Возвращает список dict: {"title","url","source","meta"}
    """
    q = title.strip() + "фильм"
    results = []

    api_url = "https://api.vk.com/method/video.search"
    params = {
        "q": q,
        "count": max_results,
        "adult": 1,
        "access_token": vk_token,
        "v": vk_api_version,
        "sort": 2,  # релевантность
    }
    j = await _http_get_json(session, api_url, params=params, headers=None)
    if j and isinstance(j, dict):
        # проверим наличие ошибок
        if "error" in j:
            pass
        else:
            resp = j.get("response") or {}
            items = resp.get("items") or []
            for it in items[:max_results]:
                title_found = it.get("title") or q
                url = it.get("direct_url")
                results.append({"title": title_found, "url": url})
            if results:
                return results

    return results


async def search_all(
    title: str,
    vk_token: Optional[str] = None,
    timeout_seconds: int = 10
) -> Dict[str, List[Dict]]:
    """
    Параллельный запуск поиска на rutube и vk.
    Возвращает словарь: {"rutube": [...], "vk": [...]}
    """
    timeout = ClientTimeout(total=timeout_seconds)
    async with ClientSession(timeout=timeout) as session:
        tasks = [
            # asyncio.create_task(search_rutube(session, title)),
            asyncio.create_task(search_vk_video(session, title, vk_token=vk_token))
        ]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

        # извлечь результаты в том же порядке
        rutube_res = tasks[0].result() if not tasks[0].cancelled() else []
        vk_res = tasks[1].result() if not tasks[1].cancelled() else []
        return {"rutube": rutube_res, "vk": vk_res}


async def fetch_movie_by_query(
    api_key: str,
    query: str,
    page: int = 1,
    limit: int = 10,
    timeout: int = 30
) -> Optional[Dict[str, Any]]:
    """
    Асинхронно получает данные о фильме по query

    Args:
        api_key: API ключ для заголовка X-API-KEY
        query: Запрос для поиска
        page: Номер страницы (по умолчанию 1)
        limit: Количество результатов на странице (по умолчанию 10)
        timeout: Таймаут запроса в секундах (по умолчанию 30)

    Returns:
        Словарь с данными ответа или None в случае ошибки
    """
    base_url = "https://api.poiskkino.dev/v1.4/movie/search"
    params = {
        "page": page,
        "limit": limit,
        "query": query
    }

    headers = {
        "accept": "application/json",
        "X-API-KEY": api_key
    }

    try:
        async with ClientSession(timeout=ClientTimeout(total=timeout)) as session:
            async with session.get(
                url=base_url,
                params=params,
                headers=headers
            ) as response:

                response.raise_for_status()
                data = await response.json()

                print(f"Успешный запрос для query: {query}")

                return data

    except ClientError as e:
        print(f"Ошибка сети для query {query}: {e}")
    except Exception as e:
        print(f"Общая ошибка для query {query}: {e}")

    return None
