import os
import json
import time
import httpx
import pickle
from datetime import datetime
from login import *


url_search = "https://betting.sisal.it/api/ticket-info/secure/searchSportTicketList"
url_details = "https://betting.sisal.it/api/ticket-info/secure/getBetDetails"

def load(credentials_path):
    try:
        with open(credentials_path, 'r') as json_file:
            data = json.load(json_file)
            username = data.get('USERNAME')
            password = data.get('PASSWORD')
            token_jwt = data.get('JWT')
            account_id = data.get('ID')
            token = data.get('TOKEN')
            return username, password, token_jwt, account_id, token
    except FileNotFoundError:
        print("File 'credenziali.json' non trovato.")
        return None, None, None, None, None
    except json.JSONDecodeError:
        print("Errore nel decodificare 'credenziali.json'. Assicurati che il file sia formattato correttamente.")
        return None, None, None, None, None
    

CREDENTIALS_PATH = 'credenziali.json'

def fetch_tickets():
    username, password, token_jwt, account_id, token = load(CREDENTIALS_PATH)

    # Headers per le richieste
    headers = {
        'authority': 'betting.sisal.it',
        'accept': '*/*',
        'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
        'origin': 'https://www.sisal.it',
        'referer': 'https://www.sisal.it/',
        'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not=A?Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'user_data': json.dumps({
            "accountId": account_id,
            "token": token,
            "tokenJWT": token_jwt,
            "locale": "it_IT",
            "loggedIn": True,
            "channel": 62,
            "brandId": 175,
            "offerId": 0
        }),
}
    # Parametri di ricerca per i ticket
    params = {
        'periodo': '99',
        'pageSize': '10',
        'pageNumber': '1',
        'stato': '4',
        'tipo': '2',
        'channel': '62'
    }

    # Recupero dei ticket
    try:
        response = httpx.get(
            url=url_search,
            params=params,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()
        cont = json.loads(response.content)
        n_tickets = cont["result"]["ticketCount"]
        print(f"{n_tickets} scommesse da scaricare.")
    except Exception as e:
        print(f"Errore durante il recupero dei dati iniziali: {e}")
        n_tickets = 0

    # Variabili per gestire i download dei ticket
    how_many_at_time = 50
    contenuti = []
    page_counter = 1

    while n_tickets > 0:
        params["pageSize"] = str(min(n_tickets, how_many_at_time))
        params["pageNumber"] = str(page_counter)
        page_counter += 1
        n_tickets -= min(how_many_at_time, n_tickets)
        print(f"{n_tickets} scommesse rimanenti.")
        try:
            response = httpx.get(
                url=url_search,
                params=params,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            contenuti.append(json.loads(response.content))
        except Exception as e:
            print(f"Errore durante il recupero dei ticket: {e}")

    # Recupero dettagli di ogni ticket chiuso
    bets_and_details = []
    sisal_sesh = httpx.Client(headers=headers)
    counter = 1

    for cont in contenuti:
        try:
            for closed_bet in cont["result"]["ticketsList"]:
                time.sleep(1.5)
                print(f"Recupero dettagli per bet {counter}")
                counter += 1
                parametri = {
                    "channel": "62",
                    "regulatorBetId": str(closed_bet["regulatorBetId"]),
                    "betId": str(closed_bet["betId"])
                }
                response = sisal_sesh.get(
                    url=url_details,
                    params=parametri,
                    timeout=60
                )
                response.raise_for_status()
                content = json.loads(response.content)
                bets_and_details.append((closed_bet, content))
        except Exception as e:
            print(f"Errore durante il recupero del dettaglio di una scommessa: {e}")

    return bets_and_details


def load_all_bets():
    # Caricamento dei dettagli da tutti i file pickle
    try:
        export_path = os.path.join(os.getcwd(), "export")
        files = [f for f in os.listdir(export_path) if f.startswith("bets_") and f.endswith(".pkl")]
        if not files:
            print("Nessun file di scommesse trovato.")
            return []
        all_bets_and_details = []
        for filename in files:
            with open(os.path.join(export_path, filename), "rb") as file:
                bets_and_details = pickle.load(file)
                all_bets_and_details.extend(bets_and_details)
        print(f"Dati caricati da {len(files)} file.")
        return all_bets_and_details
    except Exception as e:
        print(f"Errore durante il caricamento: {e}")
        return []

def load_user_specific_bets(usernames):
    try:
        export_path = os.path.join(os.getcwd(), "export")
        files = [f for f in os.listdir(export_path) if f.startswith("bets_") and f.endswith(".pkl")]
        if not files:
            print("Nessun file di scommesse trovato.")
            return []
        user_bets_and_details = []
        for filename in files:
            # Estrai il nome utente dal nome del file
            username_in_file = filename.split('_')[1]
            if username_in_file in usernames:
                with open(os.path.join(export_path, filename), "rb") as file:
                    bets_and_details = pickle.load(file)
                    user_bets_and_details.extend(bets_and_details)
        print(f"Dati caricati per gli utenti: {', '.join(usernames)}")
        return user_bets_and_details
    except Exception as e:
        print(f"Errore durante il caricamento: {e}")
        return []

def save_bets(bets_and_details, username):
    # Salvataggio dei dettagli in un file pickle
    DATETIME_FORMAT = "%d-%m-%Y"
    try:
        export_path = os.path.join(os.getcwd(), "export")
        if not os.path.exists(export_path):
            os.makedirs(export_path)
        
        # Controlla se esiste un file con lo stesso username e rimuovilo
        for f in os.listdir(export_path):
            if f.startswith(f"bets_{username}_") and f.endswith(".pkl"):
                os.remove(os.path.join(export_path, f))
        
        filename = f"bets_{username}_{datetime.fromtimestamp(time.time()).strftime(DATETIME_FORMAT)}.pkl"
        file_path = os.path.join(export_path, filename)
        
        # Salva i nuovi dettagli
        with open(file_path, "wb") as file:
            pickle.dump(bets_and_details, file)
        print(f"Dettagli delle scommesse salvati in {filename}")
    except Exception as e:
        print(f"Errore durante il salvataggio: {e}")


def load_bets():
    # Caricamento dei dettagli da un file pickle
    username, password, token_jwt, account_id, token = load(CREDENTIALS_PATH)
    try:
        export_path = os.path.join(os.getcwd(), "export")
        files = [f for f in os.listdir(export_path) if f.startswith(f"bets_{username}_") and f.endswith(".pkl")]
        if not files:
            print("Nessun file di scommesse trovato.")
            return []
        latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(export_path, x)))
        with open(os.path.join(export_path, latest_file), "rb") as file:
            bets_and_details = pickle.load(file)
        print(f"Dati caricati da {latest_file}")
        return bets_and_details
    except Exception as e:
        print(f"Errore durante il caricamento: {e}")
        return []

