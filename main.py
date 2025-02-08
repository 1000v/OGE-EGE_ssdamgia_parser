import re
import json
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from bs4 import BeautifulSoup

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parser.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_directory(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f"Создана директория: {path}")
    except Exception as e:
        logger.error(f"Ошибка при создании директории {path}: {e}")
        raise

def adjust_window_size(driver):
    width = driver.execute_script(
        "return Math.max(document.body.scrollWidth, document.documentElement.scrollWidth);"
    )
    height = driver.execute_script(
        "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);"
    )
    driver.set_window_size(width + 100, height + 100)  # Добавляем отступ

def screenshot_component_html(driver, html_path, image_path):
    try:
        absolute_path = os.path.abspath(html_path)
        driver.get(f"file:///{absolute_path}")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        time.sleep(1)
        adjust_window_size(driver)
        time.sleep(1)
        element = driver.find_element(By.TAG_NAME, 'body')
        element.screenshot(image_path)
        trim_screenshot(image_path)
        logger.info(f"Скриншот успешно сохранен: {image_path}")
    except Exception as e:
        logger.error(f"Ошибка при создании скриншота {image_path}: {e}")
        raise

def trim_screenshot(image_path, padding=25):
    """
    Обрезает скриншот по границам контента с отступами
    """
    try:
        # Открываем изображение
        with Image.open(image_path) as img:
            # Конвертируем в RGB если изображение в другом формате
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Получаем данные пикселей
            pixels = img.load()
            width, height = img.size
            
            # Находим верхнюю границу (первый непустой пиксель)
            top = 0
            for y in range(height):
                for x in range(width):
                    r, g, b = pixels[x, y]
                    if not (r > 250 and g > 250 and b > 250):  # Не белый
                        top = max(0, y - padding)
                        break
                if top:
                    break
            
            # Находим нижнюю границу (последний непустой пиксель)
            bottom = height
            for y in range(height - 1, -1, -1):
                for x in range(width):
                    r, g, b = pixels[x, y]
                    if not (r > 250 and g > 250 and b > 250):  # Не белый
                        bottom = min(height, y + padding)
                        break
                if bottom != height:
                    break
            
            # Обрезаем изображение
            cropped = img.crop((0, top, width, bottom))
            cropped.save(image_path)
            logger.info(f"Изображение успешно обрезано: {image_path}")
            
    except Exception as e:
        logger.error(f"Ошибка при обрезке изображения {image_path}: {e}")
        raise

def take_screenshot(driver, element, output_path):
    try:
        logger.info(f"Попытка сделать скриншот: {output_path}")
        
        # Прокручиваем к элементу
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(1)  # Ждем завершения прокрутки
        
        # Получаем размеры элемента
        size = element.size
        location = element.location
        
        # Увеличиваем высоту на 100 пикселей
        driver.execute_script("""
            arguments[0].style.marginBottom = '500px';
        """, element)
        
        # Делаем скриншот элемента
        element.screenshot(output_path)
        
        # Обрезаем лишние белые поля
        trim_screenshot(output_path)
        
        logger.info(f"Скриншот успешно сохранен: {output_path}")
    except Exception as e:
        logger.error(f"Ошибка при создании скриншота {output_path}: {e}")
        raise

