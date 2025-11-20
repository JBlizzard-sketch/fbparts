# EMPIRE v13 - Render Deployment Guide

## Deploy your Telegram bot to the cloud for 24/7 operation (FREE!)

---

## Why Render?

- ✅ **Free Tier**: Run your bot 24/7 at no cost
- ✅ **Auto-Deploy**: Push to GitHub → Auto-deploy
- ✅ **Zero Config**: Blueprint handles everything
- ✅ **Persistent Storage**: 1GB disk included
- ✅ **Logs & Monitoring**: Built-in dashboard
- ✅ **Custom Domains**: Optional

**Cost**: $0/month on free tier (sufficient for most users)

---

## Prerequisites

1. **GitHub Account** ([Sign up](https://github.com))
2. **Render Account** ([Sign up](https://render.com))
3. **Your Telegram Bot Token & User ID** (from local setup)
4. **(Optional) Groq API Key**

---

## Step-by-Step Deployment

### Step 1: Push to GitHub

1. **Create a new repository** on GitHub:
   - Go to [github.com/new](https://github.com/new)
   - Name it `empire-v13` (or any name you like)
   - Keep it **Private** (recommended for security)
   - Don't initialize with README (we already have code)

2. **Push your local code**:

   ```bash
   cd empire-v13
   
   # Initialize git if not already done
   git init
   
   # Add all files
   git add .
   
   # Commit
   git commit -m "Initial commit: EMPIRE v13"
   
   # Add GitHub as remote (replace with your repo URL)
   git remote add origin https://github.com/YOUR_USERNAME/empire-v13.git
   
   # Push to GitHub
   git branch -M main
   git push -u origin main
   ```

**Important**: Make sure `.env` is in `.gitignore` (it already is) so your secrets aren't exposed!

### Step 2: Connect to Render

1. **Go to Render Dashboard**: [dashboard.render.com](https://dashboard.render.com)

2. **Click "New +"** in the top right

3. **Select "Blueprint"**

4. **Connect your GitHub repository**:
   - Grant Render access to your GitHub
   - Select the `empire-v13` repository
   - Click "Connect"

5. **Render will detect `render.yaml`** and show you the service configuration

### Step 3: Configure Environment Variables

Render will prompt you to set:

1. **BOT_TOKEN**
   - Get from @BotFather
   - Example: `123456:ABC-DEF1234567890`

2. **OWNER_ID**
   - Get from @userinfobot
   - Example: `987654321` (just the number, no prefix!)

3. **GROQ_KEY** (Optional)
   - Get from console.groq.com
   - Example: `gsk_...`
   - Leave blank to use template responses

### Step 4: Deploy

1. **Click "Apply"** to create the service

2. **Render will**:
   - Build your Docker image (~5-10 minutes first time)
   - Deploy to a server
   - Start your bot
   - Assign a URL (e.g., `empire-v13.onrender.com`)

3. **Monitor the build logs** in the Render dashboard

4. **Look for the success message**:
   ```
   EMPIRE v13 — EXPANDED BUILD — ONLINE
   ```

5. **Check Telegram** - You should receive the online notification!

---

## Post-Deployment Setup

### Configure Your Bot via Telegram

Once deployed, use Telegram to configure everything:

1. **/start** - Open the main menu

2. **Add Facebook Groups**:
   ```
   /add_group
   ```
   Paste group URLs one by one

3. **Add Facebook Accounts**:
   ```
   /add_fb_account
   ```
   Choose cookie-based authentication (recommended)

4. **Add WhatsApp Numbers**:
   ```
   /add_wa_number
   ```
   Enter session name, then scan QR code from your phone

5. **Upload Inventory**:
   - Go to Database menu
   - Upload CSV with columns: `part,price,stock,vehicle,year`

---

## Managing Your Deployment

### Viewing Logs

1. Go to your service in Render dashboard
2. Click "Logs" tab
3. See real-time output from your bot

### Restarting

1. Go to service settings
2. Click "Manual Deploy" → "Deploy latest commit"
3. Or just push to GitHub (auto-deploys)

### Updating Code

```bash
# Make changes locally
git add .
git commit -m "Update: describe your changes"
git push

# Render auto-deploys within 1-2 minutes!
```

### Checking Status

1. **Render Dashboard**: See service status (green = running)
2. **Telegram**: Send `/start` to your bot
3. **Logs**: Check for any errors

---

## Persistent Storage

Your Render deployment includes **1GB persistent disk** mounted at `/app/sessions`:

- **WhatsApp sessions**: Saved between restarts
- **Facebook sessions**: Preserved
- **Database**: Persists automatically

**Note**: Your `groups.json`, `accounts.json`, and `wa_numbers.json` are in your code, so they're always available!

---

## Free Tier Limits

Render Free Tier includes:

- ✅ 750 hours/month runtime (enough for 24/7!)
- ✅ 512MB RAM (sufficient for this bot)
- ✅ Automatic sleep after 15 min inactivity
- ✅ 1GB persistent disk
- ⏸️ Service **sleeps** after 15 minutes of no web requests

**Important**: Your bot is a background service, not a web server. To keep it always running:

**Option 1**: Upgrade to Starter plan ($7/month) for 24/7 uptime  
**Option 2**: Use a cron job to ping your service every 10 minutes (prevents sleep)

###Option 2 Implementation:

Use a free cron service like [cron-job.org](https://cron-job.org):

1. Sign up at cron-job.org
2. Create a new cron job
3. Set URL to: `https://your-service.onrender.com`
4. Set interval: Every 10 minutes
5. Enable it!

This keeps your bot awake 24/7 on the free tier.

---

## Upgrading to Paid (Optional)

For production use with high volume:

### Starter Plan ($7/month)
- ✅ Always on (no sleep)
- ✅ 512MB RAM
- ✅ 1GB disk
- ✅ Custom domains
- ✅ Priority support

### Pro Plan ($25/month)
- ✅ All Starter features
- ✅ 2GB RAM
- ✅ 10GB disk
- ✅ Auto-scaling
- ✅ Enhanced security

**Recommendation**: Start with Free + cron ping, upgrade to Starter when you're making sales!

---

## Environment Variables Management

### Viewing Current Values

1. Go to your service in Render
2. Click "Environment" tab
3. See all configured variables

### Adding New Variables

1. Click "Add Environment Variable"
2. Enter key and value
3. Click "Save Changes"
4. Service auto-redeploys

### Updating Values

1. Click "Edit" next to the variable
2. Update the value
3. Click "Save Changes"
4. Service restarts with new value

---

## Troubleshooting

### "Service keeps restarting"

**Check logs** in Render dashboard. Common issues:

1. **Invalid BOT_TOKEN or OWNER_ID**
   - Update in Environment tab
   - Make sure OWNER_ID is just the number (no "Id:" prefix)

2. **Missing dependencies**
   - Check Dockerfile includes all packages
   - Rebuild service

3. **Port binding issues**
   - Our bot doesn't need a web server
   - Render expects port binding (we handle this)

### "Bot not responding in Telegram"

1. **Check service status** in Render (should be green "Running")
2. **Check logs** for errors
3. **Verify BOT_TOKEN** is correct
4. **Restart service** (Manual Deploy → Deploy latest)

### "QR code not appearing"

1. Check that WhatsApp service started:
   ```
   Look for: "✅ Baileys server started successfully"
   ```

2. If missing, check logs for Node.js errors

3. Verify `package.json` is committed to Git

### "Database not persisting"

1. Check that disk is mounted:
   - Go to service settings
   - Verify "Disk" section shows `/app/sessions` mount

2. Database file `empire.db` should be in your code (committed to Git)

---

## Security Best Practices

### Don't Commit Secrets

**Never commit `.env` to GitHub!**

The `.gitignore` already excludes it, but double-check:

```bash
cat .gitignore | grep .env
```

You should see `.env` listed.

### Use Render's Environment Variables

- Store all secrets in Render's Environment tab
- They're encrypted at rest
- Never exposed in logs

### Keep Repository Private

- Use GitHub private repository
- Don't expose your code publicly (contains config structure)

### Rotate API Keys Regularly

- Change Groq API key every 3-6 months
- Update in Render Environment tab

---

## Monitoring & Alerts

### Built-in Monitoring

Render provides:
- CPU usage graphs
- Memory usage graphs
- Request logs
- Error logs

### Telegram Notifications

Your bot sends you messages for:
- Startup confirmation
- Critical errors (if configured)
- Daily summaries (if enabled)

### Custom Alerts

Add to your bot code (optional):

```python
# In main.py, add error handler
async def error_handler(update, context):
    await app.bot.send_message(
        OWNER_ID,
        f"⚠️ ERROR: {context.error}"
    )

app.add_error_handler(error_handler)
```

---

## Scaling Considerations

### When to Upgrade

Upgrade from Free to Starter ($7/month) when:
- You have >100 leads/day
- You need guaranteed uptime
- You're making consistent sales

Upgrade to Pro ($25/month) when:
- You have >1000 leads/day
- You need more RAM for multiple WhatsApp numbers
- You want auto-scaling

### Horizontal Scaling

For very high volume:
- Deploy multiple instances
- Each handles different Facebook groups
- Centralize data in PostgreSQL (upgrade from SQLite)

---

## Backup & Recovery

### Automatic Backups

Render doesn't auto-backup the disk. **Backup yourself**:

1. **Database**:
   ```bash
   # Download empire.db from Render
   # Via service shell or SFTP
   ```

2. **Configuration**:
   - Already in your Git repository
   - Push changes regularly

3. **Sessions**:
   - WhatsApp sessions can be regenerated (scan QR again)
   - Facebook cookies can be re-exported

### Disaster Recovery

If service fails:

1. Redeploy from GitHub (all config preserved)
2. Re-scan WhatsApp QR codes
3. Database and inventory should persist

---

## Cost Optimization

### Stay on Free Tier

- Use cron-job.org ping (free)
- Optimize code to reduce CPU usage
- Clean up old logs

### Monitor Usage

Check Render dashboard monthly:
- RAM usage should stay <512MB
- CPU should be low
- Disk should be <1GB

---

## Next Steps

1. ✅ Bot deployed to Render
2. Configure via Telegram commands
3. Monitor performance in dashboard
4. Upgrade when making sales!

---

## Support Resources

- **Render Docs**: [render.com/docs](https://render.com/docs)
- **Render Community**: [community.render.com](https://community.render.com)
- **Project Docs**: Check `NAVIGATION.md` for bot commands

**Your EMPIRE v13 is now running 24/7 in the cloud! 🚀**