def organize_bets(bets_and_details):
    # Organizzazione delle scommesse per tipo di sport
    sport_bets_dict = {}
    for bet in bets_and_details:
        try:
            sport = bet[1]["result"]["predictions"][0]["sportDescription"]
            sport_bets_dict.setdefault(sport, []).append(bet)
        except Exception:
            pass

    # Organizzazione delle scommesse per competizione (campionato)
    competition_bets_dict = {}
    for bet in bets_and_details:
        try:
            competition = bet[1]["result"]["predictions"][0]["competitionDescription"]
            competition_bets_dict.setdefault(competition, []).append(bet)
        except Exception:
            pass

    # Organizzazione delle scommesse per mercato usando selectionDescription
    market_bets_dict = {}
    for bet in bets_and_details:
        try:
            market = bet[1]["result"]["predictions"][0]["selectionDescription"]
            market_bets_dict.setdefault(market, []).append(bet)
        except Exception:
            pass

    return sport_bets_dict, competition_bets_dict, market_bets_dict

def apply_filters(bets_and_details, sport_filter=None, competition_filter=None, market_filter=None):
    filtered_bets = []

    for bet in bets_and_details:
        try:
            sport = bet[1]["result"]["predictions"][0]["sportDescription"]
            competition = bet[1]["result"]["predictions"][0]["competitionDescription"]
            market = bet[1]["result"]["predictions"][0]["selectionDescription"]

            sport_match = True
            competition_match = True
            market_match = True

            if sport_filter:
                sport_match = (sport_filter.lower() == sport.lower())

            if competition_filter:
                competition_match = (competition_filter.lower() == competition.lower())

            if market_filter:
                market_match = (market_filter.lower() == market.lower())

            if sport_match and competition_match and market_match:
                filtered_bets.append(bet)
        except Exception:
            pass

    return filtered_bets

