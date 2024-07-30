import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from bs4 import BeautifulSoup
import time

# Step 1: Selenium을 사용하여 웹 페이지 로드
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # 브라우저 창을 열지 않음
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

url = "https://www.kbchachacha.com/public/search/main.kbc"
driver.get(url)

wait = WebDriverWait(driver, 10)
container = wait.until(EC.presence_of_element_located((By.ID, 'mCSB_1_container')))

soup = BeautifulSoup(driver.page_source, 'html.parser')

manufacturers = []
manufacturer_data = {}

for item in soup.find_all('div', class_='checkList__manufacturer'):
    a_tag = item.find('a', class_='checkListLink')
    manufacturer = a_tag.find('span').text.strip()
    href = a_tag['href']
    
    maker_code = re.search(r"setMakerCode\('(\d+)'\)", href).group(1)
    
    manufacturers.append((manufacturer, maker_code))

print("Manufacturers and Codes:", manufacturers)

for manufacturer, maker_code in manufacturers:
    driver.get(f"https://www.kbchachacha.com/public/search/main.kbc#!?page=1&sort=-orderDate&makerCode={maker_code}")
    #오버로드 방지
    time.sleep(2)  
    
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'checkList__model__title')))
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    models = []
    
    name_order_section = None
    for div in soup.find_all('div', class_='checkList__model'):
        if div.find('strong') and '이름순' in div.find('strong').text:
            name_order_section = div
            break
    
    if name_order_section:
        for model_item in name_order_section.find_all('div', class_='checkList__model__title'):
            model_a_tag = model_item.find('a', class_='checkListLink')
            model_name = model_a_tag.find('span').text.strip()
            model_href = model_a_tag['href']

            model_code = re.search(r"setClassCode\('(\d+)'\)", model_href).group(1)

            model_number = model_item.find('span', class_='number').text.strip()
            
            models.append((model_name, model_code, model_number))

            driver.get(f"https://www.kbchachacha.com/public/search/main.kbc#!?page=1&sort=-orderDate&makerCode={maker_code}&classCode={model_code}")
            time.sleep(2)

            sub_soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            sub_models = []
            sub_model_section = sub_soup.find('div', class_='checkList__year')
            if sub_model_section:
                for sub_model_item in sub_model_section.find_all('div', class_='listItem'):
                    sub_model_name = sub_model_item.find('label').find('span').text.strip()
                    sub_model_number = sub_model_item.find('span', class_='number').text.strip()
                    sub_models.append((sub_model_name, sub_model_number))

            models[-1] += (sub_models,)
    
    manufacturer_data[manufacturer] = models

with open('manufacturers_models.csv', 'w', encoding='utf-8', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Manufacturer', 'Model Name', 'Model Code', 'Model Number', 'Sub-model Name', 'Sub-model Number'])
    
    for manufacturer, models in manufacturer_data.items():
        for model_data in models:
            model_name, model_code, model_number, sub_models = model_data
            if sub_models:
                for sub_model_name, sub_model_number in sub_models:
                    writer.writerow([manufacturer, model_name, model_code, model_number, sub_model_name, sub_model_number])
            else:
                writer.writerow([manufacturer, model_name, model_code, model_number, '', ''])

driver.quit()
