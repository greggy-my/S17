from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import requests


def update_proxy_list():
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument("--incognito")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 8)

    driver.get('https://free-proxy-list.net/')
    driver.maximize_window()
    text = driver.find_element(By.XPATH, '/html/body/section[1]/div/div[2]/div/table/tbody').text.split('\n')
    elite_proxy = [proxy_info.split(' ')[0]
                   for proxy_info in text
                   if ('elite' in proxy_info.split(' ')) and ('no' not in proxy_info.split(' '))]
    return elite_proxy


def check_proxy(proxy):
    proxies = {
        "http": proxy
    }
    request = str(requests.get('https://www.google.com', proxies=proxies).status_code)
    if request == '200':
        return True
    else:
        return False