def get_filtered_competitions(bets_and_details, sport_filter):
    competitions = set()
    for bet in bets_and_details:
        try:
            sport = bet[1]["result"]["predictions"][0]["sportDescription"]
            competition = bet[1]["result"]["predictions"][0]["competitionDescription"]
            if sport_filter and sport_filter.lower() == sport.lower():
                competitions.add(competition)
        except Exception:
            pass
    return list(competitions)

def get_filtered_markets(bets_and_details, sport_filter=None, competition_filter=None):
    markets = set()
    for bet in bets_and_details:
        try:
            sport = bet[1]["result"]["predictions"][0]["sportDescription"]
            competition = bet[1]["result"]["predictions"][0]["competitionDescription"]
            market = bet[1]["result"]["predictions"][0]["selectionDescription"]
            if sport_filter and sport_filter.lower() == sport.lower():
                if competition_filter is None or competition_filter.lower() == competition.lower():
                    markets.add(market)
        except Exception:
            pass
    return list(markets)

def aggregate_info(bets):
    paid = 0
    losing = 0
    total = 0
    total_stake = 0.0
    paid_amount = 0.0

    for element in bets:
        bet_info = element[0]

        if bet_info["betState"] == "LOSING":
            losing += 1
        else:
            paid += 1

        total += 1

        stake = bet_info.get("stakeAmount", 0) or 0
        payout = bet_info.get("paidAmount", 0) or 0

        stake = stake / 100
        payout = payout / 100

        total_stake += stake
        paid_amount += payout

    profit = paid_amount - total_stake
    roi = (profit / total_stake) * 100 if total_stake > 0 else 0

    return dict(
        paid=paid,
        losing=losing,
        total=total,
        total_stake=round(total_stake, 2),
        paid_amount=round(paid_amount, 2),
        profit=round(profit, 2),
        roi=round(roi, 2)
    )

def display_list(options_list, title):
    print(f"\n{title}:")
    for idx, item in enumerate(sorted(options_list), 1):
        print(f"{idx}. {item}")

def get_user_input(prompt, allow_back_exit=True):
    while True:
        user_input = input(prompt)
        if allow_back_exit and user_input.lower() in ['exit', 'back']:
            return user_input.lower()
        return user_input


def top_wins(bets_and_details):
    # Dizionario per tenere traccia delle vittorie per campionato
    championship_wins = {}
    championship_totals = {}
    for bet in bets_and_details:
        try:
            competition = bet[1]["result"]["predictions"][0]["competitionDescription"]
            bet_info = bet[0]
            bet_state = bet_info.get("betState", "UNKNOWN")

            # Controlla lo stato della scommessa
            if bet_state != "PAID":
                pass  # Non incrementare le vittorie
            else:
                # Considera tutte le scommesse non perdenti come vincenti
                championship_wins[competition] = championship_wins.get(competition, 0) + 1
            championship_totals[competition] = championship_totals.get(competition, 0) + 1
        except Exception as e:
            print(f"Errore: {e}")
            pass

    # Calcolo del tasso di vittoria per ogni campionato
    championship_win_rates = {}
    for competition in championship_totals:
        wins = championship_wins.get(competition, 0)
        total = championship_totals[competition]
        win_rate = (wins / total) * 100 if total > 0 else 0
        championship_win_rates[competition] = win_rate

    # Ordinamento dei campionati per tasso di vittoria
    sorted_championships = sorted(championship_win_rates.items(), key=lambda x: x[1], reverse=True)

    top_n = 5
    print("\nTop 5 campionati per tasso di vittoria:")
    for comp, rate in sorted_championships[:top_n]:
        print(f"{comp}: {rate:.2f}% vittorie su {championship_totals[comp]} scommesse")

    print("\nPeggiori 5 campionati per tasso di vittoria:")
    for comp, rate in sorted_championships[-top_n:]:
        print(f"{comp}: {rate:.2f}% vittorie su {championship_totals[comp]} scommesse")



