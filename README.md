# Парсер задач

Этот проект представляет собой парсер для загрузки и обработки задач с сайта math-ege.sdamgia.ru. Скрипт использует:
- [Selenium](https://www.selenium.dev/) для взаимодействия с веб-страницами,
- [Pillow](https://python-pillow.org/) для обработки изображений,
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) для парсинга HTML.

## Установка и запуск

1. Клонируйте репозиторий:
   ```
   git clone <URL вашего репозитория>
   ```

2. Перейдите в папку проекта:
   ```
   cd <название_репозитория>
   ```

3. (Опционально) Создайте и активируйте виртуальное окружение:
   - Windows:
     ```
     python -m venv venv
     venv\Scripts\activate
     ```
   - Unix/Mac:
     ```
     python3 -m venv venv
     source venv/bin/activate
     ```

4. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

5. Запустите скрипт:
   ```
   python main.py
   ```

## Настройка WebDriver

Убедитесь, что установлен ChromeDriver и его версия соответствует версии вашего браузера Google Chrome. Скачать ChromeDriver можно с [официального сайта](https://chromedriver.chromium.org/downloads).

## Логирование

Логи работы парсера записываются в файл `parser.log`.

## Структура проекта

- `main.py` – основной скрипт парсера.
- `requirements.txt` – файл с зависимостями.
- `README.md` – инструкция по установке и использованию.
- `.gitignore` – список файлов/папок, которые не нужно добавлять в репозиторий.