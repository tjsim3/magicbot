# Discord Bot for Replit

A Discord bot designed to run 24/7 on Replit with secure token management and reliable uptime.

## 🚀 Features

- **24/7 Operation**: Includes keep-alive mechanism for continuous operation on Replit
- **Secure Token Management**: Uses Replit's secrets for secure token storage
- **Command System**: Extensible command system with error handling
- **Event Handling**: Comprehensive event handling for Discord interactions
- **Status Updates**: Automatic status updates and presence management
- **Modular Design**: Clean, organized code structure for easy maintenance

## 📋 Available Commands

### Training Match System
- `!testsignup` - Post the training signup message
- `!testmatches` - Assign matches from current signups

### Reminder System  
- `!remindme <minutes> <message>` - Set a reminder after X minutes
- `!remindat <YYYY-MM-DD> <HH:MM> <message>` - Set reminder for specific UTC date/time

### General Commands
- `!helpme` - Show all available commands
- `!ping` - Check bot latency and responsiveness
- `!info` - Display bot information and statistics
- `!server` - Show current server information

## 🔧 Setup Instructions

### 1. Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section and click "Add Bot"
4. Copy the bot token (you'll need this for step 3)
5. Enable "Message Content Intent" in the bot settings
6. Go to "OAuth2 > URL Generator"
7. Select "bot" scope and required permissions
8. Use the generated URL to invite the bot to your server

### 2. Import to Replit

1. Create a new Python Repl on Replit
2. Upload or paste all the files from this project
3. Make sure the directory structure matches exactly

### 3. Configure Secrets

1. In your Replit project, click on "Secrets" (lock icon) in the sidebar
2. Add a new secret with:
   - Key: `DISCORD_TOKEN`
   - Value: Your Discord bot token from step 1

### 4. Install Dependencies

Replit will automatically detect and install the required packages when you run the bot. The main dependencies are:

- `discord.py` - Discord API wrapper
- `flask` - For the keep-alive web server

### 5. Run the Bot

1. Click the "Run" button in Replit
2. The bot should start and display connection information
3. You should see "Bot is ready!" in the console
4. The keep-alive server will be accessible at your Repl's URL

### 6. Enable Always-On (Optional)

For true 24/7 operation, consider upgrading to Replit's Always-On feature, or use external monitoring services to ping your bot's keep-alive URL.

## 🛠️ Customization

### Adding New Commands

1. Open `bot/commands.py`
2. Add your command function following the existing pattern:

```python
@bot.command(name='mycommand')
async def my_command(ctx):
    """Description of your command"""
    await ctx.send("Hello, World!")