def top_roi(bets_and_details):
    # Dizionario per tenere traccia dei guadagni e delle puntate per campionato
    championship_profits = {}
    championship_stakes = {}
    for bet in bets_and_details:
        try:
            competition = bet[1]["result"]["predictions"][0]["competitionDescription"]
            bet_info = bet[0]
            stake = bet_info.get("stakeAmount", 0) / 100  # Converti in euro
            payout = bet_info.get("paidAmount", 0) / 100  # Converti in euro
            profit = payout - stake
            championship_profits[competition] = championship_profits.get(competition, 0) + profit
            championship_stakes[competition] = championship_stakes.get(competition, 0) + stake
        except Exception:
            pass

    # Calcolo del ROI per ogni campionato
    championship_roi = {}
    for competition in championship_stakes:
        total_stake = championship_stakes[competition]
        total_profit = championship_profits.get(competition, 0)
        roi = (total_profit / total_stake) * 100 if total_stake > 0 else 0
        championship_roi[competition] = roi

    # Ordinamento dei campionati per ROI
    sorted_championships = sorted(championship_roi.items(), key=lambda x: x[1], reverse=True)

    top_n = 5
    print("\nTop 5 campionati per ROI:")
    for comp, roi in sorted_championships[:top_n]:
        print(f"{comp}: ROI {roi:.2f}% su {championship_stakes[comp]:.2f}€ puntati")

    print("\nPeggiori 5 campionati per ROI:")
    for comp, roi in sorted_championships[-top_n:]:
        print(f"{comp}: ROI {roi:.2f}% su {championship_stakes[comp]:.2f}€ puntati")


def load_all_bets():
    # Caricamento dei dettagli da tutti i file pickle
    try:
        export_path = os.path.join(os.getcwd(), "export")
        files = [f for f in os.listdir(export_path) if f.startswith("bets_") and f.endswith(".pkl")]
        if not files:
            print("Nessun file di scommesse trovato.")
            return []
        all_bets_and_details = []
        for filename in files:
            with open(os.path.join(export_path, filename), "rb") as file:
                bets_and_details = pickle.load(file)
                all_bets_and_details.extend(bets_and_details)
        print(f"Dati caricati da {len(files)} file.")
        return all_bets_and_details
    except Exception as e:
        print(f"Errore durante il caricamento: {e}")
        return []
    

def calculate_championship_stats(bets_and_details):
    championship_stats = {}

    for bet in bets_and_details:
        try:
            competition = bet[1]["result"]["predictions"][0]["competitionDescription"]
            bet_info = bet[0]

            # Inizializza il dizionario per il campionato se non esiste
            if competition not in championship_stats:
                championship_stats[competition] = {
                    'wins': 0,
                    'losses': 0,
                    'total_bets': 0,
                    'total_stake': 0.0,
                    'total_payout': 0.0,
                    'profit': 0.0,
                    'roi': 0.0
                }

            stats = championship_stats[competition]

            # Aggiorna il conteggio delle scommesse
            stats['total_bets'] += 1

            # Calcola stake e payout
            stake = bet_info.get("stakeAmount", 0) / 100  # Converti in euro
            payout = bet_info.get("paidAmount", 0) / 100  # Converti in euro

            # Assicurati che stake e payout siano numerici
            if not isinstance(stake, (int, float)) or not isinstance(payout, (int, float)):
                raise ValueError("Stake o payout non valido.")

            stats['total_stake'] = round(stats['total_stake'] + stake, 2)

            # Determina se la scommessa è vincente o perdente
            if bet_info.get("betState") == "PAID":  # Considera vincente solo se betState è "PAID"
                stats['wins'] += 1
                stats['total_payout'] = round(stats['total_payout'] + payout, 2)  # Aggiungi il payout solo se la scommessa è vincente
            else:
                stats['losses'] += 1  # Qualsiasi stato diverso da "PAID" è considerato perdente

        except KeyError as e:
            print(f"Chiave mancante nell'elaborazione di una scommessa: {e}")
        except ValueError as e:
            print(f"Errore di valore nell'elaborazione di una scommessa: {e}")
        except Exception as e:
            continue

    # Calcola profitto e ROI per ogni campionato
    for competition, stats in championship_stats.items():
        stats['profit'] = round(stats['total_payout'] - stats['total_stake'], 2)
        if stats['total_stake'] > 0:
            stats['roi'] = round((stats['profit'] / stats['total_stake']) * 100, 2)
        else:
            stats['roi'] = 0.0

    return championship_stats
 