def save_component_html(html_content, base_path, filename):
    try:
        # Создаем директорию для компонента, если она не существует
        component_dir = os.path.join(base_path, os.path.dirname(filename))
        if not os.path.exists(component_dir):
            os.makedirs(component_dir)
            
        html_path = os.path.join(base_path, filename.replace('/', os.path.sep))
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ margin: 0; padding: 20px; }}
                img {{ max-width: 100%; height: auto; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_template)
        return html_path
    except Exception as e:
        logger.error(f"Ошибка при сохранении HTML компонента: {e}")
        raise

def fix_image_paths(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Исправляем пути для тегов img
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if src.startswith('/problem?id='):
            img['src'] = f"https://ege.sdamgia.ru{src}"
        elif src.startswith('/img/'):
            img['src'] = f"https://ege.sdamgia.ru{src}"
        elif src.startswith('/get_file?'):
            img['src'] = f"https://ege.sdamgia.ru{src}"
            
    # Исправляем пути в стилях с background-image
    for tag in soup.find_all(style=True):
        style = tag['style']
        if 'url(' in style:
            # Заменяем относительные пути в url() на абсолютные
            style = re.sub(r'url\([\'"]?(/[^\'"\)]+)[\'"]?\)', 
                          lambda m: f'url("https://ege.sdamgia.ru{m.group(1)}")', 
                          style)
            tag['style'] = style
            
    return str(soup)

def save_condition_html(html_content, problem_path):
    try:
        html_path = os.path.join(problem_path, "condition.html")
        fixed_html = fix_image_paths(html_content)
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <link rel="stylesheet" href="https://ege.sdamgia.ru/template/style.css">
            <style>
                body {{ margin: 0; padding: 20px; padding-bottom: 150px; }}
                img {{ max-width: 100%; height: auto; }}
            </style>
        </head>
        <body>
            {fixed_html}
        </body>
        </html>
        """
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_template)
        return html_path
    except Exception as e:
        logger.error(f"Ошибка при сохранении HTML условия: {e}")
        raise

def save_solution_html(html_content, problem_path):
    try:
        html_path = os.path.join(problem_path, "solution.html")
        fixed_html = fix_image_paths(html_content)
        # Удаляем display:none из решения
        fixed_html = fixed_html.replace('style="display:none"', '')
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <link rel="stylesheet" href="https://ege.sdamgia.ru/template/style.css">
            <style>
                body {{ margin: 0; padding: 20px; }}
                img {{ max-width: 100%; height: auto; }}
                .solution {{ display: block !important; }}
                .solution * {{ display: block !important; }}
            </style>
        </head>
        <body>
            {fixed_html}
        </body>
        </html>
        """
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_template)
        return html_path
    except Exception as e:
        logger.error(f"Ошибка при сохранении HTML решения: {e}")
        raise

def save_answer_html(text, base_path):
    return save_component_html(f"<div>{text}</div>", base_path, os.path.join("answer", "content.html"))

def parse_problem(driver, block_html, base_path):
    try:
        soup = BeautifulSoup(block_html, 'html.parser')
        header_elem = soup.find(class_='prob_nums')
        header = header_elem.get_text(strip=True) if header_elem else ''
        
        # Извлекаем все типы из заголовка
        types = re.findall(r'Тип\s*(\d+)', header)
        match_id = re.search(r'№\s*(\d+)', header)
        
        if not (types and match_id):
            logger.warning(f"Не удалось извлечь тип или номер задачи из заголовка: {header}")
            return
        
        problem_id = match_id.group(1)
        
        for type_num in types:
            logger.info(f"Обработка задачи: Тип {type_num}, № {problem_id}")
            
            problem_path = os.path.join(base_path, f"Тип_{type_num}", f"N_{problem_id}")
            create_directory(problem_path)
            
            # Обработка условия - теперь берем весь блок задачи
            condition_div = soup.find('div', class_='prob_maindiv')
            if condition_div:
                condition_html = str(condition_div)
                condition_html_path = save_condition_html(condition_html, problem_path)
                driver.get(f"file:///{os.path.abspath(condition_html_path)}")
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                time.sleep(2)
                condition_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'body'))
                )
                condition_path = os.path.join(problem_path, "condition.png")
                take_screenshot(driver, condition_element, condition_path)
            
            # Обработка решения
            solution_div = soup.find('div', class_='solution')
            if solution_div:
                solution_html = str(solution_div)
                solution_html_path = save_solution_html(solution_html, problem_path)
                driver.get(f"file:///{os.path.abspath(solution_html_path)}")
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                time.sleep(2)
                solution_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'body'))
                )
                solution_path = os.path.join(problem_path, "solution.png")
                take_screenshot(driver, solution_element, solution_path)
            
            # Обработка ответа
            answer_div = soup.find('div', class_='answer')
            if answer_div:
                answer_text = answer_div.get_text(strip=True)
                answer_html_path = save_answer_html(answer_text, problem_path)
                driver.get(f"file:///{os.path.abspath(answer_html_path)}")
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                time.sleep(2)
                answer_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'body'))
                )
                answer_path = os.path.join(problem_path, "answer.png")
                take_screenshot(driver, answer_element, answer_path)
                
    except Exception as e:
        logger.error(f"Ошибка при разборе задачи: {e}")
        raise

def main():
    #url = 'https://ege.sdamgia.ru/test?id=80987883&nt=True&pub=False&print=true'
    url = 'https://math-ege.sdamgia.ru/test?id=81010423&nt=True&pub=False&print=true'
    base_path = 'save'
    
    logger.info("Начало работы парсера")
    logger.info(f"URL: {url}")
    
    try:
        create_directory(base_path)
        
        logger.info("Инициализация Chrome драйвера")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=options)
        
        logger.info("Загрузка страницы...")
        driver.get(url)
        
        logger.info("Ожидание загрузки контента...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "prob_maindiv")))
        problem_blocks = driver.find_elements(By.CLASS_NAME, "prob_maindiv")
        
        blocks_html = [block.get_attribute('outerHTML') for block in problem_blocks]
        logger.info(f"Найдено задач: {len(blocks_html)}")
        
        for block_html in blocks_html:
            parse_problem(driver, block_html, base_path)
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        raise
    finally:
        if 'driver' in locals():
            logger.info("Завершение работы драйвера")
            driver.quit()

if __name__ == "__main__":
    main()