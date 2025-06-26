import math

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Возвращает расстояние между двумя точками на Земле (в километрах),
    заданными широтой и долготой, используя формулу Хаверсина.
    """
    # радиус Земли в км
    R = 6371.0

    # перевести градусы в радианы
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
