# Messaging Router API

Purchase event → CRM (Odoo) → LINE / Telegram / WhatsApp

## Быстрый старт

```bash
cd messaging_api
cp .env.example .env        # заполни токены
pip install -r requirements.txt
uvicorn main:app --reload
```

Swagger UI: http://localhost:8000/docs

---

## Структура проекта

```
messaging_api/
├── main.py                  # FastAPI app
├── core/
│   ├── config.py            # Настройки (env)
│   └── database.py          # Async SQLAlchemy
├── models/
│   ├── user.py              # ORM: users
│   ├── channel.py           # ORM: channels (line/tg/wa)
│   ├── purchase.py          # ORM: purchases
│   └── schemas.py           # Pydantic schemas
├── services/
│   ├── user_service.py      # DB операции с пользователями
│   ├── router.py            # Messaging Router (LINE → TG → WA)
│   └── odoo.py              # Odoo XML-RPC интеграция
├── adapters/
│   ├── telegram.py          # Telegram Bot API
│   ├── line.py              # LINE Messaging API
│   └── whatsapp.py          # Meta WhatsApp Business API
└── routers/
    ├── users.py             # POST /users, GET /users/{phone}
    ├── channels.py          # POST /channels/bind, POST /channels/send
    ├── purchases.py         # POST /purchases
    └── webhooks.py          # POST /webhooks/{telegram,line,whatsapp}
```

---

## API Endpoints

### Пользователи
| Method | Path | Описание |
|--------|------|----------|
| POST | `/users/` | Зарегистрировать пользователя |
| GET | `/users/{phone}` | Получить профиль |
| GET | `/users/{phone}/channels` | Список привязанных каналов |

### Привязка каналов
| Method | Path | Описание |
|--------|------|----------|
| POST | `/channels/bind` | Привязать LINE/Telegram/WhatsApp |
| POST | `/channels/send` | Отправить сообщение по телефону |

### Покупки (основной flow)
| Method | Path | Описание |
|--------|------|----------|
| POST | `/purchases/` | Событие покупки (POS → API) |

### Вебхуки от мессенджеров
| Method | Path | Описание |
|--------|------|----------|
| POST | `/webhooks/telegram` | Telegram webhook |
| POST | `/webhooks/line` | LINE webhook |
| GET/POST | `/webhooks/whatsapp` | WhatsApp verification + messages |

---

## Привязка каналов

### Telegram
Пользователь пишет боту: `/start +995555123456`  
→ chat_id автоматически привязывается к телефону.

### LINE
Пользователь пишет боту: `/bind +995555123456`  
→ LINE userId привязывается к телефону.

### WhatsApp
Любое входящее сообщение от номера автоматически создаёт/обновляет привязку.

---

## Purchase Flow (POS → сообщение)

```
POST /purchases/
{
  "phone": "+995555123456",
  "amount": 150.00,
  "store_id": "store_tbilisi_01"
}
```

1. Находим/создаём пользователя
2. Upsert контакт в Odoo + начисляем баллы
3. Router выбирает канал: LINE → Telegram → WhatsApp
4. Отправляем сообщение
5. Сохраняем покупку с указанием использованного канала
