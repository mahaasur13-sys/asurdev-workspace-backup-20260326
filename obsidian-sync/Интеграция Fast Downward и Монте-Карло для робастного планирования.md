---
tags:
  - AI
  - planning
  - PDDL
  - FastDownward
  - MonteCarlo
  - Python
  - automation
  - robotics
aliases: [Робастное планирование, План и Проверка]
---
# Интеграция Fast Downward и Монте-Карло для робастного планирования

&gt; [!abstract] Зачем это нужно?
&gt; **Fast Downward** строит идеальные планы в предсказуемом мире. Реальный мир — стохастический (случайный), где действия могут провалиться. Эта заметка описывает методологию **"Спланируй, затем проверь"**: мы используем Fast Downward для генерации оптимальной стратегии, а затем с помощью симуляций **Монте-Карло** оцениваем ее реальные шансы на успех.

---

## Концептуальная архитектура

1. **Детерминированный планировщик (`Fast Downward`)**: Генерирует "идеальный" план на основе PDDL-модели.
2. **Стохастический симулятор (`Python/NumPy`)**: Модель "реального мира", где каждое действие имеет вероятность успеха.
3. **Оркестратор (`Python-скрипт`)**: Скрипт, который сначала вызывает планировщик, получает план, а затем многократно прогоняет его через симулятор для сбора статистики.

## Workflow: "Спланируй, затем проверь"

### Шаг 1: Создание PDDL-моделей

Создайте в вашем хранилище два файла: `domain.pddl` и `problem.pddl`.

