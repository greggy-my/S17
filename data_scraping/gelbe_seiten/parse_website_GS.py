import datetime
import time
import pandas
import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import csv
from data_preprocessing.name_similarity import get_similarity
import sys

dict_for_csv = dict(initial_name="",
                    provided_legal_name="",
                    provided_register="",
                    provided_address="",
                    probability_initial_legal_names="",
                    gelbe_name="",
                    gelbe_address="",
                    gelbe_industry="",
                    name_similarity_prob="",
                    address_similarity_prob="",
                    combined_probability_of_similarity_legal_gelbe="")

error_counter = 0
len_break_counter = 0
unequal_probabilities = False

# Getting lists of suppliers information

suppliers_information = pandas.read_csv(
    '../north_data/suppliers_name_register_address.csv',
    names=['initial_name',
           'provided_legal_name',
           'provided_register',
           'provided_address',
           'probability_initial_legal_names'
           ])

initial_name_list = suppliers_information['initial_name'].values.tolist()
provided_legal_name_list = suppliers_information['provided_legal_name'].values.tolist()
provided_register_list = [str(register).replace('nan', "") for register in
                          suppliers_information['provided_register'].values.tolist()]
provided_address_list = [str(address).replace('nan', "") for address in
                         suppliers_information['provided_address'].values.tolist()]
probability_initial_legal_names_list = suppliers_information['probability_initial_legal_names'].values.tolist()

# Getting counter variable to count the progress of scraping

counter_file = open('counter_g.txt', 'r')
counter = int(counter_file.readline())
counter_file.close()

