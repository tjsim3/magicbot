import os
import asyncio
import discord
from discord.ext import commands
from keep_alive import keep_alive
from bot.commands import setup_commands
from bot.events import setup_events
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
    # Get bot token from environment variables (Replit secrets)
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("ERROR: DISCORD_TOKEN not found in environment variables!")
        print("Please add your Discord bot token to Replit secrets with key 'DISCORD_TOKEN'")
        return
    
    # Setup commands and events
    await setup_commands(bot)
    await setup_events(bot)
    
    try:
        # Start the bot
        print("Starting Discord bot...")
        await bot.start(token)
    except discord.LoginFailure:
        print("ERROR: Invalid Discord token! Please check your DISCORD_TOKEN in Replit secrets.")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Initialize database
    app = create_app()
    print("✅ Database initialized successfully!")
    
    # Start the keep-alive server for 24/7 operation
    keep_alive()
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except Exception as e:
        print(f"Bot crashed with error: {e}")
