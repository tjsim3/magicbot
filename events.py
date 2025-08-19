import discord
from discord.ext import commands
import datetime
import asyncio
import os

# Import global variables from commands module
signup_message_id = None
signups = set()

async def setup_events(bot):
    """Setup all bot events"""
    global signup_message_id, signups
    
    @bot.event
    async def on_ready():
        """Event triggered when bot is ready"""
        print(f"\n🤖 Bot is ready!")
        print(f"Logged in as: {bot.user.name} (ID: {bot.user.id})")
        print(f"Connected to {len(bot.guilds)} guild(s)")
        print(f"Serving {len(set(bot.get_all_members()))} unique users")
        print(f"Bot latency: {round(bot.latency * 1000)}ms")
        print(f"discord.py version: {discord.__version__}")
        print("-" * 50)
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} servers | !helpme"
        )
        await bot.change_presence(activity=activity, status=discord.Status.online)
        
        # Start monthly scheduler
        if hasattr(bot, 'monthly_scheduler') and not bot.monthly_scheduler.is_running():
            bot.monthly_scheduler.start()
            print("✅ Monthly scheduler started!")
    
    @bot.event
    async def on_raw_reaction_add(payload):
        """Handle reaction additions for signup system"""
        # Import here to avoid circular imports
        from bot.commands import signup_message_id as cmd_signup_id, signups as cmd_signups
        
        if payload.message_id == cmd_signup_id and payload.user_id != bot.user.id:
            if payload.member and not payload.member.bot:
                # Check if user has valid roles
                valid_roles = ['wizard', 'apprentice', 'sage']
                user_roles = [role.name.lower() for role in payload.member.roles]
                
                if any(role in user_roles for role in valid_roles):
                    cmd_signups.add(payload.user_id)
                    print(f"✅ {payload.member.display_name} signed up for training matches")
                else:
                    # Try to send DM explaining role requirement
                    try:
                        user = bot.get_user(payload.user_id)
                        if user:
                            await user.send("⚠️ You need a Wizard, Apprentice, or Sage role to sign up for training matches.")
                    except discord.Forbidden:
                        pass  # Can't send DM, that's fine
    
    @bot.event
    async def on_raw_reaction_remove(payload):
        """Handle reaction removals for signup system"""
        from bot.commands import signup_message_id as cmd_signup_id, signups as cmd_signups
        
        if payload.message_id == cmd_signup_id and payload.user_id != bot.user.id:
            cmd_signups.discard(payload.user_id)
            user = bot.get_user(payload.user_id)
            if user:
                print(f"❌ {user.display_name} removed their signup")
    
    @bot.event
    async def on_guild_join(guild):
        """Event triggered when bot joins a new guild"""
        print(f"✅ Joined new guild: {guild.name} (ID: {guild.id})")
        print(f"Guild has {guild.member_count} members")
        
        # Update bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} servers | !help"
        )
        await bot.change_presence(activity=activity)
        
        # Try to send a welcome message to the system channel
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title="👋 Hello!",
                description=(
                    "Thanks for adding me to your server!\n\n"
                    "🔧 Use `!help` to see all available commands\n"
                    "🏓 Try `!ping` to test if I'm working\n"
                    "📊 Use `!info` to see bot statistics\n\n"
                    "If you need help, feel free to ask!"
                ),
                color=discord.Color.green()
            )
            try:
                await guild.system_channel.send(embed=embed)
            except discord.Forbidden:
                print(f"⚠️ Cannot send welcome message to {guild.name} - insufficient permissions")
    
    @bot.event
    async def on_guild_remove(guild):
        """Event triggered when bot leaves a guild"""
        print(f"❌ Left guild: {guild.name} (ID: {guild.id})")
        
        # Update bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} servers | !help"
        )
        await bot.change_presence(activity=activity)
    
    @bot.event
    async def on_member_join(member):
        """Event triggered when a new member joins a guild"""
        print(f"👤 New member joined {member.guild.name}: {member.name}")
        
        # You can add welcome message logic here
        # Example: Send a DM or message to a welcome channel
    
    @bot.event
    async def on_member_remove(member):
        """Event triggered when a member leaves a guild"""
        print(f"👤 Member left {member.guild.name}: {member.name}")
    
    @bot.event
    async def on_message(message):
        """Event triggered for every message"""
        # Ignore messages from bots
        if message.author.bot:
            return
        
        # Process commands
        await bot.process_commands(message)
        
        # You can add custom message handling here
        # Example: Auto-responses, keyword detection, etc.
    
    @bot.event
    async def on_disconnect():
        """Event triggered when bot disconnects"""
        print("⚠️ Bot disconnected from Discord")
    
    @bot.event
    async def on_resumed():
        """Event triggered when bot resumes connection"""
        print("🔄 Bot connection resumed")
    
    @bot.event
    async def on_error(event, *args, **kwargs):
        """Global error handler"""
        print(f"❌ Error in event {event}: {args}")
    
    # Scheduled tasks setup
    async def setup_scheduled_tasks():
        """Start scheduled tasks when bot is ready"""
        if not hasattr(bot, '_scheduled_tasks_started'):
            bot._scheduled_tasks_started = True
            bot.loop.create_task(status_updater())
    
    async def status_updater():
        """Update bot status periodically"""
        await bot.wait_until_ready()
        
        statuses = [
            ("watching", f"{len(bot.guilds)} servers"),
            ("listening", "!help for commands"),
            ("playing", "with Discord API"),
        ]
        
        while not bot.is_closed():
            for activity_type, name in statuses:
                if bot.is_closed():
                    break
                
                activity_types = {
                    "playing": discord.ActivityType.playing,
                    "watching": discord.ActivityType.watching,
                    "listening": discord.ActivityType.listening
                }
                
                activity = discord.Activity(
                    type=activity_types[activity_type],
                    name=name
                )
                
                try:
                    await bot.change_presence(activity=activity)
                    await asyncio.sleep(300)  # Change status every 5 minutes
                except Exception as e:
                    print(f"Error updating status: {e}")
                    await asyncio.sleep(60)
    
    print("✅ Events loaded successfully!")
