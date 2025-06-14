import logging
from geopy.geocoders import Nominatim
from geopy.adapters import AioHTTPAdapter

logger = logging.getLogger(__name__)

async def get_city_name(latitude: float, longitude: float) -> str:
    """Convert coordinates to city name using OpenStreetMap"""
    try:
        async with Nominatim(user_agent="dating_bot", adapter_factory=AioHTTPAdapter) as geolocator:
            location = await geolocator.reverse((latitude, longitude), exactly_one=True)
            if location:
                address = location.raw.get('address', {})
                return address.get('city', address.get('town', "Unknown City"))
        return "Unknown Location"
    except Exception as e:
        logger.error(f"Geocoding failed: {e}")
        return "Unknown Location"