# Анализ оценок филиалов по звонкам и аудиобейджам

## Описание проекта
Построить сводные таблицы, графики и тепловые карты, отражающие:
 - средние оценки по каждому филиалу,
 - динамику оценок филиалов по неделям/месяцам,
 - сравнение филиалов по критериям оценки.

## Описание данных
Для анализа использована база данных по звонкам и аудиобейджам за период с 16.09.2025 по 23.09.2025, однако модель может работать на разных временных отрезках, выстраивая тренд по неделям.

## Используемые библиотеки
*pandas*, *numpy*, *seaborn*, *matplotlib*, *scipy*, *streamlit*, *statsmodels*, *os*, *sys*

## Результат
Получено приложение, которое выдает аналитику по выгрузке из базы данных в формате *.csv или *.xlsx.

Необходимый минимум столбцов для получения аналитики - `"call_id", "call_type", "branch_name", "organization_name", "score"`. По этим столбцам выдается аналитика по распределению оценок и сравнению средних значений оценок по филиалам. Отсутствие хотя бы одного из столбцов приводит к тому, что приложение не выдает никакой аналитики.

Кроме того, наличие столбца `"created_at"` в датасете открывает аналитику нееделельной динамики, а наличие столбца `"criteria_name"` — сравнительную аналитику филиалов по критериям оценки. Таким образом, для получения наиболее полной аналитики необходимо наличие в датасете столбцов: `"call_id", "call_type", "branch_name", "organization_name", "score", "created_at", "criteria_name"`. Можно загружать датасет за любой временной период: при наличии `"created_at"` и необходимого минимума столбцов приложение будет выдавать аналитику по недельной динамике.


## Как запустить проект
1. Требования
- Перед запуском убедитесь, что у вас установлено: Python 3.10 или выше; Git (если вы клонируете проект с GitHub); pip (менеджер пакетов Python).
- Проверить это можно в терминале:
 - python --version
 - pip --version
 - git --version 

2. Клонирование проекта
git clone https://github.com/EvgeniyKaduk/calls_analysis_intern_project.git

3. Запуск из каталога проекта
cd calls_analysis_intern_project

4. Установка и активация виртуального окружения
- python -m venv venv
- Активация окружения в Windows: venv\Scripts\activate
- Активация окружения в macOS/Linux: source venv/bin/activate

5. Установка зависимостей
- pip install -r requirements.txt
- Если вдруг появится ошибка с зависимостями, можно обновить проблемную библиотеку: pip install --upgrade pip <имя_библиотеки>

6. Проверка структуры проекта

project/
|
├── requirements.txt
│   
├── call_quality_analyzer/
│   ├── __init__.py
│   ├── data_preparation.py
│   ├── visualiztions.py
|   ├── analyzer.py
|   └── app.py

7. Запуск приложения в Streamlit из корневой папки проекта
  - streamlit run call_quality_analyzer/app.py
  - Перейти по ссылке в консоли: Local URL: http://localhost:8501 (либо автоматически запустится в браузере)

8. Обратить внимание на необходимые названия столбцов в загружаемом датасете
  - При отсуствиии необходимых для получения анализа столбцов в загруженных данных, система выдает уведомления и подсказки, чего не хватает для каждого аналитического блока.
  - Ограничение объема загружаемого файла - 200 Мб
  - Оптимальный вариант SQL-запроса для выгрузки датасета с необходимыми данными из базы данных:

  SELECT c.id call_id, c.created_at, c.call_type, b.name branch_name, o.name organization_name,
  e.score, cr.name criteria_name
  
  FROM call c 
  
  JOIN branch b ON b.id = c.fk_call_branch_id_branch
  
  JOIN organization o ON o.id = b.organization_id
  
  JOIN analysis a ON a.fk_analysis_call_id_call = c.id
  
  JOIN evaluation e ON e.fk_evaluation_analysis_id_analysis=a.id
  
  JOIN criteria cr ON cr.id = e.fk_evaluation_criteria_id_criteria;
