import requests
import os

SERVER_IP = os.getenv("SERVER_IP")
SERVER_URL = f"http://{SERVER_IP}:5000/query"

class Connection:
    def cursor(self):
        return Cursor()
    def commit(self):
        # на сервере коммит внутри API, тут нет действий
        pass
    def close(self):
        pass

class Cursor:
    def __init__(self):
        self._rows = None
        self.description = []

    def execute(self, sql, params=None):
        # ВСЕ запросы — и SELECT, и INSERT/UPDATE/DELETE — шлём на сервер
        resp = requests.post(SERVER_URL, json={"sql": sql, "params": params or []})
        if not resp.ok:
            # распечатаем, что пришло от сервера
            print("=== SERVER ERROR ===")
            # print("REQUEST JSON:", payload)
            print("STATUS CODE:", resp.status_code)
            print("RESPONSE BODY:", resp.text)
            resp.raise_for_status()
        resp.raise_for_status()

        # Если это SELECT — парсим строки, иначе игнорируем ответ
        if sql.strip().upper().startswith("SELECT"):
            self._rows = resp.json() or []
            if self._rows:
                self.description = [
                    (col, None, None, None, None, None, None)
                    for col in self._rows[0].keys()
                ]
            else:
                self.description = []
        return self

    def fetchall(self):
        return self._rows

    def fetchone(self):
        if not self._rows:
            return None
        # self._rows[0] — словарь, возвращаем кортеж его значений
        # .values() идут в том порядке, в каком курсор вернул колонки
        return tuple(self._rows[0].values())


def connect(db_path=None):
    # параметр db_path игнорируем
    return Connection()
