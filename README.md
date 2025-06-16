# Telegram Dating Bot - Final Version

## Структура проекта
```
telegram_dating_bot_final/
├── main.py
├── config.py
├── requirements.txt
├── database/
│   └── db.py
├── fsm/
│   └── states.py
├── handlers/
│   ├── menu.py
│   ├── profile.py
│   └── browse.py
├── keyboards/
│   ├── reply.py
│   └── inline.py
└── utils/
    └── utils.py
```

## Установка на Mac OS

1. **Распаковка**  
   ```bash
   cd ~/Downloads
   unzip telegram_dating_bot_final.zip
   cd telegram_dating_bot_final
   ```

2. **Виртуальное окружение**  
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Зависимости**  
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```

4. **Токен**  
   В `config.py` замените `YOUR_BOT_TOKEN_HERE` на токен от BotFather.

5. **Запуск**  
   ```bash
   python main.py
   ```
   Увидите `Bot started`. Бот готов к работе.

## Использование  
- `/start` → заполнение анкеты (имя, пол, описание, возраст, город, предпочтения).  
- Главное меню (кнопки):  
  - 👤 Моя анкета → просмотр и редактирование.  
  - 🔍 Просмотр анкет → лайк 👍 или пропуск 👎.  
  - 💛 Кто меня лайкнул → ответный лайк + получение ссылки @username при матче.  