while counter < len(initial_name_list):
    if error_counter != 0:
        break

    if len_break_counter > 4:
        unequal_probabilities = True
        len_break_counter = 0

    try:
        driver.quit()
    except NameError:
        pass

    # Initialisation of chrome driver

    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--headless")
    # chrome_options.add_argument('--proxy-server=%s' % proxy)
    # add this options=chrome_options to the Chrome() object if you want chrome to keep pages open
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 8)

    driver.get('https://www.gelbeseiten.de/')
    driver.maximize_window()

    # Accepting cookies
    try:
        wait.until(EC.element_to_be_clickable(
            (By.ID, 'cmpbntyestxt'))).click()  # accept all cookies
    except:
        pass

    # Main loop for scraping https://www.gelbeseiten.de/

    for x in range(0, 100):

        provided_legal_name = provided_legal_name_list[counter]
        provided_legal_address = provided_address_list[counter]

        print(f'\nProvided legal name: {provided_legal_name}')

        # Inserting address

        if provided_legal_address != '':
            try:
                search_address = driver.find_element(By.ID, 'where_search')
                search_address.send_keys(provided_legal_address)
            except selenium.common.exceptions.NoSuchElementException as noelement:
                with open('errors.csv', 'a') as errors_file:
                    writer = csv.writer(errors_file)
                    writer.writerow([datetime.datetime.now(), counter, provided_legal_name, noelement.msg])
                    error_counter += 1
                    break

        # Inserting name and submitting
        try:
            search_name = driver.find_element(By.ID, 'what_search')
            search_name.send_keys(provided_legal_name)
            search_name.send_keys(Keys.ENTER)
        except selenium.common.exceptions.NoSuchElementException as noelement:
            with open('errors.csv', 'a') as errors_file:
                writer = csv.writer(errors_file)
                writer.writerow([datetime.datetime.now(), counter, provided_legal_name, noelement.msg])
                error_counter += 1
                break

        # Checking whether there are more results than 0

        try:
            number_results = int(driver.find_element(By.ID, 'mod-TrefferlisteInfo').text)
            if number_results > 0:
                search_result = True
            else:
                search_result = False
        except selenium.common.exceptions.NoSuchElementException as noelement:
            with open('errors.csv', 'a') as errors_file:
                writer = csv.writer(errors_file)
                writer.writerow([datetime.datetime.now(), counter, provided_legal_name, noelement.msg])
                error_counter += 1
                break

        if not search_result and provided_legal_address != "":
            try:
                search_address = driver.find_element(By.ID, 'where_search')
                search_address.clear()
                search_address.send_keys(Keys.ENTER)
                try:
                    number_results = int(driver.find_element(By.ID, 'mod-TrefferlisteInfo').text)
                    if number_results > 0:
                        search_result = True
                    else:
                        search_result = False
                except selenium.common.exceptions.NoSuchElementException as noelement:
                    with open('errors.csv', 'a') as errors_file:
                        writer = csv.writer(errors_file)
                        writer.writerow([datetime.datetime.now(), counter, provided_legal_name, noelement.msg])
                        error_counter += 1
                        break
            except selenium.common.exceptions.NoSuchElementException as noelement:
                with open('errors.csv', 'a') as errors_file:
                    writer = csv.writer(errors_file)
                    writer.writerow([datetime.datetime.now(), counter, provided_legal_name, noelement.msg])
                    error_counter += 1
                    break

        # Getting and writing new data
        print(f'Search status: {search_result}')

        if search_result:
            try:
                wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@data-wipe-name="Titel"]')))
                gelbe_names_list = [name.text for name in driver.find_elements(By.XPATH, '//*[@data-wipe-name="Titel"]')]
            except selenium.common.exceptions.StaleElementReferenceException:
                driver.implicitly_wait(5)
                wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@data-wipe-name="Titel"]')))
                gelbe_names_list = [name.text for name in
                                    driver.find_elements(By.XPATH, '//*[@data-wipe-name="Titel"]')]

            try:
                wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@data-wipe-name="Titel"]/following'
                                                                          '-sibling::p')))
                gelbe_industry_list = [industry.text for industry in driver.find_elements(By.XPATH,
                                                                                          '//*[@data-wipe-name="Titel'
                                                                                          '"]/following-sibling::p')]
            except selenium.common.exceptions.StaleElementReferenceException:
                driver.implicitly_wait(5)
                wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@data-wipe-name="Titel"]/following'
                                                                          '-sibling::p')))
                gelbe_industry_list = [industry.text for industry in driver.find_elements(By.XPATH,
                                                                                          '//*[@data-wipe-name="Titel'
                                                                                          '"]/following-sibling::p')]
            try:
                wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'mod-AdresseKompakt')))
                gelbe_address_blocks_text = [name.text.split('\n') for name in
                                     driver.find_elements(By.CLASS_NAME, 'mod-AdresseKompakt')]
            except selenium.common.exceptions.StaleElementReferenceException:
                driver.implicitly_wait(5)
                wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'mod-AdresseKompakt')))
                gelbe_address_blocks_text = [name.text.split('\n') for name in
                                             driver.find_elements(By.CLASS_NAME, 'mod-AdresseKompakt')]

            gelbe_address_list = [address[0] if not address[0].replace(" ", "").isdigit() else "" for address in
                                  gelbe_address_blocks_text]

            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article.mod.mod-Treffer')))
                gelbe_blocks_text = [
                    name.text.replace("PLATIN PARTNER\n", "").replace("SILVER PARTNER\n", "").replace("GOLD PARTNER\n", "")
                    for name in driver.find_elements(By.CSS_SELECTOR, 'article.mod.mod-Treffer')]
            except selenium.common.exceptions.StaleElementReferenceException:
                driver.implicitly_wait(5)
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article.mod.mod-Treffer')))
                gelbe_blocks_text = [
                    name.text.replace("PLATIN PARTNER\n", "").replace("SILVER PARTNER\n", "").replace("GOLD PARTNER\n", "") for name in driver.find_elements(By.CSS_SELECTOR, 'article.mod.mod-Treffer')]

            gelbe_company_blocks = [company.split('\n')[:5] for company in gelbe_blocks_text]

            address_span_list = [span_tag.text for span_tag in
                                 driver.find_elements(By.CLASS_NAME, 'mod-AdresseKompakt__entfernung')]

            print(f'Gelbe names list: {gelbe_names_list}"')
            print(f'Gelbe industry list: {gelbe_industry_list}')
            print(f'Gelbe address list: {gelbe_address_list}')

            # Getting rid of geo in span tags

            for index, company_address in enumerate(gelbe_address_list):
                if len(address_span_list) != 0:
                    for span_tag in address_span_list:
                        if span_tag in company_address:
                            company_address = company_address.replace(f"{span_tag}", "").strip()
                gelbe_address_list[index] = company_address

            # Calculating probabilities of similarity and choosing optimal choice
            if len(gelbe_names_list) == len(gelbe_address_list) == len(gelbe_industry_list):
                probability_legal_gelbe_names_list = [get_similarity(gelbe_name, provided_legal_name) * 100
                                                      for gelbe_name in gelbe_names_list]
                probability_legal_gelbe_address_list = [get_similarity(gelbe_address, provided_legal_address) * 100
                                                        for gelbe_address in gelbe_address_list]

                combined_probability_of_similarity_legal_gelbe = [
                    prob_name * probability_legal_gelbe_address_list[index] / 100
                    for index, prob_name
                    in enumerate(probability_legal_gelbe_names_list)]

                print(f'Legal-Gelbe names similarity probabilities: {probability_legal_gelbe_names_list}')
                print(f'Legal-Gelbe addresses similarity probabilities: {probability_legal_gelbe_address_list}')
                print(f'Legal-Gelbe combined similarity probabilities: {combined_probability_of_similarity_legal_gelbe}')

                optimal_index = combined_probability_of_similarity_legal_gelbe.index(
                    max(combined_probability_of_similarity_legal_gelbe))

                if probability_legal_gelbe_address_list.count(0.0) == len(probability_legal_gelbe_address_list):
                    optimal_index = probability_legal_gelbe_names_list.index(max(probability_legal_gelbe_names_list))
                    print(f'Optimal index was chosen based on name prob: {optimal_index}')

                combined_probability_of_similarity_legal_gelbe_optimal = combined_probability_of_similarity_legal_gelbe[optimal_index]

                gelbe_name = gelbe_names_list[optimal_index]

                gelbe_address = gelbe_address_list[optimal_index]

                gelbe_industry = gelbe_industry_list[optimal_index]

                print(f'Combined prob: {combined_probability_of_similarity_legal_gelbe_optimal}')
                print(f'Optimal Gelbe name: {gelbe_name}')
                print(f'Optimal Gelbe address: {gelbe_address}')
                print(f'Optimal Gelbe industry: {gelbe_industry}')

                # Storing new data

                dict_for_csv['initial_name'] = initial_name_list[counter]
                dict_for_csv['provided_legal_name'] = provided_legal_name
                dict_for_csv['provided_register'] = provided_register_list[counter]
                dict_for_csv['provided_address'] = provided_legal_address
                dict_for_csv['probability_initial_legal_names'] = probability_initial_legal_names_list[counter]
                dict_for_csv['gelbe_name'] = gelbe_name
                dict_for_csv['gelbe_address'] = gelbe_address
                dict_for_csv['gelbe_industry'] = gelbe_industry
                dict_for_csv['name_similarity_prob'] = round(probability_legal_gelbe_names_list[optimal_index], 2)
                dict_for_csv['address_similarity_prob'] = round(probability_legal_gelbe_address_list[optimal_index], 2)
                dict_for_csv[
                    'combined_probability_of_similarity_legal_gelbe'] = round(combined_probability_of_similarity_legal_gelbe_optimal, 2)
                len_break_counter = 0
            else:
                if not unequal_probabilities:
                    len_break_counter += 1
                    break
                else:
                    sys.exit(f'Len of names and addresses arent the same. Counter: {counter}, Name: {provided_legal_name} - refreshing the page')

        else:
            dict_for_csv['initial_name'] = initial_name_list[counter]
            dict_for_csv['provided_legal_name'] = provided_legal_name
            dict_for_csv['provided_register'] = provided_register_list[counter]
            dict_for_csv['provided_address'] = provided_legal_address
            dict_for_csv['probability_initial_legal_names'] = probability_initial_legal_names_list[counter]
            dict_for_csv['gelbe_name'] = ""
            dict_for_csv['gelbe_address'] = ""
            dict_for_csv['gelbe_industry'] = ""
            dict_for_csv['name_similarity_prob'] = ""
            dict_for_csv['address_similarity_prob'] = ""
            dict_for_csv[
                'combined_probability_of_similarity_legal_gelbe'] = ""

        with open('suppliers_name_register_address_industry.csv', 'a') as correct_info_file:
            writer = csv.writer(correct_info_file)
            writer.writerow(dict_for_csv.values())

        counter += 1

        with open('counter_g.txt', 'w+') as counter_file:
            counter_file.write(str(counter))
            counter_file.close()

        # Erasing info from the search

        if provided_legal_address != '':
            try:
                search_address = driver.find_element(By.ID, 'where_search')
                search_address.clear()
            except selenium.common.exceptions.NoSuchElementException as noelement:
                with open('errors.csv', 'a') as errors_file:
                    writer = csv.writer(errors_file)
                    writer.writerow([datetime.datetime.now(), counter, provided_legal_name, noelement.msg])
                    error_counter += 1
                    break

        try:
            search_name = driver.find_element(By.ID, 'what_search')
            search_name.clear()
        except selenium.common.exceptions.NoSuchElementException as noelement:
            with open('errors.csv', 'a') as errors_file:
                writer = csv.writer(errors_file)
                writer.writerow([datetime.datetime.now(), counter, provided_legal_name, noelement.msg])
                error_counter += 1
                break
