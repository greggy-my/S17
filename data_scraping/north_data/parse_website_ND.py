import datetime
import random
import time
import pandas
import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import csv
from data_preprocessing.name_similarity import get_similarity

break_counter = 0

# Getting a list of suppliers names

suppliers_information = pandas.read_excel('../../supplier_names.xlsx', sheet_name='Tabelle1')
suppliers_name_list = [str(name).strip() for name in suppliers_information['Supplier Name'].values.tolist()]

# Getting counter variable to count the progress of scraping

counter_file = open('counter.txt', 'r')
counter = int(counter_file.readline())
counter_file.close()

# Getting proxy

# proxy_list = update_proxy_list()
# proxy_pool = cycle(proxy_list)

while counter < 8001: #len(suppliers_name_list):
    try:
        driver.quit()
    except NameError:
        pass

    if break_counter > 2:
        time.sleep(5400)
        break_counter = 0
    #     proxy = next(proxy_pool)  # Get a proxy from the pool
    #
    #     while not check_proxy(proxy):
    #         proxy = next(proxy_pool)

    # Initialisation of chrome driver

    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--headless")
    # chrome_options.add_argument('--proxy-server=%s' % proxy)
    # add this options=chrome_options to the Chrome() object if you want chrome to keep pages open
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 8)

    driver.get('https://www.northdata.de')
    driver.maximize_window()

    # Accepting all cookies
    try:
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, '/html/body/div[2]/div[1]/div[2]/span[2]/a'))).click()  # accept all cookies
    except:
        pass

    # Main loop for scraping https://www.northdata.de/

    for x in range(0, 30):
        time.sleep(random.randint(0, 10))

        supplier_name = suppliers_name_list[counter]

        # Inserting name
        try:
            search = driver.find_element(By.CLASS_NAME, 'prompt')
            search.send_keys(supplier_name)
            search.send_keys(Keys.ENTER)
        except (selenium.common.exceptions.TimeoutException, selenium.common.exceptions.NoSuchElementException):
            try:
                block_text = driver.find_element(By.XPATH, '/html/body/main/div[1]/div/div[1]/div/p[1]/i').text.lower()
                if block_text == 'fraud prevention system':
                    driver.quit()
                    break_counter += 1
                    with open('blocks.csv', 'a') as block_info_file:
                        writer = csv.writer(block_info_file)
                        writer.writerow(['blocked', datetime.datetime.now(), counter, supplier_name])
                    break
            except selenium.common.exceptions.NoSuchElementException:
                break

        # Comparing company names within the list on the website
        possible_choices = driver.find_elements(By.CSS_SELECTOR, '.event .content .summary .title')
        span_tags = driver.find_elements(By.CSS_SELECTOR, '.event .content .summary .title span')
        sup_tags = driver.find_elements(By.CSS_SELECTOR, '.event .content .summary .title sup')

        possible_choices_text = [company_name.text for company_name in possible_choices]
        span_tags = set([span_tag.text for span_tag in span_tags if span_tag.text != ''])
        sup_tags = set([sup_tag.text for sup_tag in sup_tags if sup_tag.text != ''])

        for index, company_name in enumerate(possible_choices_text):
            if len(sup_tags) != 0:
                for sup_tag in sup_tags:
                    if sup_tag in company_name:
                        company_name = company_name.replace(f"{sup_tag}", "").strip()
            if len(span_tags) != 0:
                for span_tag in span_tags:
                    if span_tag in company_name:
                        company_name = company_name.replace(f"{span_tag}", "").strip()
            possible_choices_text[index] = company_name

        possible_choices_probabilities = [get_similarity(company_name.lower(), supplier_name.lower()) * 100 for
                                          company_name in possible_choices_text]

        if len(possible_choices_probabilities) != 0:
            optimal_index = possible_choices_probabilities.index(max(possible_choices_probabilities))
            optimal_company_name = possible_choices_text[optimal_index]
            print(round(possible_choices_probabilities[optimal_index], 1))
            print(optimal_company_name)
        else:
            optimal_company_name = supplier_name

        time.sleep(random.randint(0, 4))

        # Clicking on the optimal company link
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, f'//a[contains(text(),"{optimal_company_name}")]'))).click()  # click on company link
        except selenium.common.exceptions.ElementClickInterceptedException:
            # In case of the intersection
            link_to_company = driver.find_element(By.XPATH, f'//a[contains(text(),"{optimal_company_name}")]')
            actions = ActionChains(driver)
            actions.move_to_element(link_to_company).perform()
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, f'//a[contains(text(),"{optimal_company_name}")]'))).click()  # click on company link
        except selenium.common.exceptions.TimeoutException:
            # In case the website blocks the request
            try:
                block_text = driver.find_element(By.XPATH,
                                                 '/html/body/main/div[1]/div/div[1]/div/p[1]/i').text.lower()
                if block_text == 'fraud prevention system':
                    driver.quit()
                    break_counter += 1
                    with open('blocks.csv', 'a') as block_info_file:
                        writer = csv.writer(block_info_file)
                        writer.writerow(['blocked', datetime.datetime.now(), counter, supplier_name])
                    break
            except selenium.common.exceptions.NoSuchElementException:
                # In case there is no information about a company
                company_name = supplier_name
                company_register = ""
                company_address = ""
                dict_for_csv = {
                    'provided_name': supplier_name,
                    'name': company_name,
                    'register': company_register,
                    'address': company_address,
                    'probability_of_similarity': 0
                }

                with open('suppliers_name_register_address.csv', 'a') as correct_info_file:
                    writer = csv.writer(correct_info_file)
                    writer.writerow(dict_for_csv.values())

                counter += 1

                with open('counter.txt', 'w+') as counter_file:
                    counter_file.write(str(counter))

                print(dict_for_csv)

                driver.find_element(By.XPATH, '//*[@id="search"]/div[1]/form/div[1]/div[1]/div/i').click()
                continue

        company_name = ""
        company_register = ""
        company_address = ""

        # Getting a company name
        try:
            company_name = driver.find_element(By.XPATH,
                                               '/html/body/main/div[1]/section/div[2]/div/div[1]/div[1]/div/div').text
        except selenium.common.exceptions.NoSuchElementException:
            try:
                company_name = driver.find_element(By.XPATH,
                                                   '/html/body/main/div[1]/section/div[2]/div/div/h3['
                                                   '1]/following-sibling::div').text
            except selenium.common.exceptions.NoSuchElementException:
                try:
                    company_name = driver.find_element(By.XPATH,
                                                       "//h3[contains(text(),'Name')]/following-sibling::div").text
                except selenium.common.exceptions.NoSuchElementException:
                    company_name = optimal_company_name

        # Getting a company register

        try:
            company_register = driver.find_element(By.XPATH,
                                                   '/html/body/main/div[1]/section/div[2]/div/div[1]/div[2]/div').text.replace(
                '\n', ':')
        except selenium.common.exceptions.NoSuchElementException:
            try:
                company_register = driver.find_element(By.XPATH, "/html/body/main/div[1]/section/div[2]/div/div/h3["
                                                                 "2]/following-sibling::div").text.replace('\n', ':')
            except selenium.common.exceptions.NoSuchElementException:
                try:
                    company_register = driver.find_element(By.XPATH,
                                                           "//h3[contains(text(),'Register')]/following-sibling::div").text.replace(
                        '\n', ':')
                except selenium.common.exceptions.NoSuchElementException:
                    pass

        # Getting a company address

        try:
            company_address = driver.find_element(By.XPATH,
                                                  '/html/body/main/div[1]/section/div[2]/div/div[1]/div[3]/div/div/a').text
        except selenium.common.exceptions.NoSuchElementException:
            try:
                company_address = driver.find_element(By.XPATH, '//a[@title="Suche an dieser Adresse"]').text
            except selenium.common.exceptions.NoSuchElementException:
                try:
                    company_address = driver.find_element(By.XPATH,
                                                          '/html/body/main/div[1]/section/div[2]/div/div/h3['
                                                          '3]/following-sibling::div').text
                except selenium.common.exceptions.NoSuchElementException:
                    try:
                        company_address = driver.find_element(By.XPATH,
                                                              "//h3[contains(text(),'Adresse')]/following-sibling::div").text
                    except selenium.common.exceptions.NoSuchElementException:
                        pass

        time.sleep(random.randint(0, 3))

        # Clearing the search bar
        try:
            driver.find_element(By.XPATH, '//*[@id="search"]/div[1]/form/div[1]/div[1]/div/i').click()
        except selenium.common.exceptions.NoSuchElementException:
            try:
                block_text = driver.find_element(By.XPATH,
                                                 '/html/body/main/div[1]/div/div[1]/div/p[1]/i').text.lower()
                if block_text == 'fraud prevention system':
                    driver.quit()
                    break_counter += 1
                    with open('blocks.csv', 'a') as block_info_file:
                        writer = csv.writer(block_info_file)
                        writer.writerow(['blocked', datetime.datetime.now(), counter, supplier_name])
                    break
            except selenium.common.exceptions.NoSuchElementException:
                break
        finally:
            # Appending information to csv
            dict_for_csv = {
                'provided_name': supplier_name,
                'name': company_name,
                'register': company_register,
                'address': company_address,
                'probability_of_similarity': round(possible_choices_probabilities[optimal_index], 1)
            }

            print(dict_for_csv)

            # Storing data and counter

            with open('suppliers_name_register_address.csv', 'a') as correct_info_file:
                writer = csv.writer(correct_info_file)
                writer.writerow(dict_for_csv.values())

            counter += 1

            with open('counter.txt', 'w+') as counter_file:
                counter_file.write(str(counter))
                counter_file.close()
