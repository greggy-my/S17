import pandas
import datetime
from data_preprocessing.name_similarity import  get_similarity
import unicodedata
import Levenshtein
from collections import Counter


def merge_similarity(data_list: list):
    global threshold
    list_new = data_list
    for ind, element in enumerate(data_list):
        cos_sim = [round(get_similarity(str(element), str(element_new)), 3) if element != element_new else 0 for
                   element_new in list_new]
        lev_sim = [round(Levenshtein.ratio(element, element_new), 3) if element != element_new else 0 for element_new in
                   list_new]
        total_similarity = [sim + lev_sim[ind] for ind, sim in enumerate(cos_sim)]
        if max(total_similarity) > threshold:
            optimal_ind = total_similarity.index(max(total_similarity))
            list_new[optimal_ind] = element
    return list_new


def compare_database(legal_information, data_list):
    global threshold_d
    for ind, element in enumerate(data_list):
        cos_sim = [round(get_similarity(str(element), str(element_new)), 3) for
                   element_new in legal_information]
        lev_sim = [round(Levenshtein.ratio(element, element_new), 3) for element_new in
                   legal_information]
        total_similarity = [sim + lev_sim[ind] for ind, sim in enumerate(cos_sim)]
        if max(total_similarity) > threshold_d:
            optimal_ind = total_similarity.index(max(total_similarity))
            data_list[ind] = legal_information[optimal_ind]
    return data_list


def decode_text(data_list: list):
    data_list = [unicodedata.normalize('NFKD', str(element).strip().encode('ASCII', 'ignore').decode()) for element in
                 data_list]
    return data_list


def is_change(old_list: list, new_list: list):
    for index, element in enumerate(old_list):
        if str(element).lower() != str(new_list[index]).lower():
            return True
    return False


def two_most_frequent(data_list: list):
    occurence_count = Counter(data_list)
    return occurence_count.most_common(2)


if __name__ == "__main__":

    start_time = datetime.datetime.now()
    print(f'Start: {start_time}')

    threshold = 1.50
    threshold_d = 1.70

    # Database of legal information
    database = pandas.read_csv(
        '../data_scraping/gelbe_seiten/suppliers_name_register_address_industry.csv')
    legal_names = database['provided_legal_name'].tolist()

    # General data Sender company name
    general_data = pandas.read_excel('../data.xlsx',
                                     sheet_name='General data')
    sender_company_name = general_data['Sender company name'].tolist()
    sender_company_name = decode_text(data_list=sender_company_name)
    sender_company_name = merge_similarity(data_list=sender_company_name)
    sender_company_name_new = compare_database(data_list=sender_company_name, legal_information=legal_names)
    print(
        f'Made any changes using database: {is_change(old_list=sender_company_name, new_list=sender_company_name_new)}')
    general_data['Sender company name'] = sender_company_name_new
    print(f'Sender company name: Done\nAt: {datetime.datetime.now()}')

    # General data Sender street
    sender_street = general_data['Sender street'].tolist()
    sender_street = decode_text(data_list=sender_street)
    sender_street_new = merge_similarity(data_list=sender_street)
    general_data['Sender street'] = sender_street_new
    print(f'Sender street: Done \nAt: {datetime.datetime.now()}')

    # General data Receiver company name
    receiver_company_name = general_data['Receiver company name'].tolist()
    receiver_company_name = decode_text(data_list=receiver_company_name)
    receiver_company_name = merge_similarity(data_list=receiver_company_name)
    receiver_company_name_new = compare_database(data_list=receiver_company_name, legal_information=legal_names)
    print(
        f'Made any changes using database: {is_change(old_list=receiver_company_name, new_list=receiver_company_name_new)}')
    general_data['Receiver company name'] = receiver_company_name_new
    print(f'Receiver company name: Done\nAt: {datetime.datetime.now()}')

    # General data Receiver street
    receiver_street = general_data['Receiver street'].tolist()
    receiver_street = decode_text(data_list=receiver_street)
    receiver_street_new = merge_similarity(data_list=receiver_street)
    general_data['Receiver street'] = receiver_street_new
    print(f'Receiver street: Done\nAt: {datetime.datetime.now()}')

    # General Data VAT check
    vat_dict = {}
    vat = general_data['VAT ID'].tolist()
    vat = [str(vat).strip().replace(" ", "") for vat in vat]
    vat_new = vat

    # Creating dict of all VAT for a company
    for index, name in enumerate(sender_company_name_new):
        vat_number = vat[index]
        if name not in vat_dict:
            vat_dict[name] = []
        vat_dict[name].append(vat_number)

    # Choosing the most frequent one
    for name in vat_dict:
        if two_most_frequent(vat_dict[name])[0][0] == 'nan' and len(two_most_frequent(vat_dict[name])) > 1:
            vat_dict[name] = two_most_frequent(vat_dict[name])[1][0]
        else:
            vat_dict[name] = two_most_frequent(vat_dict[name])[0][0]

    # Changing VAT in the dataframe
    for index, name in enumerate(sender_company_name_new):
        vat_new[index] = vat_dict[name]

    general_data['VAT ID'] = vat_new
    print(f'Vat: Done\nAt: {datetime.datetime.now()}')

    # Position data Title
    position_data = pandas.read_excel('../data.xlsx',
                                      sheet_name='Position data')
    title = position_data['Title'].tolist()
    title = decode_text(data_list=title)
    title_new = merge_similarity(data_list=title)
    print(f'Title: Done\nAt: {datetime.datetime.now()}')
    position_data['Title'] = title_new

    # Writing to excel

    with pandas.ExcelWriter('../data_upd.xlsx') as writer:
        general_data.to_excel(excel_writer=writer, sheet_name='General data', index=False)
        # position_data.to_excel(excel_writer=writer, sheet_name='Position data', index=False)

    end_time = datetime.datetime.now()
    print(f'End: {end_time}')
    total_time = end_time - start_time
    print(f'Total Time: {total_time}')
