# OBD Virtual Cockpit (ELM327 → InfluxDB → Grafana)

Проект: виртуальный кокпит для мотоцикла/ТС на базе ELM327-over-WiFi + Raspberry Pi + InfluxDB + Grafana.

Основные функции:

- Подключение к ELM327 через TCP (elm327-proxy).
- Первичная инициализация (AT-команды, выбор протокола, проверка связи).
- Чтение VIN и базовое построение профиля ТС.
- Сканирование поддерживаемых PID (Mode 01) и сохранение профиля.
- Периодический опрос выбранных датчиков и запись телеметрии в InfluxDB.
- Одностраничный веб-интерфейс (SPA-лайт) для:
  - запуска/остановки опроса;
  - выбора датчиков;
  - просмотра статуса подключения;
  - отправки одиночных OBD-команд;
  - просмотра живого лога.
- Интеграция с Grafana для построения досок в реальном времени.

## 1. Структура проекта

```text
obd-virtual-cockpit/
├─ app/
│  ├─ Dockerfile
│  ├─ requirements.txt
│  ├─ main.py                 # FastAPI + фоновые задачи опроса
│  ├─ config.py               # загрузка конфигов/ENV
│  ├─ obd/
│  │  ├─ __init__.py
│  │  ├─ elm327_client.py     # низкоуровневый TCP-клиент к ELM327
│  │  ├─ vin_profile.py       # чтение VIN, профиль ТС
│  │  ├─ pid_scanner.py       # сканирование поддерживаемых PID
│  │  ├─ poller.py            # движок опроса датчиков и запись в Influx
│  │  ├─ models.py            # Pydantic-модели API/профилей
│  │  └─ utils.py
│  └─ web/
│     ├─ templates/
│     │  └─ index.html        # одностраничный UI
│     └─ static/
│        ├─ app.js
│        └─ styles.css
├─ config/
│  └─ pids/
│     └─ standard_mode01.json # стандартные PID Mode 01
├─ profiles/
│  └─ sample_profile.json     # пример профиля ТС
├─ logs/                      # логи приложения
├─ docker-compose.yml         # стек app + InfluxDB + Grafana
├─ .env.example
└─ README.md
```

## 2. Быстрый старт (локально на Raspberry Pi / OMV)

1. Скопировать проект на Raspberry:

```bash
scp -r obd-virtual-cockpit cosinusrus@192.168.1.51:~
```

или клонировать из GitHub на Raspberry:

```bash
git clone https://github.com/<USER>/<REPO>.git obd-virtual-cockpit
```

2. Зайти в каталог и создать `.env`:

```bash
cd obd-virtual-cockpit
cp .env.example .env
nano .env
```

- Указать правильные `ELM327_HOST` и `ELM327_PORT`.
- При необходимости поменять организацию/бакет/токен Influx.

3. Запустить стек через Docker Compose (на Pi напрямую):

```bash
docker compose up -d
```

Либо через OMV7 → Docker → Compose → указать путь к `docker-compose.yml` и стартовать стек в GUI.

4. Открыть:

- Веб-интерфейс приложения: `http://<IP_RPI>:8080`
- Grafana: `http://<IP_RPI>:3000` (логин/пароль из `.env`).

## 3. Настройка репозитория GitHub

### Локально на Mac

1. Распаковать архив:

```bash
unzip obd-virtual-cockpit.zip
cd obd-virtual-cockpit
```

2. Инициализировать git:

```bash
git init
git add .
git commit -m "Initial commit: OBD virtual cockpit skeleton"
```

3. Создать пустой репозиторий на GitHub (без README).

4. Привязать и запушить:

```bash
git remote add origin git@github.com:<USER>/<REPO>.git
git branch -M main
git push -u origin main
```

### Обновление на Raspberry через git

На Raspberry:

```bash
cd /srv/dev-disk-by-uuid-.../compose/obd-virtual-cockpit
git pull
docker compose pull   # если будут использоваться внешние образы
docker compose up -d --build
```

В OMV можно просто нажать "Re-deploy / up -d" после `git pull`.

(Дополнительно можно позже добавить watchtower для автообновления.)

## 4. Подключение VSCode

На Mac:

1. Установить расширение **Remote - SSH**.
2. Настроить SSH-подключение к Raspberry (`~/.ssh/config`).
3. В VSCode → `Remote Explorer` → SSH Targets → Raspberry → открыть папку `~/obd-virtual-cockpit` или путь на диске OMV.
4. Работать с кодом прямо на Pi или локально и пушить изменения на GitHub.

## 5. Архитектура приложения

Приложение построено на базе **FastAPI**:

- `/` — веб-интерфейс.
- `/api/status` — общие статусы (подключение к ELM, Influx, активные профили и т.п.).
- `/api/elm/connect` — первичная инициализация (ATZ, протокол, echo off и т.п.).
- `/api/elm/test` — пробный `0100` или `ATZ`.
- `/api/vin/read` — чтение VIN (Mode 09 PID 02) и создание/обновление профиля.
- `/api/vehicle/profile` — получение профиля ТС (VIN, блоки, поддерживаемые PID).
- `/api/pids/scan` — сканирование поддерживаемых PID Mode 01.
- `/api/polling/start` — запуск опроса выбранных PID.
- `/api/polling/stop` — остановка опроса.
- `/api/polling/config` — настройка частоты опроса, списка датчиков.
- `/api/command` — отправка произвольной OBD-команды (сырые строки: `010C`, `0902`, `ATZ`).
- `/api/logs/stream` — SSE/WebSocket (упрощённо: long-poll / периодический fetch) для живого лога.

### Профили ТС

- Хранятся в `profiles/<VIN>.json`.
- Структура (упрощённо):

```json
{
  "vin": "JYARM1234ABCDEFGH",
  "created_at": "...",
  "updated_at": "...",
  "ecus": ["ECU", "ABS", "TFT"],
  "supported_pids": {
    "01": ["0C", "0D", "05", "0F", "11"]
  }
}
```

### PID-конфигурация

Файл `config/pids/standard_mode01.json` содержит описания стандартных PID Mode 01:

- PID
- Название
- Единицы измерения
- Формула преобразования из сырых байтов

Можно расширять для конкретного мотоцикла.

## 6. Grafana + InfluxDB

Приложение пишет данные в InfluxDB в measurement, например: `obd_metrics`.

Пример полей/тегов:

- `vin` (tag)
- `pid` (tag)
- `name` (tag, например `engine_rpm`)
- `value` (float)
- `unit` (tag, например `rpm`)

В Grafana добавляем InfluxDB как datasource и строим:

- RPM / скорость / температура / TPS по времени.
- Можно собрать дашборд "виртуальный кокпит".

## 7. Дальнейшее развитие

- Расширить список PID (Mode 01 + 09).
- Добавить UDS/ISO-TP диалоги (для специфичных блоков).
- Автообнаружение блоков (по ответам на запросы, по CAN ID).
- Больше диагностических тестов (MIL, DTC, freeze frame).
- UI для экспорта профиля ТС и бэкапа настроек.

---

Дальше можно пошагово дорабатывать:

1. Тест подключения к ELM327 (через уже готовую подсистему elm327-proxy).
2. Реальный опрос PID по твоему мотоциклу (MT-07 2023).
3. Обновление профиля ТС.
4. Настройка канала Influx → Grafana под реальные данные.
5. Допиливание веб-UI под нужды "дилерского" сканера.
