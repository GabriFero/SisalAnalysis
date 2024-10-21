GUIDA PER UTILIZZARE IL PARSER
creare un ambiente virtuale usando il comando python -m venv .venv

se non è gia stato fatto bisogna installare le librerie 
dal file requirements.txt con il seguente comando pip install -r requirements.txt

una volta installate le librerie bisogna inserire i dati dell'account che si vuole analizzare( questo processo dovra essere fatto ogni qualvolta si ha un nuovo account da analizzare oppure uno stesso account con nuove scommesse), i dati andtranno inseriti all'interno del file credenziali.json

La prima volta di ogni account partira un login su sisal(puo essere ripetuto in automatico fino a 3 volte in caso di fallimento del login)
Se invece l'account da analizzare è gia stato scaricato bastera premere 1 per caricare il file

A questo punto abbiamo 3 scelte:
premere 1 se si vuole analizzare l'utente che abbiamoinserito nel file credenziali.json

premre 2 se si vuole sceglire quali account gia scaricati analizzare insieme: bisognera inserire i nomi utenti nel terminale

premere 3 se si vogliono analizzare tutti gli utenti gia analizzati

4 per otrnare indietro

una volta fatta la nostra scelta avremo davanti 5 possiblita di scelta

1 analizzare i dati incrocaiti tra sport campionato e mercato, possiamo scegliere noi quali paramentri mettere (per ogni parametro si ha una lista di sport/campionati e meracti che i possono scegliere se io scelgo basket e voglio vederei campionati disponibli mi usciranno ovviamnete solo i cmpionati disponibili per il basket, stessa cosa per i mercati)

2 ci da i top 5 campionati per schedine vinte

3 ci da i top 5 campionati per ROI/guadagno

4 ci salva in un file JSON tutte le statistiche per ogni campionatoil file sara salvato nella cartela campionati e avra anche il nome dell'utente che abbiamo analizzato

