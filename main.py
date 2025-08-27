import os
import asyncio
import discord
from discord.ext import commands
from models import create_app

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='%', intents=intents)

from commands import setup_commands
from events import setup_events

async def main():
    """Main function to start the bot"""
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("ERROR: DISCORD_TOKEN not found!")
        return
    
    # Setup commands and events
    await setup_commands(bot)
    await setup_events(bot)
    
    try:
        print("Starting Discord bot...")
        await bot.start(token)
    except discord.LoginFailure:
        print("ERROR: Invalid Discord token!")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    from models import init_database
    init_database()
    print("✅ Database initialized successfully!")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except Exception as e:
        print(f"Bot crashed with error: {e}")
