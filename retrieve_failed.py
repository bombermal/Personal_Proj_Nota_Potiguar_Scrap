from time import sleep
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import json

# Load file that indicates urls to retry
url_path = "Raw_Data/"
url_test = "urls" 
url_df = pd.read_csv(f"{url_path}{url_test}.csv").fillna("Failed")

# Select failed
mask = url_df.footer == "Failed"
url_df = url_df[mask]

# Result file, Create a csv to store the result
save_first_result = pd.DataFrame(columns=["df_id", "footer", "url"])
save_first_result.to_csv("Raw_Data/urls_retry.csv", index=False)

# Read user and password from a config file
config_file = json.load(open('credentials.json'))

# Call selenium webdriver
driver = webdriver.Chrome()

for _, row in url_df.iterrows():
    sleep(5)
    url = row.url
    # Open url
    driver.get(url)
    year_name, month_name, idx = row.df_id.split("_")
    
    # Load table on site
    try:
        df_list = pd.read_html(url, decimal=",", thousands=".", encoding="utf-8")
        for df_idx, df in enumerate(df_list):
            df.to_csv(f"Raw_Data/Raw_DFs/{year_name}_{month_name}_{idx}_{df_idx}.csv", encoding = "utf-8", header=False)
        df_id = f"{year_name}_{month_name}_{idx}"
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
    with open("Raw_Data/urls_retry.csv", "a", encoding="utf-8") as f:
        line = f"{df_id},{footer},{url}\r"
        f.write(line)
        f.close()
        
        
# Combine the new retrieved data with the original file, updating the successful ones
retry_df = pd.read_csv("Raw_Data/urls_retry.csv")
original_df = pd.read_csv("Raw_Data/urls.csv")

for idx, row in retry_df.iterrows():
    if row.df_id != "Failed":
        mask = original_df.df_id == row.df_id
        original_df.loc[mask, "footer"] = row.footer
        
# Save result
original_df.to_csv("Raw_Data/urls.csv", index=False)