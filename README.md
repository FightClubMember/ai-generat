# Premium Telegram Receipt Generator Bot

A highly realistic receipt generator bot for Telegram. It creates authentic receipts from grocery stores, cafes, boutique retail, and gas stations.

## 🚀 Premium Features

1. **Procedural 3D Tabletop Overlays**: Automatically generates wooden tables or concrete countertops, skews the receipt using 3D perspective transformations, and casts soft, realistic drop shadows.
2. **Dynamic 3D Fold Folds**: Creases and paper folds are rendered dynamically with light highlights and dark shadow edges to mimic physical paper.
3. **Thermal Printer Imperfections**: Print-head jitter, vertical scanner fade lines, faded ink lines, paper aging yellow-tint splits, and paper grain noise.
4. **Color Style Matching**: Upload a reference image, and the bot analyzes and extracts the dominant paper and text colors to match the layout's aesthetic style.
5. **Interactive UI**: No spammy slash commands. Everything is managed via a sleek settings control panel utilizing inline keyboards.
6. **Async & Thread-Safe**: Written using modern asyncio task architecture, running heavy CPU image filters on worker threads (`asyncio.to_thread`) to ensure the bot remains ultra-responsive under load.
7. **Production Ready**: Bundles a built-in HTTP server to respond to Render's health checks, allowing seamless deployment on free-tier Web Services.

---

## 🛠 Local Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure token**:
   - Create a file called `token.txt` in the root directory and paste your Telegram Bot Token in it, OR
   - Set the `BOT_TOKEN` environment variable.

3. **Run the bot**:
   ```bash
   python bot.py
   ```

---

## 🌐 Deploying to GitHub + Render

Render's free tier allows deploying **Web Services** that automatically sleep if they do not receive HTTP traffic. This bot includes a built-in background health-check server listening on the port designated by Render (the `PORT` environment variable), making it fully compatible with Render's free tier.

### Step 1: Create a GitHub Repository
1. Initialize a Git repository inside this directory:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of premium receipt generator bot"
   ```
2. Create a new repository on GitHub (public or private).
3. Follow the GitHub instructions to push your local repository:
   ```bash
   git remote add origin https://github.com/yourusername/receipt-generator-bot.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Render
1. Sign in to [Render](https://render.com/).
2. Click **New +** and select **Web Service**.
3. Connect your GitHub account and select your `receipt-generator-bot` repository.
4. Configure the service:
   - **Name**: `receipt-generator-bot`
   - **Language**: `Python`
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
5. Click **Advanced** to add Environment Variables:
   - Add Key: `BOT_TOKEN`, Value: `[Your Telegram Bot Token]`
6. Click **Deploy Web Service**.

Render will automatically install Python, install Pillow and Telegram dependencies, download Roboto Mono fonts on startup, spin up the HTTP health-check server, and launch the Telegram bot!
