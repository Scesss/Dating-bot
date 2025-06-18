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
        "kind": "locality",  # нас интересуют только населённые пункты
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
    if not features:
        return False

    # Проверяем, что хотя бы один результат имеет kind='locality'
    for member in features:
        kind = (
            member.get("GeoObject", {})
                  .get("metaDataProperty", {})
                  .get("GeocoderMetaData", {})
                  .get("kind")
        )
        if kind == "locality":
            return True

    return False