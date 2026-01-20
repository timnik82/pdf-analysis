# Mendeley API Setup Guide

This guide will walk you through setting up Mendeley API access for the DOI checker script.

---

## Step 1: Create a Mendeley Developer Account

1. **Sign in to Mendeley** at [https://www.mendeley.com/](https://www.mendeley.com/)
   - If you don't have an account, create one (it's free)

2. **Register for API Access** at [https://dev.mendeley.com/](https://dev.mendeley.com/)
   - Log in with your Mendeley credentials

---

## Step 2: Register Your Application

1. Go to [My Applications](http://dev.mendeley.com/myapps.html)

2. Click **"Create a new app"** or **"Register new application"**

3. Fill in the application details:
   - **Application Name**: e.g., "DOI Library Checker"
   - **Description**: e.g., "Script to check DOIs against my Mendeley library"
   - **Redirect URI**: `http://localhost:8080`
     > ⚠️ **Important**: This must be exactly `http://localhost:8080` for the script to work

4. Click **"Register Application"**

5. **Save your credentials**:
   - **Client ID**: A long string (e.g., `773`)
   - **Client Secret**: Another long string (keep this secret!)

---

## Step 3: Set Up Environment Variables

1. Navigate to your project directory:

   ```bash
   cd path/to/pdf-analysis
   ```

2. Create a `.env` file (copy from the example):

   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and add your credentials:

   ```bash
   MENDELEY_CLIENT_ID=your_client_id_here
   MENDELEY_CLIENT_SECRET=your_client_secret_here
   ```

4. **Security**: Add `.env` to `.gitignore` (already done if using the example)

---

## Step 4: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install requests python-dotenv
```

---

## Step 5: First-Time Authentication

The first time you run the script, you'll need to authenticate:

1. Run the script:

   ```bash
   python check_mendeley_dois_v2.py --interactive
   ```

2. The script will:
   - Open your web browser automatically
   - Ask you to log in to Mendeley
   - Ask permission to access your library
   - Redirect back to the script

3. After successful authentication:
   - Your access token will be saved to `mendeley_token.json`
   - Future runs won't require browser login (unless token expires)

---

## Troubleshooting

### "Redirect URI does not match"

- Make sure your registered redirect URI is exactly `http://localhost:8080`
- Check for typos in your app settings

### "Invalid client credentials"

- Double-check your Client ID and Secret in `.env`
- Make sure there are no extra spaces or quotes

### Token expired

- Delete `mendeley_token.json` and re-authenticate
- The script will automatically refresh tokens when possible

### Browser doesn't open automatically

- Copy the URL from the terminal and paste it into your browser manually
- After authorizing, copy the full redirect URL back to the terminal

---

## What Gets Stored?

- **`.env`**: Your API credentials (never commit this!)
- **`mendeley_token.json`**: Your OAuth access/refresh tokens (never commit this!)
- Both files are in `.gitignore` for security

---

## Rate Limits

Mendeley API has rate limits, but for personal library access they're generous. The script:

- Fetches your library in pages (default 100 documents per request)
- Caches library data to avoid repeated API calls
- Should work fine for libraries with thousands of documents

---

## Next Steps

Once setup is complete, see the main README for usage examples.