def save_championship_stats_json(championship_stats):
    username, password, token_jwt, account_id, token = load(CREDENTIALS_PATH)
    filename = f"statistiche_campionati_{username}.json"
    try:
        export_path = os.path.join(os.getcwd(), "campionati")
        if not os.path.exists(export_path):
            try:
                os.makedirs(export_path)
            except PermissionError as e:
                print(f"Permessi insufficienti per creare la directory di esportazione: {e}")
                return

        file_path = os.path.join(export_path, filename)

        # Salva il dizionario delle statistiche in un file JSON con indentazione per una migliore leggibilità
        with open(file_path, mode='w', encoding='utf-8') as json_file:
            json.dump(championship_stats, json_file, ensure_ascii=False, indent=4)
            print("\n\nSTATISTICHE DEI CAMPIONATI SALVATE CORRETTAMENTE")
    except Exception as e:
        print(f"Errore durante il salvataggio delle statistiche: {e}")

def load_user_specific_bets(usernames):
    try:
        export_path = os.path.join(os.getcwd(), "export")
        files = [f for f in os.listdir(export_path) if f.startswith("bets_") and f.endswith(".pkl")]
        if not files:
            print("Nessun file di scommesse trovato.")
            return []
        user_bets_and_details = []
        for filename in files:
            # Estrai il nome utente dal nome del file
            username_in_file = filename.split('_')[1]
            if username_in_file in usernames:
                with open(os.path.join(export_path, filename), "rb") as file:
                    bets_and_details = pickle.load(file)
                    user_bets_and_details.extend(bets_and_details)
        print(f"Dati caricati per gli utenti: {', '.join(usernames)}")
        return user_bets_and_details
    except Exception as e:
        print(f"Errore durante il caricamento: {e}")
        return []
    except Exception as e:
        print(f"Errore durante il caricamento: {e}")
        return []
    except Exception as e:
        print(f"Errore durante il caricamento: {e}")
        return []


