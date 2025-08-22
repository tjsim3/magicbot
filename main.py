import os
import asyncio
import discord
from discord.ext import commands
from commands import setup_commands  # Changed from bot.commands
from events import setup_events      # Changed from bot.events
from models import create_app

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True  # Required for message content access
intents.guilds = True
intents.members = True  # Enable if you need member-related events

# Create bot instance
bot = commands.Bot(command_prefix='%', intents=intents)

async def main():
    """Main function to start the bot"""
    # Get bot token from environment variables (Railway environment variables)
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("ERROR: DISCORD_TOKEN not found in environment variables!")
        print("Please add your Discord bot token to Railway environment variables with key 'DISCORD_TOKEN'")
        return
    
    # Setup commands and events
    await setup_commands(bot)
    await setup_events(bot)
    
    try:
        # Start the bot
        print("Starting Discord bot...")
        await bot.start(token)
    except discord.LoginFailure:
        print("ERROR: Invalid Discord token! Please check your DISCORD_TOKEN in Railway environment variables.")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Initialize database
    # Initialize database (already handled in models.py)
    from models import init_database
    init_database()
    print("✅ Database initialized successfully!")
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except Exception as e:
        print(f"Bot crashed with error: {e}")
