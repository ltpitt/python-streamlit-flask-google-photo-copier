# OAuth Setup Guide

## Quick Start

### 1. Start the Flask API Backend

Prima di usare l'app Streamlit, devi avviare il backend Flask:

```powershell
# Assicurati che il virtual environment sia attivo
.venv\Scripts\Activate.ps1

# Avvia Flask API
python -m flask --app src/google_photos_sync/api/app run
```

L'API sarà disponibile su `http://localhost:5000`

### 2. Start Streamlit UI

In un **nuovo terminale** (tenendo Flask in esecuzione):

```powershell
# Attiva virtual environment
.venv\Scripts\Activate.ps1

# Avvia Streamlit
python -m streamlit run src/google_photos_sync/ui/app.py
```

L'UI sarà disponibile su `http://localhost:8501`

### 3. Configurare le Credenziali Google OAuth

Prima di autenticarti, devi configurare le credenziali OAuth:

1. Vai alla [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuovo progetto o selezionane uno esistente
3. Abilita la **Google Photos Library API**
4. Vai a **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Configura il tipo applicazione: **Web application**
6. Aggiungi URI di reindirizzamento autorizzati:
   - `http://localhost:5000/api/auth/callback`
   - `http://localhost:8080/oauth2callback`
7. Copia **Client ID** e **Client Secret**

### 4. Configura il File .env

Crea un file `.env` nella root del progetto:

```bash
cp .env.example .env
```

Modifica `.env` con le tue credenziali:

```dotenv
GOOGLE_CLIENT_ID=your_actual_client_id_here
GOOGLE_CLIENT_SECRET=your_actual_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8080/oauth2callback
API_BASE_URL=http://localhost:5000
```

### 5. Riavvia Flask API

Dopo aver configurato `.env`, riavvia Flask per caricare le credenziali:

```powershell
# Ctrl+C per fermare Flask, poi riavvia:
python -m flask --app src/google_photos_sync/api/app run
```

## Uso del Flusso OAuth

### Autenticazione nell'App

1. Vai alla pagina **Compare** nell'app Streamlit
2. Clicca su **"🔐 Accedi con Google (Source)"**
3. Si aprirà automaticamente una finestra del browser
4. Autorizza l'app ad accedere al tuo Google Photos
5. Google ti mostrerà un **codice di autorizzazione**
6. Copia il codice
7. Torna all'app Streamlit
8. Incolla il codice nel campo **"Authorization Code"**
9. Inserisci la tua **email Google**
10. Clicca **"Complete Authentication"**

### Note Importanti

- **Flask API deve essere in esecuzione** per il flusso OAuth
- Il browser si aprirà automaticamente, ma puoi anche cliccare il link manualmente
- Devi autenticare **sia Source che Target** per usare compare/sync
- Le credenziali vengono salvate e riutilizzate nelle sessioni successive

## Risoluzione Problemi

### "Cannot connect to API server"

- Verifica che Flask API sia in esecuzione su `http://localhost:5000`
- Controlla che `.env` contenga `API_BASE_URL=http://localhost:5000`

### "OAuth initiation failed"

- Verifica che `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` siano configurati correttamente in `.env`
- Riavvia Flask API dopo aver modificato `.env`

### "Invalid redirect URI"

- Verifica che l'URI di reindirizzamento in Google Cloud Console corrisponda a quello in `.env`
- URI comune: `http://localhost:8080/oauth2callback`

### Browser non si apre automaticamente

- Nessun problema! Usa il link cliccabile nell'app Streamlit
- Copia/incolla l'URL nel browser manualmente

## Architettura del Flusso

```
Streamlit UI (Port 8501)
    |
    | POST /api/auth/google
    v
Flask API (Port 5000)
    |
    | Genera authorization_url
    v
Browser → Google OAuth
    |
    | User authorizes
    v
User copies code → Streamlit
    |
    | GET /api/auth/callback?code=...
    v
Flask API
    |
    | Exchanges code for credentials
    | Saves credentials to filesystem
    v
Streamlit shows "Authenticated ✅"
```

## Sicurezza

- **Non committare `.env`** al repository (già in `.gitignore`)
- Le credenziali OAuth sono salvate in `~/.google_photos_sync/credentials/`
- In produzione, usa encryption per le credenziali salvate (vedi `CREDENTIAL_ENCRYPTION_KEY`)
- Ruota le credenziali OAuth regolarmente (ogni 90 giorni)

## Prossimi Passi

Dopo l'autenticazione:

1. Vai alla pagina **Compare** per vedere le differenze tra account
2. Vai alla pagina **Sync** per eseguire la sincronizzazione
3. Configura opzioni avanzate in **Settings**
