# MikroTik hEX S (E60iUGS) — Первое включение: гайд с нуля

> **Модель:** MikroTik hEX S (E60iUGS), обновлённая версия 2025 г.
> **RouterOS:** v7 (предустановлен, Level 4)
> **Актуальность:** март 2026
> **Сложность:** для новичков

---

## 📋 Навигация по гайду

| # | Раздел | Что сделать |
|---|---|---|
| 1 | [Подготовка](#1-подготовка-железа) | Распаковать, подключить кабели, подать питание |
| 2 | [Сброс в заводские](#2-сброс-в-заводские-настройки) | Чистый сброс для уверенности |
| 3 | [Вход в управление](#3-вход-в-управление) | Winbox / Web-интерфейс / SSH |
| 4 | [Quick Set — базовая настройка](#4-quick-set--базовая-настройка) | WAN, LAN, DHCP за 3 минуты |
| 5 | [Обновление RouterOS и прошивки](#5-обновление-routeros-и-routerboard) | Последний этап, когда интернет уже есть |
| 6 | [Проверка](#6-проверка-всё-ли-работает) | Тесты, чеклист |
| 7 | [Troubleshooting](#7-troubleshooting) | Если что-то не заработало |

---

## 1. Подготовка железа

### Комплект поставки

- hEX S E60iUGS
- Блок питания **24V DC, 0.8A** (или PoE-in на ether1)
- Пластиковая стяжка / настольная подставка

### Характеристики, которые важно знать

| Параметр | Значение |
|---|---|
| CPU | Dual-core ARM 64-bit, 950 MHz |
| RAM | 512 MB DDR3 |
| NAND | 128 MB |
| Ethernet | 5× Gigabit (10/100/1000) |
| SFP | 1× 2.5G (поддерживает модули 1G и 2.5G) |
| PoE-in | **ether1** — 12–57V (802.3af/at + passive) |
| PoE-out | **ether5** — passive PoE до 57V, макс 0.5A |
| USB | USB 3.0 (для LTE-модема или накопителя) |
| Питание | DC jack (18–57V) или PoE-in на ether1 |

### Подключение кабелей (до включения!)

```
                    ┌──────────────┐
  Провайдер ───────►│  ether1       │◄── (INTERNET, PoE-in)
  (RJ45 от провайдера) │  (marked)    │
                    │              │
                    │  ether2 ─────┼──► ПК / ноутбук
                    │  ether3      │◄── (любой LAN-устройство)
                    │  ether4      │
                    │  ether5 ─────┼──► (PoE-out, можно питать AP)
                    │  SFP1  ──────┼──► SFP-модуль (оптика 2.5G)
                    │              │
                    └──────┬───────┘
                           │ DC 24V
                        ───┴───
                         ( БП )
```

> ⚠️ **Важно:** hEX S E60iUGS **НЕ имеет Wi-Fi**. Это чисто проводной роутер. Если нужна беспроводная сеть — подключи точку доступа в ether2–ether5 (или в ether5 с PoE-out).

---

## 2. Сброс в заводские настройки

### Зачем сбрасывать?

Роутер приходит с предустановленным конфигом по умолчанию. Если он новый — сброс **не обязателен**, но рекомендуется для уверенности. Если роутер б/у — **обязательно**.

### Вариант А — Через Winbox (рекомендуется)

1. Подключи ПК к **ether2** (или любому порту, кроме ether1)
2. Открой Winbox → вкладка `Neighbors` → найди роутер → нажми `Connect`
3. `System` → `Reset Configuration`
4. ✅ Поставь **Reset Boot Configuration**
5. ✅ Поставь **No Default Configuration** (чистый сброс, без конфига)
6. Нажми **Reset Configuration**
7. Роутер перезагрузится (~1 минута)

### Вариант Б — Через терминал (SSH / Terminal)

```cli
/system reset-configuration no-defaults=yes skip-backup=yes
```

После сброса роутер:
- IP: `192.168.88.1`
- Login: `admin`
- Password: (пусто)
- DHCP-сервер включён на bridge
- Firewall с NAT

---

## 3. Вход в управление

### Способ 1 — Winbox (самый удобный)

1. Скачай Winbox: `https://mt.lv/winbox` (или с `mikrotik.com`)
2. Подключи ПК к ether2–ether5
3. ПК должен получить IP `192.168.88.x` по DHCP (подожди ~10 сек)
4. Открой Winbox → `Neighbors` → MAC-адрес роутера → `Connect`

```
Login:    admin
Password: (пусто)
```

### Способ 2 — Web-интерфейс

```
http://192.168.88.1
```

Откроется страница управления (не путать с Quick Set — это разные страницы).

### Способ 3 — SSH / Terminal

```bash
ssh admin@192.168.88.1
```

---

## 4. Quick Set — базовая настройка

> **Важно:** Quick Set работает одинаково в Winbox и через браузер. Открой `http://192.168.88.1` и выбери **Quick Set** в меню слева.

### Quick Set — заполнить так:

```
┌─────────────────────────────────────────────────┐
│  Quick Set                                      │
├─────────────────────────────────────────────────┤
│  Режим (Mode):         [Router ▼]               │
│                                                  │
│  Internet (WAN):                                 │
│    Source NAT:          [✓ Включен]              │
│    Port:                [ether1 ▼]               │
│    Get Address:         [Automatic (DHCP) ▼]    │
│                                                  │
│  Local Network:                                  │
│    Address:             [192.168.88.1/24]        │
│    DHCP Server:         [✓ Enabled]             │
│    DHCP Pool:           [192.168.88.10-..]      │
│                                                  │
│  WiFi:              [Выключено / Not present]   │
│                                                  │
│                    [Apply]                       │
└─────────────────────────────────────────────────┘
```

### Что делает Quick Set автоматически

Эти настройки появятся в конфиге после нажатия **Apply**:

| Что создаётся | Куда смотреть |
|---|---|
| Bridge (lan-bridge) с ether2–ether5 | `/interface bridge print` |
| IP `192.168.88.1/24` на bridge | `/ip address print` |
| DHCP-сервер на bridge | `/ip dhcp-server print` |
| NAT (src-nat) на ether1 | `/ip firewall nat print` |
| DHCP-клиент на ether1 | `/ip dhcp-client print` |
| DNS от провайдера | `/ip dns print` |

---

## 5. Обновление RouterOS и RouterBOARD

> ⚠️ **Это нужно делать ПОСЛЕ того, как заработал интернет (шаг 4).**
> ⚠️ **Два разных обновления: RouterOS (ОС) и RouterBOARD (загрузчик/firmware).**

### Этап А — RouterOS (Операционная система)

```cli
# 1. Проверить обновления
/system package update check-for-updates once

# 2. Если обновление есть — установить
/system package update install

# 3. Перезагрузить
/system reboot
```

> Документация MikroTik (обновлена **12 января 2026**):[^1]
> *"Commands executed in this menu will take place only on restart of the router."*
> Это значит: `install` скачает пакет, но применится только после `/system reboot`.

### Этап Б — RouterBOARD Firmware (загрузчик)

```cli
# После перезагрузкиRouterOS — обновить firmware
/system routerboard upgrade

# Ещё раз перезагрузить
/system reboot
```

### Всё вместе (одной последовательностью)

```cli
/system package update check-for-updates once
:delay 2s
/system package update install
/system reboot
# ─── Ждём загрузки (~1-2 мин) ───
/system routerboard upgrade
/system reboot
```

### Проверить версии после обновления

```cli
/system package print           # RouterOS версия
/system routerboard print       # Firmware версия
```

Ожидаемый результат: `factory-firmware` = `current-firmware` = `upgrade-firmware`.

> 💡 **Автоапгрейд:** можно включить `/system routerboard settings set auto-upgrade=yes` — тогда роутер сам обновит firmware при следующих перезагрузкахRouterOS.

---

## 6. Проверка: всё ли работает

### Чеклист команд (все через Winbox → Terminal или SSH)

```cli
# 1. Порты и линки
/interface print
```

**Ожидаемо:** ether1–ether5 все в статусе `R` (running), SFP1 — зависит от модуля.

```cli
# 2. IP-адреса
/ip address print
```

**Ожидаемо:**
- `192.168.88.1/24` на `bridge` или `ether2` — LAN
- IP на `ether1` от провайдера (DHCP) — WAN

```cli
# 3. Шлюз по умолчанию
/ip route print
```

**Ожидаемо:** строка `dst-address=0.0.0.0/0 gateway=<IP провайдера>`.

```cli
# 4. NAT
/ip firewall nat print
```

**Ожидаемо:** минимум одна запись `chain=srcnat out-interface=ether1 action=masquerade`.

```cli
# 5. Тест интернета
ping 8.8.8.8
```

**Ожидаемо:** ответы от `8.8.8.8`.

```cli
# 6. Тест DNS
ping google.com
```

**Ожидаемо:** резолвится в IP и приходят ответы.

---

## 7. Troubleshooting

### ПК не получает IP от DHCP

```
Проверить: /ip dhcp-server print
Включить: /ip dhcp-server enable numbers=0
```

### Нет IP на ether1 (WAN)

```
Проверить: /ip dhcp-client print
Включить: /ip dhcp-client enable numbers=0
```

### Нет интернета, но пинг 8.8.8.8 работает

```
# DNS не резолвит
Проверить: /ip dns print
Включить: /ip dns set allow-remote-requests=yes servers=8.8.8.8,1.1.1.1
```

### Роутер не пингуется по 192.168.88.1

- Проверь, что ПК в той же подсети (`192.168.88.x`)
- Проверь кабель (замени на другой)
- Отключи VPN на ПК
- Подключись через Winbox по MAC (работает даже без IP)

---

## ❌ Что было некорректно в оригинальном гайде

| Проблема | Пояснение |
|---|---|
| `/system package update` | В RouterOS 7 это **подменю** `/system package update`, а не одна команда. Правильно: `/system package update check-for-updates once`, затем `/system package update install` |
| Отсутствовал этап RouterBOARD firmware | Обновление RouterOS **НЕ обновляет** firmware загрузчика. Это отдельный шаг: `/system routerboard upgrade` + reboot |
| Не уточнено, что нужен **двойной reboot** | Первый reboot — для применения нового RouterOS. Второй — после `routerboard upgrade` |
| `auto-upgrade=yes` не упомянут | Полезная настройка: `/system routerboard settings set auto-upgrade=yes` |
| Не акцентирована разница RouterOS 6 vs 7 | hEX S E60iUGS 2025 поставляется с RouterOS 7. Все команды в гайде для **v7** |
| Не упомянуты некоторые порты PoE | ether1 — PoE-in; ether5 — PoE-out (до 57V passive) |

---

## Что дальше?

Когда базовый гайд пройден и интернет работает, можно настроить:

| Следующий шаг | Что делать |
|---|---|
| **VLAN 10/20** | Изоляция сетей (управление / гости) |
| **Firewall** | Базовые правила безопасности |
| **VPN** | WireGuard или OpenVPN |
| **Bonding** | Объединение портов |
| **CAPsMAN** | Управление точками доступа |

---

## Источники

[^1]: MikroTik RouterOS Packages Documentation — обновлена 12 января 2026, `https://help.mikrotik.com/docs/spaces/ROS/pages/40992872/Packages`
