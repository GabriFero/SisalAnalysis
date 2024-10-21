import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
from random import uniform
import json
import os
import re

# Definisci la pagina principale
MAIN_PAGE = 'https://www.sisal.it/'
# Percorso del file JSON per le credenziali
CREDENTIALS_PATH = 'credenziali.json'


def load_credentials():

    if not os.path.exists(CREDENTIALS_PATH):
        print(f"Il file '{CREDENTIALS_PATH}' non esiste. Creane uno con 'USERNAME' e 'PASSWORD'.")
        return None, None
    
    with open(CREDENTIALS_PATH, 'r') as json_file:
        data = json.load(json_file)
    
    username = data.get('USERNAME')
    password = data.get('PASSWORD')
    
    if not username or not password:
        print("Il file JSON deve contenere 'USERNAME' e 'PASSWORD'.")
        return None, None
    
    return username, password


def init_driver_and_go_main_page():

    # Installa automaticamente la versione corretta di ChromeDriver
    from webdriver_manager.chrome import ChromeDriverManager
    latestchromedriver = ChromeDriverManager().install()

    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-gpu")

    
    driver = uc.Chrome(driver_executable_path=latestchromedriver, 
        options=options,
    )

    driver.maximize_window()
    driver.get(MAIN_PAGE)
    time.sleep(5)
    return driver


def login(max_attempts=3):
    """
    Esegue il login utilizzando le credenziali fornite e salva il token JWT.
    """
    attempt = 0
    driver = None

    while attempt < max_attempts:
        try:
            # Carica le credenziali
            username, password = load_credentials()
            if not username or not password:
                return

            # Inizializza il driver e vai alla pagina principale
            driver = init_driver_and_go_main_page()

            # Trova e clicca sul pulsante "Accedi"
            access_button = driver.find_element(By.LINK_TEXT, value="Accedi")
            time.sleep(1 + uniform(0, 1))
            access_button.click()
            time.sleep(5)

            # Trova i campi di input per username e password
            usr_field = driver.find_element(By.NAME, value="usernameEtc")
            pass_field = driver.find_element(By.NAME, value="password")
            auth_button = driver.find_element(By.ID, value="buttonAuth")

            # Inserisce le credenziali
            time.sleep(0.5)
            usr_field.click()
            usr_field.send_keys(username)
            time.sleep(1.5 + uniform(0, 1))
            pass_field.click()
            pass_field.send_keys(password)
            time.sleep(1.5 + uniform(0, 1))

            # Clicca sul pulsante di autenticazione
            auth_button.click()
            time.sleep(5)

            # Recupera i cookie
            cookies = driver.get_cookies()
            jwt_token = None
            login_data = None

            for cookie in cookies:
                if cookie['name'] == 'JWT':
                    jwt_token = cookie['value']
                elif cookie['name'] == 'login':
                    login_data = cookie['value']

            if jwt_token and login_data:
                # Usa regex per estrarre codiceConto e token dal cookie "login"
                codice_conto_match = re.search(r'codiceConto=([^%]+)', login_data)
                token_match = re.search(r'token=([^%]+)', login_data)

                # Crea il dizionario con tutti i dati richiesti
                data = {
                    'USERNAME': username,
                    'PASSWORD': password,
                    'JWT': jwt_token,
                    'ID': codice_conto_match.group(1) if codice_conto_match else None,
                    'TOKEN': token_match.group(1) if token_match else None
                }

                # Salva il dizionario in un file JSON
                with open(CREDENTIALS_PATH, 'w') as json_file:
                    json.dump(data, json_file, indent=4)
                print(f"LOGIN COMPLETATO PER L'UTENTE: {username}, ORA PUOI PROCEDERE AD ANALIZZARE I DATI")
                driver.quit()
                return jwt_token
            else:
                print("")

        except Exception as e:
            print(f"Errore: {e}")
            print(f"TENTATATIVO N {attempt} FALLITO ")
        finally:
            if driver:
                driver.quit()

        # Incrementa il numero di tentativi
        attempt += 1
        print(f"Tentativo {attempt} di {max_attempts} fallito. Riprovo...")
        time.sleep(3)  # Attendi qualche secondo prima di riprovare

    print("NUMERO MASSIMO DI LOGIN FALLIT (3), RIAVVIARE IL BOT O CONTTATARE L'ASSISTENZA")
    return None






