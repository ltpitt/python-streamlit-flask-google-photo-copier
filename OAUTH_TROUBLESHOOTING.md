# 🔧 Risoluzione Errore "Accesso bloccato: la richiesta dell'app non è valida"

## Problema
Google mostra l'errore: **"Accesso bloccato: la richiesta dell'app non è valida"**

## Causa
L'app OAuth è in modalità "Testing" ma il tuo account non è nella lista degli utenti di test.

## Soluzione

### Passo 1: Vai alla Google Cloud Console
1. Apri: https://console.cloud.google.com/apis/credentials/consent
2. Seleziona il progetto: **Google Photos Sync**

### Passo 2: Configura OAuth Consent Screen
1. Clicca su **"OAuth consent screen"** nel menu laterale
2. Dovresti vedere lo stato dell'app: **"Testing"** o **"In production"**

### Passo 3: Aggiungi Utenti di Test
1. Scorri fino alla sezione **"Test users"**
2. Clicca su **"+ ADD USERS"**
3. Inserisci il tuo indirizzo email Google (quello che usi per accedere)
4. Clicca **"Save"**

### Passo 4: Verifica le Impostazioni

#### Controlla che siano configurati:
- ✅ **User Type**: External
- ✅ **Publishing status**: Testing (va bene per sviluppo)
- ✅ **Test users**: Il tuo indirizzo email deve essere nella lista

#### Scopes richiesti:
- ✅ `https://www.googleapis.com/auth/photoslibrary.readonly`
- ✅ `https://www.googleapis.com/auth/photoslibrary`

#### Authorized redirect URIs:
- ✅ `http://localhost:5000/api/auth/callback`

### Passo 5: Riprova l'Autenticazione
1. Riavvia Flask se necessario:
   ```powershell
   .venv\Scripts\Activate.ps1
   python -m flask --app src.google_photos_sync.api.app run --port 5000
   ```
2. Vai su Streamlit: http://localhost:8501
3. Clicca "Accedi con Google"
4. Ora dovrebbe funzionare! ✅

## Screenshot Utili

### Dove trovare "Test users":
```
Google Cloud Console
└── APIs & Services
    └── OAuth consent screen
        ├── App information
        ├── Scopes
        └── Test users  ← QUI!
            └── + ADD USERS
```

## Note Importanti

### Modalità Testing vs Production
- **Testing**: Solo utenti nella lista possono accedere (max 100 utenti)
- **Production**: Tutti possono accedere, ma richiede verifica Google (processo lungo)

**Per sviluppo, usa Testing e aggiungi il tuo account alla lista!**

### Se Continui ad Avere Errori

1. **Verifica redirect URI**:
   - In Google Console deve essere: `http://localhost:5000/api/auth/callback`
   - Nel file `.env` deve essere: `GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/callback`

2. **Verifica Client ID e Secret**:
   - Nel file `.env` devono corrispondere a quelli in Google Console
   - Controlla che non ci siano spazi extra

3. **Cancella cookie del browser**:
   - A volte Google memorizza errori precedenti
   - Prova in modalità incognito

4. **Controlla i log di Flask**:
   - Guarda nel terminale dove sta girando Flask
   - Cerca errori o warning

## Comandi Utili

```powershell
# Attiva virtual environment
.venv\Scripts\Activate.ps1

# Avvia Flask
python -m flask --app src.google_photos_sync.api.app run --port 5000

# In un altro terminale, avvia Streamlit
.venv\Scripts\Activate.ps1
python -m streamlit run src/google_photos_sync/ui/app.py
```

## Link Rapidi
- [Google Cloud Console - OAuth Consent](https://console.cloud.google.com/apis/credentials/consent)
- [Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials)
- [Google Photos API Scopes](https://developers.google.com/photos/library/guides/authentication-authorization)