def main():
    while True:
        print("Vuoi caricare i dati da un file esistente o scaricarli da Sisal?")
        print("1. Carica da file")
        print("2. Scarica da Sisal (CONSIGLIATO SE ACCOUNT MAI ANALIZZATO)")
        print("3. Esci")
        choice = input("Seleziona un'opzione (1/2/3): ")

        bets_and_details = []

        if choice == '1':
            while True:
                print("\nVuoi analizzare il singolo utente, più utenti o tutti gli utenti insieme?")
                print("1. Utente singolo (utente preselezionato nel file delle credenziali)")
                print("2. Più utenti (scegli tu quali utenti analizzare)")
                print("3. Tutti gli utenti")
                print("4. Torna indietro")
                user_choice = input("Seleziona un'opzione (1/2/3/4): ")

                if user_choice == '1':
                    bets_and_details = load_bets()
                    if bets_and_details:
                        break
                    else:
                        print("Nessun file di scommesse trovato per l'utente specificato. Riprova o torna indietro.")
                elif user_choice == '2':
                    usernames = input("Inserisci gli username degli utenti da analizzare (separati da una virgola): ").split(',')
                    usernames = [username.strip() for username in usernames]
                    bets_and_details = load_user_specific_bets(usernames)
                    if bets_and_details:
                        break
                    else:
                        print("Nessun file di scommesse trovato per gli utenti specificati. Riprova o torna indietro.")
                elif user_choice == '3':
                    bets_and_details = load_all_bets()
                    if bets_and_details:
                        break
                    else:
                        print("Nessun file di scommesse trovato. Riprova o torna indietro.")
                elif user_choice == '4':
                    bets_and_details = None
                    break
                else:
                    print("Scelta non valida. Riprova.")

            if user_choice == '3':
                continue

        elif choice == '2':
            username, password, token_jwt, account_id, token = load(CREDENTIALS_PATH)
            print(f"INIZIO IL LOGIN PER L'UTENTE {username}")
            account = login()
            if account:
                bets_and_details = fetch_tickets()
                if bets_and_details:
                    save_bets(bets_and_details, username)
                else:
                    print("Errore durante il recupero delle scommesse. Riprova.")
                    continue
        elif choice == '3':
            print("Uscita dal programma.")
            break
        else:
            print("Scelta non valida. Riprova.")
            continue

        if bets_and_details is None or not bets_and_details:
            print("Nessuna scommessa da analizzare. Torna al menu principale per riprovare.")
            continue

        # Organizza le scommesse
        sport_bets_dict, competition_bets_dict, market_bets_dict = organize_bets(bets_and_details)

        # Menu interattivo con filtri
        while True:
            print("\nMenu:")
            print("1. Analisi personalizzata con filtri SPORT/CAMPIONATO/MERCATO")
            print("2. Top 5 campionati per numero di vittorie")
            print("3. Top 5 campionati per guadagni/ROI")
            print("4. Salva statistiche per ogni campionato")
            print("5. Back")
            option = input("Seleziona un'opzione: ")

            if option == '1':
                # Filtri
                sport_filter = None
                competition_filter = None
                market_filter = None

                # Filtraggio per sport
                sport_filter_choice = input("Vuoi filtrare per sport? (s/n/back): ").lower()
                if sport_filter_choice == 'back':
                    continue
                if sport_filter_choice == 's':
                    display_sport_list = input("Vuoi vedere la lista degli sport disponibili? (s/n/back): ").lower()
                    if display_sport_list == 'back':
                        continue
                    if display_sport_list == 's':
                        sports = set(bet[1]["result"]["predictions"][0]["sportDescription"] for bet in bets_and_details)
                        display_list(sports, "Sport Disponibili")
                    sport_filter = get_user_input("Inserisci il nome dello sport da filtrare (digita 'back' per tornare, 'exit' per uscire): ")
                    if sport_filter in ['back', 'exit']:
                        if sport_filter == 'exit':
                            print("Uscita dal programma.")
                            break
                        else:
                            continue

                # Filtraggio per campionato
                comp_filter_choice = input("Vuoi filtrare per campionato? (s/n/back): ").lower()
                if comp_filter_choice == 'back':
                    continue
                if comp_filter_choice == 's':
                    display_comp_list = input("Vuoi vedere la lista dei campionati disponibili? (s/n/back): ").lower()
                    if display_comp_list == 'back':
                        continue
                    if display_comp_list == 's':
                        competitions = get_filtered_competitions(bets_and_details, sport_filter)
                        display_list(competitions, "Campionati Disponibili")
                    competition_filter = get_user_input("Inserisci il nome del campionato da filtrare (digita 'back' per tornare, 'exit' per uscire): ")
                    if competition_filter in ['back', 'exit']:
                        if competition_filter == 'exit':
                            print("Uscita dal programma.")
                            break
                        else:
                            continue

                # Filtraggio per mercato (selectionDescription)
                market_filter_choice = input("Vuoi filtrare per mercato? (s/n/back): ").lower()
                if market_filter_choice == 'back':
                    continue
                if market_filter_choice == 's':
                    display_market_list = input("Vuoi vedere la lista dei mercati disponibili? (s/n/back): ").lower()
                    if display_market_list == 'back':
                        continue
                    if display_market_list == 's':
                        markets = get_filtered_markets(bets_and_details, sport_filter, competition_filter)
                        display_list(markets, "Mercati Disponibili")
                    market_filter = get_user_input("Inserisci il nome del mercato da filtrare (digita 'back' per tornare, 'exit' per uscire): ")
                    if market_filter in ['back', 'exit']:
                        if market_filter == 'exit':
                            print("Uscita dal programma.")
                            break
                        else:
                            continue

                # Applica i filtri
                filtered_bets = apply_filters(bets_and_details, sport_filter, competition_filter, market_filter)

                if not filtered_bets:
                    print("Nessuna scommessa trovata con i filtri specificati.")
                    continue

                # Calcola le statistiche sulle scommesse filtrate
                stats = aggregate_info(filtered_bets)
                titolo_analisi = "Risultati dell'analisi per"
                if sport_filter:
                    titolo_analisi += f" sport: {sport_filter}"
                if competition_filter:
                    titolo_analisi += f", campionato: {competition_filter}"
                if market_filter:
                    titolo_analisi += f", mercato: {market_filter}"

                print('\n')
                print(titolo_analisi)
                print(f"Vittorie: {stats['paid']}")
                print(f"Perdite: {stats['losing']}")
                print(f"Totale scommesse: {stats['total']}")
                print(f"Importo totale puntato: {stats['total_stake']:.2f}€")
                print(f"Importo totale vinto: {stats['paid_amount']:.2f}€")
                print(f"Profitto: {stats['profit']:.2f}€")
                print(f"ROI: {stats['roi']:.2f}%")

            elif option == '2':
                top_wins(bets_and_details)
            elif option == '3':
                top_roi(bets_and_details)
            elif option == '4':
                championship_stats = calculate_championship_stats(bets_and_details)
                save_championship_stats_json(championship_stats)
            elif option == '5':
                print("")
                break
            else:
                print("Opzione non valida. Riprova.")

if __name__ == "__main__":
    main()

