# Pip install pandas selenium lxml 
# Imports
import sys
import json
import argparse
import numpy as np
import pandas as pd
from time import sleep
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

months = np.array(["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"])

def start_scraping(range_dict, mode):
    # Create secret, config files and install libraries
    # Read user and password from a config file
    config_file = json.load(open('credentials.json'))

    # Call selenium webdriver
    driver = webdriver.Chrome()
    # Fill login page with user and password
    base_url = "https://notapotiguar.set.rn.gov.br/hotsite/#/login"
    driver.get(base_url)
    # Fill user and password
    try:
        elem = (
            WebDriverWait(driver, 30)
            .until(
                EC.presence_of_element_located(
                    (By.ID, "cpf")
                    )
                )
            )
    finally:
        user_form = driver.find_element(By.ID, "cpf")
        pass_form = driver.find_element(By.ID, "password")
        user_form.send_keys(config_file['user'])
        pass_form.send_keys(config_file['password'])
        sleep(2)
        pass_form.send_keys(Keys.RETURN)
        
    sleep(5)
    # Open "Lista de notas"
    notas_url = "https://notapotiguar.set.rn.gov.br/hotsite/#/services/notas"
    driver.get(notas_url)
    driver.maximize_window()
    sleep(1)
    # Parent window
    parent = driver.current_window_handle

    # Result file
    if mode:
        save_first_result = pd.DataFrame(columns=["df_id", "footer", "url"])
        save_first_result.to_csv("Raw_Data/urls.csv", index=False)

    # List values inside dropdown 'ano'
    drop_year = Select(driver.find_element(By.NAME, "ano"))
    for year in list(range_dict.keys()):
        # Select year
        drop_year.select_by_visible_text(str(year))

        # List values inside dropdown 'mes'
        drop_month = Select(driver.find_element(By.NAME, "mes"))
        for month in range_dict[year]:
            drop_month.select_by_visible_text(month)
            sleep(2)
            bought_items = driver.find_elements(By.CLASS_NAME, "nota-botao-detalhar")
            if len(bought_items) > 0:
                for idx, item in enumerate(bought_items):
                    # Open new tab
                    action = ActionChains(driver)
                    # Move to item
                    action.move_to_element(item).click().perform()
                    # Wait for page to load
                    sleep(5)
                    # Get handles
                    child = driver.window_handles
                    child = child[-1]
                    # Switch to new tab
                    driver.switch_to.window(child)
                    # Load url to a dataframe
                    url = driver.current_url
                    # Save found DFs
                    try:
                        df_list = pd.read_html(url, decimal=",", thousands=".", encoding="utf-8")
                        for df_idx, df in enumerate(df_list):
                            df.to_csv(f"Raw_Data/Raw_DFs/{year}_{month}_{idx}_{df_idx}.csv", encoding = "utf-8", header=False)
                        df_id = f"{year}_{month}_{idx}"
                    except:
                        df_id = "Failed"
                    
                    # Recover footer    
                    email_button = driver.find_elements(By.NAME, "btnEmail")
                    fooder_index = -3 if len(email_button) > 0 else -2  
                    try:
                        footer = driver.find_elements(By.CLASS_NAME, "bloco")[fooder_index].text.split("\n")
                        footer = '||'.join(footer)
                    except:
                        footer = "Failed"
                        
                    # Append result to a file                
                    with open("Raw_Data/urls.csv", "a", encoding="utf-8") as f:
                        line = f"{df_id},{footer},{url}\r"
                        f.write(line)
                        f.close()
                    
                    if child != parent:
                        driver.close()
                    
                    driver.switch_to.window(parent)
                    
                    
    driver.close()

def date_range_dict(input_year, input_month, input_order):
    
    # Validate month argument
    if input_month not in months:
        print('Invalid month argument. Please use three-letter abbreviation (ex. JAN, FEV, MAR)')
        sys.exit(1)
        
    # Todays year, and month
    today = datetime.now()
    present_year, present_month = today.year, today.month

    base_year = 2017

    month_index = np.where(months == input_month)[0][0]
    if input_order == "ASC":
        year_list = range(input_year, present_year+1)
        target_year = present_year
        
        to_drop_list = np.append(
            np.array([ii for ii in months[:month_index]]),
            np.array([ii for ii in months[present_month:]])
        )
    else:
        year_list = range(base_year, input_year+1)
        target_year = input_year
        to_drop_list = np.array([ii for ii in months[month_index+1:]])

    mask = np.isin(months, to_drop_list)
    result = {key: months if key != target_year else months[~mask] \
                for key in year_list}
    
    return result

if __name__ == '__main__':
    # Default values for month and year
    now = datetime.now()
    default_year = now.year
    default_month = months[now.month-1]
    
    parser = argparse.ArgumentParser(description='Faz o scrap do Nota Potiguar')
    # Add the year, month and order argument
    parser.add_argument('year', type=int, nargs='?', default=default_year, help='Digite o ano (ex. 2019)')
    parser.add_argument('month', type=str, nargs='?', default=default_month, help='Digite o mês (ex. JAN, FEV, MAR, ABR, MAI, JUN, JUL, AGO, SET, OUT, NOV, DEZ)')
    parser.add_argument('order', type=str, choices=['ASC', 'DESC'], nargs='?', default='DESC', help='Digite a ordem, pode ser ASC ou DESC')
    parser.add_argument('update', type=int, choices=[1, 0], nargs='?', default=0, help='Digite 0 para atualizar a lista de scrap ou 1 para começar do zero')
    # Parse the arguments
    args = parser.parse_args()
    # Parse input arguments
    year = args.year
    month = args.month.upper()
    order = args.order.upper()
    mode = args.update
    
    # A dict with the range of months to be scraped
    range_dict = date_range_dict(year, month, order)
        
    start_scraping(range_dict, mode)