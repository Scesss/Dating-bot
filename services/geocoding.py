import logging
import httpx
from config import Config

logger = logging.getLogger(__name__)


async def get_city_name(latitude: float, longitude: float) -> str:
    """Get city name using Yandex Geocoder with Russian localization"""
    api_key = Config.YANDEX_GEOCODER_API_KEY
    if not api_key:
        logger.error("Yandex Geocoder API key not configured")
        return "Неизвестное местоположение"

    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": api_key,
        "format": "json",
        "lang": "ru_RU",
        "kind": "locality",
        "geocode": f"{longitude},{latitude}"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Extract city name from response
            features = data.get("response", {}).get("GeoObjectCollection", {}).get("featureMember", [])
            if features:
                # Find the most specific locality (city/town)
                for feature in features:
                    geo_object = feature.get("GeoObject", {})
                    meta_data = geo_object.get("metaDataProperty", {}).get("GeocoderMetaData", {})
                    kind = meta_data.get("kind")
                    if kind == "locality":
                        return geo_object.get("name", "Неизвестный город")

                # If no locality found, return the first result
                first_result = features[0].get("GeoObject", {})
                return first_result.get("name", "Неизвестный город")

            return "Местоположение не определено"
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return "Ошибка определения местоположения"
    
async def is_valid_city(city_query: str) -> bool:
    """Проверяет, что город существует (kind='locality') через Yandex Geocoder."""
    api_key = Config.YANDEX_GEOCODER_API_KEY
    if not api_key:
        logger.error("Yandex Geocoder API key not configured")
        return False

    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": api_key,
        "format": "json",
        "lang": "ru_RU",
        # убираем жёсткую фильтрацию по kind — пусть вернёт любой объект
        "results": 1,
        "geocode": city_query
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error(f"Geocoding error for '{city_query}': {e}")
        return False

    features = (
        data.get("response", {})
            .get("GeoObjectCollection", {})
            .get("featureMember", [])
    )
    # если нет ни одного GeoObject — город не распознан
    if not features:
        return False

    # любое попадание считаем корректным городом
    return True

async def get_city_name_from_query(city_query: str) -> str | None:
    """
    Делает геокодинг по строке запроса и возвращает каноническое название
    (из поля GeoObject.name). Если ничего не нашлось — возвращает None.
    """
    api_key = Config.YANDEX_GEOCODER_API_KEY
    if not api_key:
        logger.error("Yandex Geocoder API key not configured")
        return None

    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": api_key,
        "format": "json",
        "lang": "ru_RU",
        "results": 1,
        "geocode": city_query
    }
    try:
        resp = httpx.get(url, params=params, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        features = (
            data.get("response", {})
                .get("GeoObjectCollection", {})
                .get("featureMember", [])
        )
        if not features:
            return None

        # Берём первое GeoObject и его name
        geo = features[0].get("GeoObject", {})
        return geo.get("name")
    except Exception as e:
        logger.error(f"Geocoding error for text '{city_query}': {e}")
        return None