#### `domain.pddl`
pddl
(define (domain blocks-world)
  (:requirements :strips)
  (:predicates (on-table ?x)
               (clear ?x)
               (holding ?x)
               (hand-empty))

  (:action pick-up
    :parameters (?b)
    :precondition (and (clear ?b) (on-table ?b) (hand-empty))
    :effect (and (not (on-table ?b))
                 (not (clear ?b))
                 (not (hand-empty))
                 (holding ?b)))

  (:action put-down
    :parameters (?b)
    :precondition (holding ?b)
    :effect (and (not (holding ?b))
                 (hand-empty)
                 (clear ?b)
                 (on-table ?b)))


#### `problem.pddl`

### Шаг 2: Создание скрипта-оркестратора

Создайте Python-скрипт `run_robust_planner.py` и поместите его в корень вашего хранилища.

&gt; [!warning] Предварительные требования
&gt; У вас должен быть установлен `python3`, `numpy` (`pip install numpy`), и [[FastDownward|Fast Downward]] должен быть скомпилирован и находиться в папке `fast-downward` в корне хранилища.

#### `run_robust_planner.py`
ChatGPT 5 & [🅼🅹] | DeepSeek | GPT4 ✹, [10.09.2025 22:21]
Конечно! Вот готовая заметка для Obsidian. Она структурирована с использованием Markdown, содержит YAML-заголовки для метаданных, код, примеры и даже готовые команды для плагина `Shell Commands`.

Просто скопируйте весь текст ниже и вставьте его в новую заметку в вашем хранилище Obsidian.

---

---
tags:
  - AI
  - planning
  - PDDL
  - FastDownward
  - MonteCarlo
  - Python
  - automation
  - robotics
aliases: [Робастное планирование, План и Проверка]
---

# Интеграция Fast Downward и Монте-Карло для робастного планирования

&gt; [!abstract] Зачем это нужно?
&gt; **Fast Downward** строит идеальные планы в предсказуемом мире. Реальный мир — стохастический (случайный), где действия могут провалиться. Эта заметка описывает методологию **"Спланируй, затем проверь"**: мы используем Fast Downward для генерации оптимальной стратегии, а затем с помощью симуляций **Монте-Карло** оцениваем ее реальные шансы на успех.

---

## Концептуальная архитектура

1. **Детерминированный планировщик (`Fast Downward`)**: Генерирует "идеальный" план на основе PDDL-модели.
2. **Стохастический симулятор (`Python/NumPy`)**: Модель "реального мира", где каждое действие имеет вероятность успеха.
3. **Оркестратор (`Python-скрипт`)**: Скрипт, который сначала вызывает планировщик, получает план, а затем многократно прогоняет его через симулятор для сбора статистики.

## Workflow: "Спланируй, затем проверь"

### Шаг 1: Создание PDDL-моделей

Создайте в вашем хранилище два файла: `domain.pddl` и `problem.pddl`.

#### `domain.pddl`
pddl
(define (domain blocks-world)
  (:requirements :strips)
  (:predicates (on-table ?x)
               (clear ?x)
               (holding ?x)
               (hand-empty))

  (:action pick-up
    :parameters (?b)
    :precondition (and (clear ?b) (on-table ?b) (hand-empty))
    :effect (and (not (on-table ?b))
                 (not (clear ?b))
                 (not (hand-empty))
                 (holding ?b)))

  (:action put-down
    :parameters (?b)
    :precondition (holding ?b)
    :effect (and (not (holding ?b))
                 (hand-empty)
                 (clear ?b)
                 (on-table ?b)))
)

#### `problem.pddl`
pddl
(define (problem two-blocks)
  (:domain blocks-world)
  (:objects a b)
  (:init (on-table a)
         (on-table b)
         (clear a)
         (clear b)
         (hand-empty))
  (:goal (and (holding a)))
)

### Шаг 2: Создание скрипта-оркестратора

Создайте Python-скрипт `run_robust_planner.py` и поместите его в корень вашего хранилища.

&gt; [!warning] Предварительные требования
&gt; У вас должен быть установлен `python3`, `numpy` (`pip install numpy`), и [[FastDownward|Fast Downward]] должен быть скомпилирован и находиться в папке `fast-downward` в корне хранилища.

#### `run_robust_planner.py`
python
import subprocess
import numpy as np
import sys
import os

def get_plan(domain_file, problem_file, fd_path):
    """Вызывает Fast Downward и возвращает найденный план."""
    try:
        result = subprocess.run(
            [fd_path, domain_file, problem_file, '--search', 'astar(lmcut())'],
            capture_output=True, text=True, check=True, timeout=30
        )
        plan = []
        parsing = False
        for line in result.stdout.split('\n'):
            if "Solution found!" in line:
                parsing = True
                continue
            if "Plan length" in line:
                break
            if parsing and line.strip():
                action = line.split('(')[1].split(')')[0]
                plan.append(action)
        
        if not plan:
            print("План не найден в выводе Fast Downward.")
            return None
            
        print(f"Найденный детерминированный план: {plan}")
        return plan
        
    except FileNotFoundError:
        print(f"Ошибка: Не найден исполняемый файл Fast Downward по пути '{fd_path}'")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при вызове


Fast Downward:\n{e.stderr}")
        return None
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        return None

def run_simulation(plan):
    """Прогоняет один раз план через симулятор с вероятностными действиями."""
    # Упрощенная модель мира
    state = {'hand_empty': True, 'a_on_table': True, 'b_on_table': True}
    
    for action_str in plan:
        action_name = action_str.split()[0]
        
        # Действие 'pick-up' имеет 95% шанс на успех
        if action_name == 'pick-up':
            if np.random.rand() > 0.95:
                # print("Действие 'pick-up' провалилось!")
                return False # Провал симуляции
        
        # Действие 'put-down' имеет 99% шанс на успех
        elif action_name == 'put-down':
            if np.random.rand() > 0.99:
                # print("Действие 'put-down' провалилось!")
                return False
        
    # Считаем, что если все действия выполнены (и не провалились), цель достигнута
    return True

def evaluate_plan_with_monte_carlo(plan, num_simulations=10000):
    """Запускает N симуляций и оценивает вероятность успеха плана."""
    if not plan:
        return 0.0
        
    success_count = 0
    for _ in range(num_simulations):
        if run_simulation(plan):
            success_count += 1
            
    return success_count / num_simulations

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Использование: python run_robust_planner.py <domain.pddl> <problem.pddl>")
        sys.exit(1)
        
    domain_pddl_path = sys.argv[1]
    problem_pddl_path = sys.argv[2]
    
    # Определение пути к Fast Downward относительно скрипта
    script_dir = os.path.dirname(os.path.realpath(__file__))
    fd_executable_path = os.path.join(script_dir, 'fast-downward', 'fast-downward.py')

    my_plan = get_plan(domain_pddl_path, problem_pddl_path, fd_executable_path)
    
    if my_plan:
        success_probability = evaluate_plan_with_monte_carlo(my_plan, 10000)
        print("---")
        print(f"РЕЗУЛЬТАТ СИМУЛЯЦИИ МОНТЕ-КАРЛО:")
        print(f"Вероятность успеха плана: {success_probability:.2%}")

### Шаг 3: Интеграция в Obsidian

Теперь вы можете запускать весь процесс прямо из Obsidian с помощью плагина [[obsidian-shellcommands|Shell Commands]].

1. Установите плагин `Shell Commands`.
2. Создайте новую команду со следующими параметрами:
    *   **Command name:** `Запустить Робастный Планировщик`
    *   **Shell command:** `python3 "{{vault_path}}/run_robust_planner.py" "{{vault_path}}/domain.pddl" "{{vault_path}}/problem.pddl"`
3. Сохраните команду.

Теперь вы можете вызвать палитру команд (`Ctrl/Cmd + P`), найти "Запустить Робастный Планировщик" и выполнить. Результат появится в модальном окне.

&gt; [!success] Ожидаемый результат выполнения
&gt; 
> Найденный детерминированный план: ['pick-up a']
> ---
> РЕЗУЛЬТАТ СИМУЛЯЦИИ МОНТЕ-КАРЛО:
> Вероятность успеха плана: 95.12%
> 
---

## Дальнейшее развитие

- **Параметризация**: Модифицируйте скрипт, чтобы он принимал количество симуляций или вероятности успеха в качестве аргументов командной строки.
- **Сравнение планов**: Используйте Fast Downward для генерации нескольких планов (например, с разными эвристиками) и запускайте симуляцию для каждого, чтобы найти самый надежный, а не самый короткий план.
- **Визуализация**: Сохраняйте результаты симуляций в CSV-файл и используйте плагины вроде `Obsidian Charts` для построения графиков.
- 
### Шаг 3: Интеграция в Obsidian

Теперь вы можете запускать весь процесс прямо из Obsidian с помощью плагина [[obsidian-shellcommands|Shell Commands]].

1. Установите плагин `Shell Commands`.
2. Создайте новую команду со следующими параметрами:
    *   **Command name:** `Запустить Робастный Планировщик`
    *   **Shell command:** `python3 "{{vault_path}}/run_robust_planner.py" "{{vault_path}}/domain.pddl" "{{vault_path}}/problem.pddl"`
3. Сохраните команду.

Теперь вы можете вызвать палитру команд (`Ctrl/Cmd + P`), найти "Запустить Робастный Планировщик" и выполнить. Результат появится в модальном окне.

&gt; [!success] Ожидаемый результат выполнения
&gt; 

---

## Дальнейшее развитие

- **Параметризация**: Модифицируйте скрипт, чтобы он принимал количество симуляций или вероятности успеха в качестве аргументов командной строки.
- **Сравнение планов**: Используйте Fast Downward для генерации нескольких планов (например, с разными эвристиками) и запускайте симуляцию для каждого, чтобы найти самый надежный, а не самый короткий план.
- **Визуализация**: Сохраняйте результаты симуляций в CSV-файл и используйте плагины вроде `Obsidian Charts` для построения графиков.
