---
tags: [#backup, #scripts, #config]
---
## 🚀 **Использование backup скрипта:**

После создания файла вы можете использовать его:

bash

# Сделать скрипт исполняемым (если еще не сделано)
chmod +x scripts/backup-config.sh

# Использовать скрипт
./scripts/backup-config.sh                 # Инкрементальный бэкап (по умолчанию)
./scripts/backup-config.sh full           # Полный бэкап системы
./scripts/backup-config.sh ddev           # Только конфигурация DDEV
./scripts/backup-config.sh list           # Показать существующие бэкапы
./scripts/backup-config.sh help           # Показать справку

## ✅ **Проверка результата:**

bash

# Проверим, что файл создан и имеет правильные права
ls -la scripts/backup-config.sh

# Проверим, что он исполняемый
file scripts/backup-config.sh

# Тестируем скрипт
./scripts/backup-config.sh list