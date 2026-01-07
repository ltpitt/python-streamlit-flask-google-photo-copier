# Google Photos Sync - User Guide

**Welcome!** This guide will walk you through everything you need to know to safely sync your Google Photos between accounts. Don't worry if you're not technical - we'll explain everything step by step.

## Table of Contents

1. [What Does This Application Do?](#what-does-this-application-do)
2. [Before You Start](#before-you-start)
3. [Setting Up Google Cloud (One-Time Setup)](#setting-up-google-cloud-one-time-setup)
4. [Installing the Application](#installing-the-application)
5. [Running the Application](#running-the-application)
6. [Authenticating Your Accounts](#authenticating-your-accounts)
7. [Comparing Accounts (Safe Preview)](#comparing-accounts-safe-preview)
8. [Syncing Accounts (Makes Changes)](#syncing-accounts-makes-changes)
9. [Troubleshooting Common Issues](#troubleshooting-common-issues)
10. [Frequently Asked Questions (FAQ)](#frequently-asked-questions-faq)
11. [Getting Help](#getting-help)

---

## What Does This Application Do?

**Google Photos Sync** copies all your photos from one Google Photos account (called the "source") to another Google Photos account (called the "target"). Think of it like making an exact backup of your photo library.

### Key Features

✅ **Safe Preview**: See exactly what will change before making any changes  
✅ **One Direction**: Photos go from source → target (never the reverse)  
✅ **Complete Copy**: All photos and their information (date, location, camera details)  
✅ **No Duplicates**: Running it multiple times is safe - won't create duplicates  
✅ **Warnings**: Multiple safety checks before deleting anything

### Important Safety Information

⚠️ **This application will modify your target account** to make it exactly match your source account. This means:
- Photos on the source will be **added** to the target
- Extra photos on the target (not on source) will be **deleted**
- **Always preview changes first** using the Compare feature

---

## Before You Start

### What You'll Need

1. **Two Google Accounts**
   - **Source account**: The account with photos you want to copy FROM
   - **Target account**: The account you want to copy photos TO

2. **A Computer**
   - Windows, Mac, or Linux
   - Internet connection
   - Web browser (Chrome, Firefox, Safari, Edge)

3. **About 30 Minutes**
   - First-time setup takes 20-30 minutes
   - After setup, syncing is quick (depends on photo count)

4. **Python 3.10 or Newer**
   - Don't worry, we'll show you how to check and install

### Prerequisites Checklist

Before continuing, make sure you have:

- [ ] Access to both Google accounts (email and password)
- [ ] Administrative access to your computer (to install software)
- [ ] Stable internet connection
- [ ] At least 500MB free disk space

---

## Setting Up Google Cloud (One-Time Setup)

Google requires applications to register before accessing Google Photos. This is a security measure to protect your photos. You only need to do this once.

### Step 1: Create a Google Cloud Project

1. **Go to Google Cloud Console**
   - Open your web browser
   - Visit: [https://console.cloud.google.com/](https://console.cloud.google.com/)
   - Sign in with **either** of your Google accounts (doesn't matter which)

2. **Create a New Project**
   - Click on the project dropdown at the top of the page (says "Select a project")
   - Click **"NEW PROJECT"** button in the top-right
   - Project name: Enter `Google Photos Sync` (or any name you like)
   - Click **"CREATE"**
   - Wait 10-30 seconds for the project to be created

3. **Select Your New Project**
   - Click the project dropdown again
   - Click on your newly created project (`Google Photos Sync`)
   - Verify the project name appears at the top

### Step 2: Enable Google Photos API

1. **Open API Library**
   - In the left sidebar, click **"APIs & Services"** > **"Library"**
   - Or visit: [https://console.cloud.google.com/apis/library](https://console.cloud.google.com/apis/library)

2. **Search for Photos API**
   - In the search box, type: `Photos Library API`
   - Click on **"Photos Library API"** in the results

3. **Enable the API**
   - Click the blue **"ENABLE"** button
   - Wait 10-20 seconds for it to enable
   - You should see "API enabled" confirmation

### Step 3: Create OAuth Credentials

1. **Configure OAuth Consent Screen**
   - In the left sidebar, click **"APIs & Services"** > **"OAuth consent screen"**
   - Or visit: [https://console.cloud.google.com/apis/credentials/consent](https://console.cloud.google.com/apis/credentials/consent)

2. **Choose User Type**
   - Select **"External"** (allows any Google account)
   - Click **"CREATE"**

3. **Fill Out App Information**
   - **App name**: `Google Photos Sync`
   - **User support email**: Select your email from dropdown
   - **Developer contact information**: Enter your email address
   - Leave other fields blank for now
   - Click **"SAVE AND CONTINUE"**

4. **Configure Scopes**
   - Click **"ADD OR REMOVE SCOPES"**
   - In the filter box, search for: `photoslibrary`
   - Check these two scopes:
     - ✅ `https://www.googleapis.com/auth/photoslibrary.readonly`
     - ✅ `https://www.googleapis.com/auth/photoslibrary.appendonly`
   - Click **"UPDATE"** at the bottom
   - Click **"SAVE AND CONTINUE"**

5. **Add Test Users**
   - Click **"ADD USERS"**
   - Enter **both** your Google account email addresses:
     - Your source account email
     - Your target account email
   - Click **"ADD"**
   - Click **"SAVE AND CONTINUE"**
   - Click **"BACK TO DASHBOARD"**

6. **Create OAuth Client ID**
   - In the left sidebar, click **"APIs & Services"** > **"Credentials"**
   - Click **"+ CREATE CREDENTIALS"** at the top
   - Select **"OAuth client ID"**

7. **Configure OAuth Client**
   - **Application type**: Select **"Desktop app"**
   - **Name**: `Google Photos Sync Desktop Client`
   - Click **"CREATE"**

8. **Save Your Credentials**
   - A popup appears with your credentials
   - **IMPORTANT**: Copy these somewhere safe - you'll need them soon
     - **Client ID**: Starts with `...apps.googleusercontent.com`
     - **Client Secret**: Random string of letters and numbers
   - Click **"DOWNLOAD JSON"** to save a backup copy
   - Click **"OK"** to close the popup

**✅ Google Cloud Setup Complete!** You now have the credentials needed to access Google Photos.

---

## Installing the Application

### Step 1: Check Python Installation

1. **Open Terminal/Command Prompt**
   - **Windows**: Press `Win + R`, type `cmd`, press Enter
   - **Mac**: Press `Cmd + Space`, type `Terminal`, press Enter
   - **Linux**: Press `Ctrl + Alt + T`

2. **Check Python Version**
   - Type this command and press Enter:
     ```bash
     python --version
     ```
   - Or try:
     ```bash
     python3 --version
     ```

3. **Verify Python Version**
   - You should see: `Python 3.10.x` or `Python 3.11.x` or higher
   - If you see `Python 2.x` or an error, you need to install Python 3.10+

4. **Install Python (If Needed)**
   - Visit: [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - Download Python 3.10 or newer
   - Run the installer
   - **IMPORTANT**: Check "Add Python to PATH" during installation
   - After installation, restart your terminal and try step 2 again

### Step 2: Download the Application

1. **Download from GitHub**
   - Visit: [https://github.com/ltpitt/python-streamlit-flask-google-photo-copier](https://github.com/ltpitt/python-streamlit-flask-google-photo-copier)
   - Click the green **"Code"** button
   - Click **"Download ZIP"**
   - Save the file to your Downloads folder

2. **Extract the ZIP File**
   - **Windows**: Right-click the ZIP file > **"Extract All"** > Choose a location
   - **Mac**: Double-click the ZIP file (auto-extracts to Downloads)
   - **Linux**: Right-click > **"Extract Here"**

3. **Open Terminal in Project Folder**
   - Navigate to the extracted folder
   - **Windows**: Hold Shift, right-click in the folder > **"Open PowerShell window here"**
   - **Mac/Linux**: Right-click > **"Open in Terminal"** (or drag folder to Terminal)

### Step 3: Install uv (Fast Package Manager)

**What is uv?** It's a modern, super-fast tool for installing Python packages (10-100x faster than pip).

1. **Install uv**
   - **Mac/Linux**: Run this command:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - **Windows (PowerShell)**: Run this command:
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
   - **Alternative (any system)**: If above doesn't work:
     ```bash
     pip install uv
     ```

2. **Verify uv Installation**
   - Type:
     ```bash
     uv --version
     ```
   - You should see a version number (e.g., `uv 0.9.0`)

### Step 4: Set Up the Application

1. **Create Virtual Environment**
   - This keeps the application's files separate from your system
   - Run:
     ```bash
     uv venv
     ```
   - Wait 5-10 seconds. You should see: "Virtual environment created"

2. **Activate Virtual Environment**
   - **Windows (PowerShell)**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
     - If you get an error about execution policy:
       ```powershell
       Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
       ```
       Then try activating again.
   
   - **Mac/Linux**:
     ```bash
     source .venv/bin/activate
     ```
   
   - **Success**: You should see `(.venv)` at the start of your command prompt

3. **Install Application Dependencies**
   - This downloads all the software the application needs
   - Run:
     ```bash
     uv pip install -r requirements.txt -r requirements-dev.txt
     ```
   - This takes 10-30 seconds (much faster with uv!)
   - You'll see a lot of text scrolling - this is normal

4. **Install the Application**
   - Run:
     ```bash
     uv pip install -e .
     ```
   - Takes 5-10 seconds

### Step 5: Configure Application

1. **Create Configuration File**
   - Copy the example configuration:
     - **Windows**:
       ```powershell
       copy .env.example .env
       ```
     - **Mac/Linux**:
       ```bash
       cp .env.example .env
       ```

2. **Edit Configuration File**
   - Open the `.env` file in a text editor (Notepad, TextEdit, VS Code, etc.)
   - Find these lines:
     ```bash
     GOOGLE_CLIENT_ID=your_google_client_id_here
     GOOGLE_CLIENT_SECRET=your_google_client_secret_here
     ```
   - Replace with your credentials from Step 3 of Google Cloud Setup:
     ```bash
     GOOGLE_CLIENT_ID=123456789-abcdef.apps.googleusercontent.com
     GOOGLE_CLIENT_SECRET=GOCSPX-abc123def456
     ```
   - **IMPORTANT**: Keep the `.env` file private - never share it!

3. **Save the File**
   - Save and close the `.env` file

**✅ Installation Complete!** The application is now ready to use.

---

## Running the Application

The application has two parts that work together:
1. **Flask API** (the "brain" - runs in the background)
2. **Streamlit UI** (the "face" - what you interact with)

You need to run both at the same time.

### Step 1: Start the Flask API

1. **Open First Terminal Window**
   - Keep your terminal from installation open, or open a new one
   - Navigate to the project folder
   - Activate the virtual environment (see "Activate Virtual Environment" in installation)

2. **Start Flask API**
   - Run:
     ```bash
     python -m flask --app src/google_photos_sync/api/app.py run
     ```
   - You should see:
     ```
     * Running on http://127.0.0.1:5000
     * Running on http://127.0.0.1:5000 (Press CTRL+C to quit)
     ```
   - **Keep this terminal window open** - don't close it!

### Step 2: Start the Streamlit UI

1. **Open Second Terminal Window**
   - Open a **NEW** terminal window (keep the first one running)
   - Navigate to the same project folder
   - Activate the virtual environment again

2. **Start Streamlit UI**
   - Run:
     ```bash
     streamlit run src/google_photos_sync/ui/app.py
     ```
   - You should see:
     ```
     You can now view your Streamlit app in your browser.
     Local URL: http://localhost:8501
     ```
   - Your web browser should open automatically to the application
   - If it doesn't, manually open: [http://localhost:8501](http://localhost:8501)

### Step 3: Verify Both Are Running

You should now have:
- ✅ First terminal: Flask API running (shows log messages)
- ✅ Second terminal: Streamlit UI running (shows log messages)
- ✅ Web browser: Application interface open

**Tip**: Minimize the terminal windows - you don't need to watch them. Just leave them running.

---

## Authenticating Your Accounts

Before you can compare or sync, you need to give the application permission to access your Google Photos accounts.

### Authenticate Source Account

1. **In the Application UI**
   - You'll see a section labeled **"Source Account (Copy FROM)"**
   - Click the **"Authenticate Source Account"** button

2. **Google Sign-In Page Opens**
   - A new browser tab opens to Google's sign-in page
   - Sign in with your **source account** (the one with photos to copy)
   - If already signed in, select the source account

3. **Grant Permissions**
   - Google shows a warning: "Google hasn't verified this app"
   - Click **"Advanced"** (or "Show Advanced")
   - Click **"Go to Google Photos Sync (unsafe)"**
   - **Don't worry**: This is normal for personal projects. You created this app yourself.

4. **Allow Access**
   - Google shows: "Google Photos Sync wants to access your Google Account"
   - Review the permissions:
     - ✅ "View your Google Photos library" (read-only, safe)
     - ✅ "Add to your Google Photos library" (needed for target account)
   - Click **"Allow"** or **"Continue"**

5. **Return to Application**
   - You'll be redirected back to the application
   - You should see: **"✅ Source Account Authenticated"**
   - The authenticated email address is displayed

### Authenticate Target Account

1. **In the Application UI**
   - You'll see a section labeled **"Target Account (Copy TO)"**
   - Click the **"Authenticate Target Account"** button

2. **Google Sign-In Page Opens**
   - A new browser tab opens
   - **IMPORTANT**: Sign in with your **target account** (NOT the source!)
   - If you were signed into source, click **"Use another account"**
   - Enter target account credentials

3. **Grant Permissions**
   - Same steps as source account:
   - Click **"Advanced"** > **"Go to Google Photos Sync (unsafe)"**
   - Review permissions
   - Click **"Allow"**

4. **Return to Application**
   - You should see: **"✅ Target Account Authenticated"**
   - Both accounts now show as authenticated

**✅ Authentication Complete!** You can now compare and sync your accounts.

### Troubleshooting Authentication

**Problem**: "Access blocked: This app's request is invalid"
- **Solution**: Check that you enabled Photos Library API in Google Cloud Console
- **Solution**: Verify you added both email addresses as test users

**Problem**: "The developer hasn't given you access to this app"
- **Solution**: Make sure you added your email addresses as test users in OAuth consent screen

**Problem**: "This app isn't verified"
- **Solution**: This is normal. Click "Advanced" > "Go to [app name] (unsafe)"
- **Why**: Apps must go through verification for public use. For personal use, this is expected.

---

## Comparing Accounts (Safe Preview)

**Before making any changes**, always compare your accounts to see what will happen.

### What Comparison Does

Comparison is **100% safe** - it only **looks** at your photos, never modifies anything. It shows you:
- 📊 How many photos are in each account
- ➕ Photos that will be **added** to target (missing from target)
- 🔄 Photos with **different information** (metadata)
- ➖ Photos that will be **deleted** from target (not on source)

### Running a Comparison

1. **Click Compare Tab**
   - In the application, click the **"Compare Accounts"** tab at the top

2. **Start Comparison**
   - Click the **"Compare Accounts"** button
   - A progress bar appears

3. **Wait for Results**
   - This can take 1-5 minutes depending on photo count
   - The application is counting and comparing all photos
   - Don't close the browser or terminals

4. **Review Results**
   - **Statistics Summary**:
     ```
     Source Account: source@gmail.com (1,234 photos)
     Target Account: target@gmail.com (567 photos)
     
     Missing on Target: 700 photos
     Extra on Target: 33 photos
     Different Metadata: 15 photos
     ```
   - **Detailed Lists**:
     - Photos to be added (with filenames and dates)
     - Photos to be deleted (with filenames)
     - Photos with metadata differences

### Understanding the Results

**Missing on Target** (Photos to be Added)
- These photos exist on source but not on target
- During sync, they will be **copied** to target
- Example: `vacation2024.jpg - Created: 2024-07-15`

**Extra on Target** (Photos to be Deleted)
- These photos exist on target but not on source
- During sync, they will be **DELETED** from target
- ⚠️ **WARNING**: Make sure you want to delete these!

**Different Metadata**
- These photos exist on both, but have different information
- During sync, target's information will be **updated** to match source
- Usually minor differences (filename, date, camera info)

### What to Do Next

✅ **If results look correct**:
- Proceed to syncing (next section)

❌ **If you see unexpected deletions**:
- **DO NOT SYNC**
- Review which photos are "Extra on Target"
- If you want to keep them, copy them to source account first
- Run comparison again

⚠️ **If in doubt**:
- Ask for help (see "Getting Help" section)
- Better safe than sorry!

---

## Syncing Accounts (Makes Changes)

**⚠️ WARNING**: Syncing **MODIFIES** your target account. Always compare first!

### Before You Sync - Important Checklist

Before clicking the sync button, make sure:

- [ ] You've run a comparison and reviewed the results
- [ ] You're okay with photos being **deleted** from target (if any)
- [ ] You're okay with target becoming **exactly** like source
- [ ] Both accounts are authenticated
- [ ] You have a stable internet connection
- [ ] You have time to let it complete (don't interrupt)

### Running a Sync

1. **Click Sync Tab**
   - In the application, click the **"Sync Accounts"** tab at the top

2. **Review Warning Message**
   - Read the big red warning box:
     ```
     ⚠️ DESTRUCTIVE OPERATION WARNING
     
     Target account (target@gmail.com) will be MODIFIED to exactly 
     match source account (source@gmail.com).
     
     This includes:
     - Adding 700 photos to target
     - DELETING 33 photos from target
     
     This cannot be undone.
     ```

3. **First Confirmation**
   - Read the warning carefully
   - Check the box: ☑️ "I understand that [target email] will be permanently modified"

4. **Second Confirmation**
   - Type the exact target account email in the text box
   - Example: Type `target@gmail.com`
   - Must match exactly (including @gmail.com)

5. **Final Confirmation**
   - The **"🔴 EXECUTE SYNC (Irreversible)"** button becomes clickable
   - Take a deep breath
   - Click the button if you're sure

6. **Sync Progress**
   - A progress bar appears showing:
     - Current operation (Adding photo, Updating metadata, Deleting photo)
     - Photos processed / Total photos
     - Percentage complete
     - Estimated time remaining

7. **Wait for Completion**
   - **DO NOT** close the browser
   - **DO NOT** close the terminal windows
   - **DO NOT** turn off your computer
   - Let it finish - this can take 30 minutes to several hours for large libraries

8. **Review Results**
   - When complete, you'll see a summary:
     ```
     ✅ Sync Complete!
     
     Photos Added: 700
     Photos Deleted: 33
     Photos Updated: 15
     Failed Actions: 0
     
     Total Time: 1 hour 23 minutes
     ```

### During Sync - What to Expect

**Normal Behavior**:
- Progress bar moves gradually (may pause briefly)
- Terminal windows show log messages
- Internet connection is active
- Computer fan may run (CPU is working)

**Warning Signs**:
- Progress bar stuck for >10 minutes (see Troubleshooting)
- Many "Failed" messages (see Troubleshooting)
- Internet connection lost (will retry, but may need to restart)

### After Sync - Verification

1. **Check Your Target Account**
   - Open [https://photos.google.com](https://photos.google.com)
   - Sign in with **target account**
   - Verify photos are there
   - Spot-check a few photos (dates, locations correct)

2. **Run Comparison Again (Optional)**
   - Go back to Compare tab
   - Click "Compare Accounts"
   - Results should show:
     ```
     Missing on Target: 0 photos
     Extra on Target: 0 photos
     Different Metadata: 0 photos
     ```
   - This confirms accounts are identical

**✅ Sync Complete!** Your target account is now an exact copy of your source account.

### Safety Features During Sync

The application has several safety features:

1. **Idempotent**: Running sync multiple times is safe - won't create duplicates
2. **Retry Logic**: If a photo fails, it automatically retries 3 times
3. **Rate Limiting**: Waits if Google says "slow down" (prevents account issues)
4. **Progress Tracking**: You can see exactly what's happening
5. **Error Handling**: If something fails, you get a clear error message

---

## Troubleshooting Common Issues

### Installation Issues

**Issue**: "python: command not found"
- **Cause**: Python not installed or not in PATH
- **Fix**: Install Python 3.10+ from [python.org](https://www.python.org/downloads/)
- **Fix**: Make sure to check "Add Python to PATH" during installation
- **Fix**: Restart terminal after installation

**Issue**: "uv: command not found"
- **Cause**: uv not installed correctly
- **Fix**: Try alternative installation: `pip install uv`
- **Fix**: Restart terminal after installation

**Issue**: "ModuleNotFoundError: No module named 'flask'"
- **Cause**: Dependencies not installed or virtual environment not activated
- **Fix**: Activate virtual environment: `source .venv/bin/activate` (Mac/Linux) or `.venv\Scripts\Activate.ps1` (Windows)
- **Fix**: Install dependencies: `uv pip install -r requirements.txt`

### Authentication Issues

**Issue**: "Access blocked: This app's request is invalid"
- **Cause**: OAuth consent screen not configured correctly
- **Fix**: Verify you enabled Photos Library API in Google Cloud Console
- **Fix**: Check you added both email addresses as test users
- **Fix**: Wait 5 minutes for Google's servers to update, then try again

**Issue**: "Invalid client: no redirect_uri"
- **Cause**: GOOGLE_REDIRECT_URI in .env doesn't match Google Cloud settings
- **Fix**: In Google Cloud Console, add redirect URI: `http://localhost:8080/oauth2callback`
- **Fix**: In .env file, set: `GOOGLE_REDIRECT_URI=http://localhost:8080/oauth2callback`

**Issue**: "The developer hasn't given you access to this app"
- **Cause**: Email not added as test user
- **Fix**: In Google Cloud Console > OAuth consent screen > Test users > Add your email

**Issue**: Already signed into wrong Google account
- **Fix**: In OAuth popup, click "Use another account"
- **Fix**: Or sign out of Google in that browser first

### Comparison Issues

**Issue**: Comparison takes forever (stuck)
- **Cause**: Very large photo library (10,000+ photos)
- **Fix**: Be patient - can take 5-10 minutes for large libraries
- **Cause**: Network issue
- **Fix**: Check internet connection, restart comparison

**Issue**: "Error: Failed to list photos"
- **Cause**: Authentication expired
- **Fix**: Re-authenticate both accounts
- **Cause**: Network timeout
- **Fix**: Check internet connection and try again

### Sync Issues

**Issue**: Sync gets stuck at a certain percentage
- **Cause**: Rate limiting from Google (too many requests)
- **Fix**: Wait 5 minutes, it should resume automatically
- **Cause**: Network issue
- **Fix**: Check internet connection
- **If stuck >15 minutes**: Stop sync (Ctrl+C in terminal), wait 10 minutes, start again

**Issue**: Many "Failed" actions in sync results
- **Cause**: Photos deleted from source during sync
- **Fix**: Normal if you're cleaning up source. Re-run sync to catch up.
- **Cause**: Network issues
- **Fix**: Check internet, re-run sync (safe to run multiple times)

**Issue**: "Error: Rate limit exceeded"
- **Cause**: Making too many requests to Google too quickly
- **Fix**: Wait 30 minutes
- **Fix**: Reduce MAX_CONCURRENT_TRANSFERS in .env to 2 or 1
- **Fix**: Try sync again

**Issue**: Sync completes but photos missing on target
- **Cause**: Sync failed for some photos (check "Failed Actions" in results)
- **Fix**: Run sync again (safe, idempotent)
- **Fix**: Check specific error messages in terminal logs

### Application Won't Start

**Issue**: Flask fails to start
- **Cause**: Port 5000 already in use
- **Fix**: Close other applications using port 5000
- **Fix**: Or change port in .env: `FLASK_PORT=5001`

**Issue**: Streamlit fails to start
- **Cause**: Port 8501 already in use
- **Fix**: Close other Streamlit apps
- **Fix**: Streamlit will offer to use next available port - click Yes

### General Issues

**Issue**: Lost internet connection during sync
- **Fix**: Sync will retry automatically
- **If fails**: Stop sync, reconnect internet, run sync again (safe)

**Issue**: Computer went to sleep during sync
- **Fix**: Wake computer
- **Fix**: Check if sync is still running
- **If stopped**: Run sync again (safe, won't duplicate)

**Issue**: Accidentally closed terminal window
- **Fix**: Restart the application (see "Running the Application")
- **Fix**: Re-authenticate accounts
- **Fix**: Continue from where you left off

---

## Frequently Asked Questions (FAQ)

### General Questions

**Q: Is this safe to use?**  
A: Yes, if you follow the instructions. The application only accesses your photos through official Google APIs. Always preview changes with Compare before syncing.

**Q: Will this work with Google Photos free tier?**  
A: Yes, works with both free and paid Google Photos accounts.

**Q: How long does sync take?**  
A: Depends on photo count:
- 100 photos: ~5-10 minutes
- 1,000 photos: ~30-60 minutes
- 10,000 photos: ~4-8 hours

**Q: Can I stop and resume a sync?**  
A: Yes! Syncs are idempotent. If you stop (Ctrl+C), just run sync again. It will skip already-synced photos.

**Q: Will this create duplicates?**  
A: No. The application checks if photos already exist before adding them.

**Q: What happens if I run sync multiple times?**  
A: Nothing! It's safe. The second sync will see accounts are already identical and do nothing.

### About Source and Target

**Q: Which account should be source?**  
A: Source = the account with photos you want to keep/backup. Target = the backup/destination account.

**Q: Can I swap source and target?**  
A: Yes, but be careful! The application will make target match source. So swapping means deleting everything unique to the old source.

**Q: Can I sync multiple source accounts to one target?**  
A: No, not directly. You'd need to:
1. Sync Source A → Target
2. Then merge Source B into Source A
3. Then sync again

**Q: Can source and target be the same account?**  
A: No, that doesn't make sense. You need two different accounts.

### About Photos and Metadata

**Q: What metadata is preserved?**  
A: Everything:
- Creation date/time
- Location (GPS coordinates)
- Camera info (make, model, settings)
- Filename
- Descriptions
- Favorites

**Q: Are videos supported?**  
A: Yes! Videos are synced just like photos.

**Q: Are albums synced?**  
A: Not in version 0.1.0. Only photos and their metadata. Album support is planned for future versions.

**Q: What about Live Photos?**  
A: Yes, Live Photos are preserved (they're treated as videos).

### About Google Cloud Setup

**Q: Why do I need to create a Google Cloud project?**  
A: Google requires all applications accessing Google Photos to register. This is for security and to prevent abuse.

**Q: Does this cost money?**  
A: No! Google Photos API is free for personal use. Google Cloud is free for small projects like this.

**Q: Do I need a credit card?**  
A: No, you don't need to enable billing for this application.

**Q: What are "scopes"?**  
A: Scopes are permissions. We request:
- `readonly` - to read photos from source
- `appendonly` - to add photos to target (but not delete)

**Q: Why does Google say the app is "unsafe"?**  
A: Apps need verification for public use. Since this is for personal use, verification isn't required. You created the app yourself, so you can trust it.

### Troubleshooting

**Q: Comparison shows photos to delete, but I want to keep them on target. What do I do?**  
A: Don't sync! Instead:
1. Copy those photos from target to source first
2. Run comparison again
3. Now sync should show 0 deletions

**Q: Sync failed halfway. What do I do?**  
A: Just run sync again! It's safe. It will skip already-synced photos and continue from where it failed.

**Q: I got "Rate limit exceeded" error. What does this mean?**  
A: Google limits how many requests you can make per minute. Wait 30 minutes and try again. The application is designed to avoid this, but it can happen with very large libraries.

**Q: Can I use this on a server/cloud?**  
A: Advanced users can, but this guide is for local use. Server deployment requires additional configuration.

### Privacy and Security

**Q: Where are my photos stored?**  
A: Your photos stay in Google Photos. This application only streams them from source to target - never saves them permanently.

**Q: Where are my credentials stored?**  
A: In memory only while the application runs. They're never saved to disk.

**Q: Can others access my photos through this app?**  
A: No. Only you (with your Google login) can authorize access.

**Q: Should I share my GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET?**  
A: No! Keep them private. Anyone with these could access apps registered to your Google Cloud project.

---

## Getting Help

### Before Asking for Help

Try these steps first:

1. **Check Troubleshooting Section** (above) - most common issues are covered
2. **Check Terminal Logs** - error messages often explain the problem
3. **Restart the Application** - close terminals, start fresh
4. **Re-authenticate Accounts** - authentication can expire

### How to Get Help

If you're still stuck:

1. **GitHub Issues**
   - Visit: [https://github.com/ltpitt/python-streamlit-flask-google-photo-copier/issues](https://github.com/ltpitt/python-streamlit-flask-google-photo-copier/issues)
   - Click "New Issue"
   - Describe your problem:
     - What you were trying to do
     - What happened instead
     - Error messages (copy from terminal)
     - Your operating system (Windows/Mac/Linux)

2. **Include This Information**
   - Operating system and version
   - Python version (`python --version`)
   - Error messages (copy exact text)
   - Steps to reproduce the problem

3. **What NOT to Share**
   - Your GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET
   - Your Google account passwords
   - Your .env file

### Resources

- **Project Documentation**: [README.md](../README.md)
- **Architecture Details**: [docs/architecture.md](architecture.md)
- **Setup Guide**: [SETUP.md](../SETUP.md)
- **Google Photos API Docs**: [https://developers.google.com/photos](https://developers.google.com/photos)

---

## Next Steps

Now that you've successfully synced your photos:

1. **Regular Syncs**
   - Run comparison and sync periodically (weekly/monthly)
   - Keeps your backup account up to date

2. **Automation (Advanced)**
   - Advanced users can schedule syncs with cron (Linux/Mac) or Task Scheduler (Windows)

3. **Multiple Backups**
   - Consider syncing to multiple target accounts for redundancy

4. **Share Feedback**
   - If you found this useful, star the project on GitHub!
   - Report bugs or suggest features via GitHub Issues

---

**Congratulations!** 🎉 You've successfully set up and used Google Photos Sync. Your photos are now safely backed up.

**Last Updated**: 2025-01-07  
**Version**: 0.1.0

---

*This user guide is maintained with love for non-technical users. If anything is confusing, please let us know so we can improve it!*
