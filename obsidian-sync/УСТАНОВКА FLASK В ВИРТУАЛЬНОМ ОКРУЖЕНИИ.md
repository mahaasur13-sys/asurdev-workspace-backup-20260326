## 🔧 **УСТАНОВКА FLASK В ВИРТУАЛЬНОМ ОКРУЖЕНИИ:**

bash

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем Flask в виртуальное окружение
pip install flask

# Проверяем установку
pip list | grep flask

## 🚀 **ЗАПУСК ВЕБ-ИНТЕРФЕЙСА:**

bash

# Убедимся что виртуальное окружение активировано (должно быть (venv) в промпте)
source venv/bin/activate

# Запускаем веб-интерфейс
python3 vimana_web_ai.py