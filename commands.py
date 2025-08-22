import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
import asyncio
import random
import os
import time

# Global variables for signup system
signup_message_id = None
signups = set()

# Helper functions to replace utils imports
def format_uptime(seconds):
    """Format uptime seconds into human readable string"""
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"

def get_server_info():
    """Simple server info placeholder"""
    return "Server information"

# Import new HP-based duel system
from models import db_session, ActiveDuel, DuelPlayer, get_or_create_player, cleanup_expired_duels, get_player_stats

# Create duel embed function (since it was in utils)
def create_duel_embed(title, description, color):
    """Create a standardized duel embed"""
    import discord
    return discord.Embed(
        title=title,
        description=description,
        color=color
    )

async def setup_commands(bot):
    """Setup all bot commands"""
    global signup_message_id, signups
    
    # Get configuration from environment variables
    GUILD_ID = int(os.getenv('GUILD_ID', 0))  # You'll need to add this to secrets
    CHANNEL_ID = int(os.getenv('CHANNEL_ID', 0))  # You'll need to add this to secrets
    
    # ---------------- SIGNUP LOGIC ----------------
    async def post_signup_message():
        global signup_message_id
        if CHANNEL_ID == 0:
            print("⚠️ CHANNEL_ID not configured")
            return
            
        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            print(f"⚠️ Channel {CHANNEL_ID} not found")
            return
            
        msg = await channel.send(
            "@spellkeeper, react here with 🐼 to sign up for this month's training matches"
        )
        signup_message_id = msg.id
        await msg.add_reaction("🐼")

    async def assign_matches():
        if GUILD_ID == 0:
            print("⚠️ GUILD_ID not configured")
            return
            
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            print(f"⚠️ Guild {GUILD_ID} not found")
            return
            
        wizards, apprentices, sages = [], [], []

        for member_id in signups:
            member = guild.get_member(member_id)
            if member:
                roles = [r.name.lower() for r in member.roles]
                if "wizard" in roles:
                    wizards.append(member)
                elif "apprentice" in roles:
                    apprentices.append(member)
                elif "sage" in roles:
                    sages.append(member)

        random.shuffle(wizards)
        random.shuffle(apprentices)
        random.shuffle(sages)

        matches = []

        # Wizard + Apprentice + Sage observer
        while wizards and apprentices and sages:
            matches.append((wizards.pop(), apprentices.pop(), sages.pop()))

        # Wizard + Sage
        while wizards and sages:
            matches.append((wizards.pop(), sages.pop()))

        # Sage + Apprentice
        while sages and apprentices:
            matches.append((sages.pop(), apprentices.pop()))

        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            print(f"⚠️ Channel {CHANNEL_ID} not found for match assignments")
            return
            
        if matches:
            await channel.send("### Match Assignments:")
            for i, match in enumerate(matches, 1):
                mention_list = " + ".join([m.mention for m in match])
                roles = [f"({len([r for r in member.roles if r.name.lower() in ['wizard', 'apprentice', 'sage']])}{[r.name.title() for r in member.roles if r.name.lower() in ['wizard', 'apprentice', 'sage']][0] if [r for r in member.roles if r.name.lower() in ['wizard', 'apprentice', 'sage']] else 'Unknown'})" for member in match]
                await channel.send(f"**Match {i}:** {mention_list}")
            
            await channel.send(f"\n✅ **{len(matches)} matches created** from {len(signups)} signups!")
        else:
            await channel.send("Not enough players to form matches. Need at least 2 people with appropriate roles (Wizard, Apprentice, or Sage).")
    
    # ---------------- REMINDER COMMANDS ----------------
    @bot.command()
    async def remindme(ctx, time_in_minutes: int, *, reminder_message: str):
        """Set a reminder in minutes. Usage: !remindme 10 Do the dishes"""
        if time_in_minutes <= 0:
            return await ctx.send("❌ Time must be greater than 0 minutes.")
        if time_in_minutes > 10080:  # 7 days limit
            return await ctx.send("❌ Reminders cannot be set for more than 7 days (10,080 minutes).")
        
        await ctx.send(f"⏰ Okay {ctx.author.mention}, I will remind you in {time_in_minutes} minute(s).")
        
        # Use create_task to prevent blocking
        async def send_reminder():
            await asyncio.sleep(time_in_minutes * 60)
            try:
                await ctx.author.send(f"🔔 Reminder: {reminder_message}")
                print(f"✅ Reminder sent to {ctx.author.name}: {reminder_message}")
            except discord.Forbidden:
                try:
                    await ctx.send(f"{ctx.author.mention}, I couldn't DM you. Reminder: {reminder_message}")
                except discord.HTTPException:
                    print(f"⚠️ Failed to send reminder to {ctx.author.name}")
        
        bot.loop.create_task(send_reminder())

    @bot.command()
    async def remindat(ctx, date_str: str, time_str: str, *, reminder_message: str):
        """
        Set a reminder at a specific UTC date/time.
        Usage: !remindat YYYY-MM-DD HH:MM Message
        Example: !remindat 2025-08-15 14:30 Meeting with team
        """
        try:
            target_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            target_dt = target_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return await ctx.send("❌ Invalid date/time format. Use YYYY-MM-DD HH:MM (UTC).")

        now_utc = datetime.now(timezone.utc)
        delay = (target_dt - now_utc).total_seconds()
        if delay <= 0:
            return await ctx.send("❌ The specified time is in the past.")
        if delay > 604800:  # 7 days limit
            return await ctx.send("❌ Reminders cannot be set more than 7 days in the future.")

        await ctx.send(f"⏰ Okay {ctx.author.mention}, I will remind you at {target_dt} UTC.")
        
        # Use create_task to prevent blocking
        async def send_scheduled_reminder():
            await asyncio.sleep(delay)
            try:
                await ctx.author.send(f"🔔 Scheduled reminder: {reminder_message}")
                print(f"✅ Scheduled reminder sent to {ctx.author.name}: {reminder_message}")
            except discord.Forbidden:
                try:
                    await ctx.send(f"{ctx.author.mention}, I couldn't DM you. Scheduled reminder: {reminder_message}")
                except discord.HTTPException:
                    print(f"⚠️ Failed to send scheduled reminder to {ctx.author.name}")
        
        bot.loop.create_task(send_scheduled_reminder())

    # ---------------- HIGH MAGE ADMIN COMMANDS ----------------
    def is_high_mage():
        """Check if user has High Mage role"""
        async def predicate(ctx):
            if not ctx.guild:
                await ctx.send("❌ This command can only be used in a server!")
                return False
            user_roles = [role.name.lower() for role in ctx.author.roles]
            if 'high mage' not in user_roles:
                await ctx.send("❌ Only High Mages can use this command!")
                return False
            return True
        return commands.check(predicate)
    
    @bot.command()
    @is_high_mage()
    async def testsignup(ctx):
        """Force post signup message now. (High Mage only)"""
        await post_signup_message()
        await ctx.send("✅ Test signup message posted.")

    @bot.command()
    @is_high_mage()
    async def testmatches(ctx):
        """Force assign matches now. (High Mage only)"""
        await assign_matches()
        await ctx.send("✅ Test matches assigned.")
    
    @bot.command()
    @is_high_mage()
    async def clearsignups(ctx):
        """Clear all current signups. (High Mage only)"""
        global signups
        signups.clear()
        await ctx.send(f"✅ Cleared all signups. Current count: {len(signups)}")
    
    @bot.command()
    @is_high_mage()
    async def setprefix(ctx, new_prefix: str):
        """Change the bot's command prefix. (High Mage only)"""
        if len(new_prefix) > 3:
            await ctx.send("❌ Prefix must be 3 characters or less!")
            return
        
        bot.command_prefix = new_prefix
        await ctx.send(f"✅ Command prefix changed to `{new_prefix}`")
        await ctx.send(f"💡 Note: This change is temporary. To make it permanent, update the code.")
    
    @bot.command()
    @is_high_mage()
    async def serverstats(ctx):
        """Show detailed server statistics. (High Mage only)"""
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server!")
            return
        
        guild = ctx.guild
        
        # Count members by status
        online = len([m for m in guild.members if m.status == discord.Status.online])
        idle = len([m for m in guild.members if m.status == discord.Status.idle])
        dnd = len([m for m in guild.members if m.status == discord.Status.dnd])
        offline = len([m for m in guild.members if m.status == discord.Status.offline])
        
        # Count bots vs humans
        bots = len([m for m in guild.members if m.bot])
        humans = guild.member_count - bots
        
        embed = discord.Embed(
            title=f"📊 Detailed Stats for {guild.name}",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="👥 Total Members", value=f"{guild.member_count}", inline=True)
        embed.add_field(name="🤖 Bots", value=f"{bots}", inline=True)
        embed.add_field(name="👤 Humans", value=f"{humans}", inline=True)
        
        embed.add_field(name="🟢 Online", value=f"{online}", inline=True)
        embed.add_field(name="🟡 Idle", value=f"{idle}", inline=True)
        embed.add_field(name="🔴 DND", value=f"{dnd}", inline=True)
        
        embed.add_field(name="📝 Text Channels", value=f"{len(guild.text_channels)}", inline=True)
        embed.add_field(name="🔊 Voice Channels", value=f"{len(guild.voice_channels)}", inline=True)
        embed.add_field(name="📁 Categories", value=f"{len(guild.categories)}", inline=True)
        
        embed.add_field(name="🎭 Total Roles", value=f"{len(guild.roles)}", inline=True)
        embed.add_field(name="😀 Emojis", value=f"{len(guild.emojis)}", inline=True)
        embed.add_field(name="🚀 Boost Level", value=f"{guild.premium_tier}", inline=True)
        
        # Role breakdown
        role_counts = {}
        for member in guild.members:
            for role in member.roles:
                if role.name != "@everyone":
                    role_counts[role.name] = role_counts.get(role.name, 0) + 1
        
        if role_counts:
            top_roles = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            role_text = "\n".join([f"{role}: {count}" for role, count in top_roles])
            embed.add_field(name="🏆 Top 5 Roles", value=role_text, inline=False)
        
        embed.set_footer(text=f"Server created: {guild.created_at.strftime('%B %d, %Y')}")
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        await ctx.send(embed=embed)
    
    @bot.command()
    async def signupcount(ctx):
        """Show current signup count."""
        await ctx.send(f"📊 Current signups: **{len(signups)}** players")

    # ---------------- HELP COMMAND ----------------
    @bot.command(name="helpme")
    async def helpme(ctx):
        """Show bot commands and usage"""
        embed = discord.Embed(
            title="📜 Bot Commands",
            description="Here are all available commands:",
            color=discord.Color.blue()
        )
        
        # Training commands
        embed.add_field(
            name="🗡️ Training Match System",
            value=(
                "`%signupcount` - Show current signup count\n"
                "`%testsignup` - Post signup message (High Mage only)\n"
                "`%testmatches` - Assign matches (High Mage only)\n"
                "`%clearsignups` - Clear all signups (High Mage only)"
            ),
            inline=False
        )
        
        # High Mage admin commands
        user_roles = [role.name.lower() for role in ctx.author.roles] if ctx.guild else []
        if 'high mage' in user_roles:
            embed.add_field(
                name="⚔️ High Mage Commands",
                value=(
                    "`%setprefix <prefix>` - Change command prefix\n"
                    "`%serverstats` - Detailed server statistics"
                ),
                inline=False
            )
        
        # Reminder commands  
        embed.add_field(
            name="⏰ Reminder System",
            value=(
                "`%remindme <minutes> <message>` - Set reminder (max 7 days)\n"
                "`%remindat <YYYY-MM-DD> <HH:MM> <message>` - Schedule reminder (UTC)"
            ),
            inline=False
        )
        
        # General commands
        embed.add_field(
            name="🤖 General Commands",
            value=(
                "`%ping` - Check bot latency\n"
                "`%info` - Show bot information\n"
                "`%server` - Show server information\n"
                "`%helpme` - Show this help message"
            ),
            inline=False
        )
        
        # Fun commands
        embed.add_field(
            name="🎲 Fun Commands",
            value=(
                "`%roll [dice]` - Roll dice (e.g., %roll 2d6)\n"
                "`%flip` - Flip a coin\n"
                "`%8ball <question>` - Ask the magic 8-ball\n"
                "`%quote` - Get an inspirational quote\n"
                "`%choose <options>` - Choose between options"
            ),
            inline=False
        )
        
        # User commands
        embed.add_field(
            name="👤 User Commands",
            value=(
                "`%whois [@user]` - Show user information\n"
                "`%avatar [@user]` - Show user's avatar"
            ),
            inline=False
        )
        
        # Game commands
        embed.add_field(
            name="⚔️ HP-Based Spell Duels",
            value=(
                "`%duel @user` - Challenge someone to an HP duel (3 HP each)\n"
                "`%cast <spell>` - Cast a spell on your turn (12h limit)\n"
                "`%duels` - Show active duels with HP and turn info\n"
                "`%cancelduels` - Cancel your active duels\n"
                "`%duelstats [@user]` - View duel statistics\n"
                "`%spells` - View all spells and strategy guide"
            ),
            inline=False
        )
        
        embed.set_footer(text="Training signups happen automatically on the first Monday of each month!")
        await ctx.send(embed=embed)
    
    # ---------------- BASIC COMMANDS ----------------
    @bot.command(name='ping')
    async def ping(ctx):
        """Check bot latency"""
        latency = round(bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency: **{latency}ms**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @bot.command(name='info')
    async def bot_info(ctx):
        """Display bot information"""
        embed = discord.Embed(
            title="🤖 Bot Information",
            color=discord.Color.blue()
        )
        
        # Bot stats
        guild_count = len(bot.guilds)
        user_count = len(set(bot.get_all_members()))
        
        embed.add_field(name="Servers", value=guild_count, inline=True)
        embed.add_field(name="Users", value=user_count, inline=True)
        
        # Uptime calculation
        if hasattr(bot, 'start_time'):
            uptime_seconds = time.time() - bot.start_time
            embed.add_field(name="Uptime", value=format_uptime(uptime_seconds), inline=True)
        else:
            embed.add_field(name="Uptime", value="Not available", inline=True)
        
        embed.set_footer(text=f"Running on Railway | discord.py {discord.__version__}")
        embed.timestamp = datetime.utcnow()
        
        await ctx.send(embed=embed)
    
    @bot.command(name='server')
    async def server_info(ctx):
        """Display server information"""
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server!")
            return
        
        guild = ctx.guild
        embed = discord.Embed(
            title=f"📊 {guild.name} Information",
            color=discord.Color.purple()
        )
        
        # Server stats
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Created", value=guild.created_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="Text Channels", value=f"{len(guild.text_channels)}", inline=True)
        embed.add_field(name="Voice Channels", value=f"{len(guild.voice_channels)}", inline=True)
        embed.add_field(name="Roles", value=f"{len(guild.roles)}", inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        await ctx.send(embed=embed)
    
    # ---------------- FUN COMMANDS ----------------
    @bot.command(name='roll')
    async def roll_dice(ctx, dice: str = "1d20"):
        """Roll dice! Format: !roll 2d6 or !roll 1d20"""
        try:
            # Parse dice format (e.g., "2d6" means 2 six-sided dice)
            if 'd' not in dice.lower():
                await ctx.send("❌ Invalid format! Use format like `1d20` or `2d6`")
                return
            
            count, sides = dice.lower().split('d')
            count = int(count) if count else 1
            sides = int(sides)
            
            if count > 20 or sides > 1000:
                await ctx.send("❌ That's too many dice or sides! Keep it reasonable.")
                return
            
            if count <= 0 or sides <= 0:
                await ctx.send("❌ Dice count and sides must be positive numbers!")
                return
            
            import random
            rolls = [random.randint(1, sides) for _ in range(count)]
            total = sum(rolls)
            
            embed = discord.Embed(
                title="🎲 Dice Roll Results",
                color=discord.Color.gold()
            )
            
            if len(rolls) == 1:
                embed.description = f"You rolled a **{total}** on a {sides}-sided die!"
            else:
                roll_details = " + ".join(map(str, rolls))
                embed.description = f"**{count}d{sides}**: {roll_details} = **{total}**"
            
            await ctx.send(embed=embed)
            
        except ValueError:
            await ctx.send("❌ Invalid dice format! Use format like `1d20` or `2d6`")
        except Exception as e:
            await ctx.send(f"❌ Error rolling dice: {str(e)}")
    
    @bot.command(name='flip')
    async def flip_coin(ctx):
        """Flip a coin"""
        import random
        result = random.choice(["Heads", "Tails"])
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"The coin landed on: **{result}**!",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)
    
    @bot.command(name='8ball')
    async def magic_8ball(ctx, *, question: str = None):
        """Ask the magic 8-ball a question"""
        if not question:
            await ctx.send("❌ You need to ask a question! Try `%8ball Will I win the next match?`")
            return
        
        import random
        responses = [
            "It is certain", "Without a doubt", "Yes definitely", "You may rely on it",
            "As I see it, yes", "Most likely", "Outlook good", "Yes", "Signs point to yes",
            "Reply hazy, try again", "Ask again later", "Better not tell you now",
            "Cannot predict now", "Concentrate and ask again",
            "Don't count on it", "My reply is no", "My sources say no",
            "Outlook not so good", "Very doubtful"
        ]
        
        answer = random.choice(responses)
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            description=f"**Question:** {question}\n**Answer:** {answer}",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)
    
    @bot.command(name='quote')
    async def inspirational_quote(ctx):
        """Get an inspirational quote"""
        import random
        quotes = [
            ("The only way to do great work is to love what you do.", "Steve Jobs"),
            ("Magic is believing in yourself. If you can do that, you can make anything happen.", "Johann Wolfgang von Goethe"),
            ("The real magic happens when you start believing in yourself.", "Unknown"),
            ("Training is everything. The peach was once a bitter almond; cauliflower is nothing but cabbage with a college education.", "Mark Twain"),
            ("Excellence is never an accident. It is always the result of high intention, sincere effort, and skillful execution.", "Aristotle"),
            ("The expert in anything was once a beginner.", "Helen Hayes"),
            ("Practice makes progress, not perfection.", "Unknown"),
            ("A wizard is never late, nor is he early. He arrives precisely when he means to.", "Gandalf"),
            ("It does not do to dwell on dreams and forget to live.", "Albus Dumbledore")
        ]
        
        quote, author = random.choice(quotes)
        embed = discord.Embed(
            title="✨ Daily Inspiration",
            description=f'"{quote}"\n\n— *{author}*',
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    
    @bot.command(name='choose')
    async def choose_option(ctx, *, choices: str):
        """Choose between options separated by commas or 'or'"""
        if not choices:
            await ctx.send("❌ Please provide options to choose from! Example: `%choose pizza, burgers, tacos`")
            return
        
        # Split by comma first, then by 'or' if no commas
        if ',' in choices:
            options = [choice.strip() for choice in choices.split(',')]
        elif ' or ' in choices:
            options = [choice.strip() for choice in choices.split(' or ')]
        else:
            await ctx.send("❌ Please separate options with commas or 'or'. Example: `%choose pizza, burgers` or `%choose this or that`")
            return
        
        if len(options) < 2:
            await ctx.send("❌ I need at least 2 options to choose from!")
            return
        
        import random
        choice = random.choice(options)
        embed = discord.Embed(
            title="🤔 Decision Made!",
            description=f"I choose: **{choice}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Options were:", value=", ".join(options), inline=False)
        await ctx.send(embed=embed)
    
    @bot.command(name='whois')
    async def user_info(ctx, member: discord.Member = None):
        """Show information about a user"""
        if member is None:
            member = ctx.author
        
        embed = discord.Embed(
            title=f"👤 User Info: {member.display_name}",
            color=member.color if member.color != discord.Color.default() else discord.Color.blue()
        )
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        
        # Basic info
        embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name="Nickname", value=member.nick or "None", inline=True)
        embed.add_field(name="User ID", value=member.id, inline=True)
        
        # Dates
        embed.add_field(name="Account Created", value=member.created_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%B %d, %Y") if member.joined_at else "Unknown", inline=True)
        
        # Roles (excluding @everyone)
        roles = [role.name for role in member.roles if role.name != "@everyone"]
        if roles:
            embed.add_field(name="Roles", value=", ".join(roles), inline=False)
        
        # Status
        status_emoji = {
            "online": "🟢",
            "idle": "🟡", 
            "dnd": "🔴",
            "offline": "⚫"
        }
        embed.add_field(name="Status", value=f"{status_emoji.get(str(member.status), '❓')} {str(member.status).title()}", inline=True)
        
        await ctx.send(embed=embed)
    
    @bot.command(name='avatar')
    async def show_avatar(ctx, member: discord.Member = None):
        """Show a user's avatar"""
        if member is None:
            member = ctx.author
        
        embed = discord.Embed(
            title=f"🖼️ {member.display_name}'s Avatar",
            color=member.color if member.color != discord.Color.default() else discord.Color.blue()
        )
        
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        embed.set_image(url=avatar_url)
        embed.add_field(name="Download", value=f"[Click here]({avatar_url})", inline=False)
        
        await ctx.send(embed=embed)
    
    # ---------------- SPELL DUEL GAME ----------------
    def process_combat_round(duel, challenger_spell, opponent_spell):
        """Process a combat round between two spells"""
        combat_log = []
        is_tie = False
        
        # Spell effectiveness chart
        spell_effects = {
            'fireball': {'beats': ['frostbolt', 'heal'], 'loses_to': ['shield', 'lightning']},
            'frostbolt': {'beats': ['lightning', 'magicmissile'], 'loses_to': ['fireball', 'heal']},
            'lightning': {'beats': ['fireball', 'shield'], 'loses_to': ['frostbolt', 'magicmissile']},
            'shield': {'beats': ['magicmissile', 'fireball'], 'loses_to': ['lightning', 'heal']},
            'heal': {'beats': ['shield', 'frostbolt'], 'loses_to': ['fireball', 'magicmissile']},
            'magicmissile': {'beats': ['heal', 'lightning'], 'loses_to': ['shield', 'frostbolt']}
        }
        
        # Determine winner
        if challenger_spell == opponent_spell:
            # Tie - no damage
            combat_log.append("✨ Spells clash! It's a tie - no damage dealt.")
            is_tie = True
        elif opponent_spell in spell_effects[challenger_spell]['beats']:
            # Challenger wins
            duel.opponent_hp -= 1
            combat_log.append(f"💥 {duel.challenger.username}'s {challenger_spell} hits {duel.opponent.username}!")
            combat_log.append(f"❤️ {duel.opponent.username} loses 1 HP!")
        else:
            # Opponent wins
            duel.challenger_hp -= 1
            combat_log.append(f"💥 {duel.opponent.username}'s {opponent_spell} hits {duel.challenger.username}!")
            combat_log.append(f"❤️ {duel.challenger.username} loses 1 HP!")
        
        # Reset spells for next round
        duel.challenger_spell = None
        duel.opponent_spell = None
        
        db_session.commit()
        return combat_log, is_tie
    
    def finish_duel(duel):
        """Finish a duel and record results"""
        now = datetime.now(timezone.utc)
        duration = now - duel.created_at
        duration_minutes = int(duration.total_seconds() / 60)
        
        # Determine winner
        if duel.challenger_hp <= 0 and duel.opponent_hp <= 0:
            # Draw
            duel.status = 'draw'
            duel.challenger.total_draws += 1
            duel.opponent.total_draws += 1
            winner = None
        elif duel.challenger_hp <= 0:
            # Opponent wins
            duel.status = 'completed'
            duel.winner_id = duel.opponent_id
            duel.challenger.total_losses += 1
            duel.opponent.total_wins += 1
            winner = duel.opponent
        else:
            # Challenger wins
            duel.status = 'completed'
            duel.winner_id = duel.challenger_id
            duel.challenger.total_wins += 1
            duel.opponent.total_losses += 1
            winner = duel.challenger
        
        # Update games played and last active
        duel.challenger.games_played += 1
        duel.opponent.games_played += 1
        duel.challenger.last_active = now
        duel.opponent.last_active = now
        
        db_session.commit()
        
        return {
            'winner': winner,
            'duration_minutes': duration_minutes
        }
    
    @bot.command(name='duel')
    async def spell_duel(ctx, opponent: discord.Member = None):
        """Challenge someone to a magical HP-based spell duel!"""
        if opponent is None:
            await ctx.send("❌ You need to mention someone to duel! Try `%duel @username`")
            return
        
        if opponent == ctx.author:
            await ctx.send("❌ You cannot duel yourself! Find a worthy opponent.")
            return
        
        if opponent.bot:
            await ctx.send("❌ You cannot duel bots! Challenge a real wizard.")
            return
        
        # Clean up expired duels
        cleanup_expired_duels()
        
        # Check if either player is already in an active duel
        existing_duel = db_session.query(ActiveDuel).filter(
            ((ActiveDuel.challenger_id == ctx.author.id) | (ActiveDuel.opponent_id == ctx.author.id) |
             (ActiveDuel.challenger_id == opponent.id) | (ActiveDuel.opponent_id == opponent.id)) &
            (ActiveDuel.status == 'active')
        ).first()
        
        if existing_duel:
            await ctx.send("⚔️ One of you is already in an active duel! Use `%duels` to see active duels.")
            return
        
        # Get or create players
        challenger_player = get_or_create_player(ctx.author.id, ctx.author.display_name)
        opponent_player = get_or_create_player(opponent.id, opponent.display_name)
        
        # Create new duel with HP system
        new_duel = ActiveDuel(
            challenger_id=challenger_player.id,
            opponent_id=opponent_player.id,
            challenger_hp=3,
            opponent_hp=3,
            current_turn='challenger',
            turn_deadline=datetime.now(timezone.utc) + timedelta(hours=12)
        )
        
        db_session.add(new_duel)
        db_session.commit()
        
        embed = create_duel_embed(
            "⚔️ Epic Spell Duel Begins!",
            f"{ctx.author.mention} has challenged {opponent.mention} to an HP-based magical duel!",
            discord.Color.red()
        )
        
        embed.add_field(
            name="🏠 HP System",
            value="**Each duelist starts with 3 HP**\nFirst to reduce opponent to 0 HP wins!",
            inline=False
        )
        
        embed.add_field(
            name="⏰ Turn System", 
            value=f"**{ctx.author.display_name}'s turn** (12 hours to cast)\nUse `%cast <spell>` to attack!",
            inline=False
        )
        
        embed.add_field(
            name="❤️ Current HP",
            value=f"**{ctx.author.display_name}:** 3 HP ❤️❤️❤️\n**{opponent.display_name}:** 3 HP ❤️❤️❤️",
            inline=False
        )
        
        embed.add_field(
            name="Available Spells:",
            value="🔥 Fireball • ❄️ Frostbolt • ⚡ Lightning • 🛡️ Shield • ✨ Heal • 💫 Magic Missile",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @bot.command(name='cast')
    async def cast_spell(ctx, *, spell_name: str = None):
        """Cast a spell in your active HP-based duel"""
        if spell_name is None:
            await ctx.send("❌ You need to specify a spell! Available: Fireball, Frostbolt, Lightning, Shield, Heal, Magic Missile")
            return
        
        # Clean up expired duels
        cleanup_expired_duels()
        
        # Find if user is in an active duel
        user_duel = db_session.query(ActiveDuel).filter(
            ((ActiveDuel.challenger_id == ctx.author.id) | (ActiveDuel.opponent_id == ctx.author.id)) &
            (ActiveDuel.status == 'active')
        ).first()
        
        if not user_duel:
            await ctx.send("❌ You're not in an active duel! Use `%duel @someone` to start one.")
            return
        
        # Check if it's the user's turn
        is_challenger = ctx.author.id == user_duel.challenger_id
        is_users_turn = (user_duel.current_turn == 'challenger' and is_challenger) or \
                       (user_duel.current_turn == 'opponent' and not is_challenger)
        
        if not is_users_turn:
            other_player = user_duel.challenger.username if not is_challenger else user_duel.opponent.username
            await ctx.send(f"❌ It's not your turn! Waiting for **{other_player}** to cast their spell.")
            return
        
        # Check for turn timeout
        if datetime.now(timezone.utc) > user_duel.turn_deadline:
            await ctx.send("⏰ Your turn has expired! The duel will be marked as expired.")
            return
        
        # Normalize spell name
        spell_name = spell_name.lower().strip().replace(' ', '')
        valid_spells = ['fireball', 'frostbolt', 'lightning', 'shield', 'heal', 'magicmissile']
        
        if spell_name not in valid_spells:
            await ctx.send(f"❌ Unknown spell! Valid spells: Fireball, Frostbolt, Lightning, Shield, Heal, Magic Missile")
            return
        
        # Record the spell for current player
        if is_challenger:
            user_duel.challenger_spell = spell_name
        else:
            user_duel.opponent_spell = spell_name
        
        # Update last action time
        user_duel.last_action = datetime.now(timezone.utc)
        
        # Check if both players have cast spells for this round
        if user_duel.challenger_spell and user_duel.opponent_spell:
            # Both spells cast - reveal and resolve combat
            await ctx.send(f"✨ {ctx.author.mention} casts their spell! Both players have cast - resolving combat...")
            await resolve_combat_round(ctx, user_duel)
        else:
            # First spell cast - hide the spell choice
            await ctx.send(f"✅ {ctx.author.display_name} has cast their spell!\n🔒 Spell choices will be revealed after both players cast.")
            
            # Switch turns and set new deadline
            user_duel.current_turn = 'opponent' if is_challenger else 'challenger'
            user_duel.turn_deadline = datetime.now(timezone.utc) + timedelta(hours=12)
            
            db.session.commit()
            
            # Notify next player
            next_player = user_duel.opponent if is_challenger else user_duel.challenger
            embed = create_duel_embed(
                "⏳ Turn Switch - Spell Hidden",
                f"**{next_player.username}**, it's your turn to cast a spell!",
                discord.Color.orange()
            )
            embed.add_field(
                name="❤️ Current HP",
                value=f"**{user_duel.challenger.username}:** {user_duel.challenger_hp} HP {'❤️' * user_duel.challenger_hp}{'💔' * (3 - user_duel.challenger_hp)}\n**{user_duel.opponent.username}:** {user_duel.opponent_hp} HP {'❤️' * user_duel.opponent_hp}{'💔' * (3 - user_duel.opponent_hp)}",
                inline=False
            )
            embed.add_field(
                name="🔒 Spell Secrecy",
                value="Your opponent has cast their spell, but it's hidden until you cast yours!",
                inline=False
            )
            embed.add_field(
                name="⏰ Time Limit",
                value="You have **12 hours** to cast your spell!",
                inline=False
            )
            
            await ctx.send(embed=embed)
    
    async def resolve_combat_round(ctx, duel):
        """Resolve a combat round between two spells"""
        challenger_spell = duel.challenger_spell
        opponent_spell = duel.opponent_spell
        
        # First reveal both spells before combat
        spell_emojis = {
            'fireball': '🔥', 'frostbolt': '❄️', 'lightning': '⚡',
            'shield': '🛡️', 'heal': '✨', 'magicmissile': '💫'
        }
        
        reveal_embed = create_duel_embed(
            "🔓 Spells Revealed!",
            "Both players have cast their spells:",
            discord.Color.blue()
        )
        
        reveal_embed.add_field(
            name=f"{spell_emojis.get(challenger_spell, '✨')} {duel.challenger.username}",
            value=f"**{challenger_spell.replace('magicmissile', 'Magic Missile').title()}**",
            inline=True
        )
        reveal_embed.add_field(
            name="VS",
            value="⚔️",
            inline=True
        )
        reveal_embed.add_field(
            name=f"{spell_emojis.get(opponent_spell, '✨')} {duel.opponent.username}",
            value=f"**{opponent_spell.replace('magicmissile', 'Magic Missile').title()}**",
            inline=True
        )
        
        await ctx.send(embed=reveal_embed)
        
        # Process combat using the utility function
        combat_log, is_tie = process_combat_round(duel, challenger_spell, opponent_spell)
        
        # Create combat result embed
        if is_tie:
            embed = create_duel_embed(
                "⚖️ Spells Clash - Tie Round!",
                "\n".join(combat_log),
                discord.Color.orange()
            )
        else:
            embed = create_duel_embed(
                "💥 Combat Round Results!",
                "\n".join(combat_log),
                discord.Color.gold()
            )
        
        # Show current HP
        embed.add_field(
            name="❤️ Current HP",
            value=f"**{duel.challenger.username}:** {duel.challenger_hp} HP {'❤️' * duel.challenger_hp}{'💔' * (3 - duel.challenger_hp)}\n**{duel.opponent.username}:** {duel.opponent_hp} HP {'❤️' * duel.opponent_hp}{'💔' * (3 - duel.opponent_hp)}",
            inline=False
        )
        
        # Check if duel is over (only if not a tie)
        if not is_tie and (duel.challenger_hp <= 0 or duel.opponent_hp <= 0):
            # Finish the duel
            result = finish_duel(duel)
            
            if result['winner']:
                embed.add_field(
                    name="🏆 Victory!",
                    value=f"**{result['winner'].username}** wins the duel!\n⏱️ Duration: {result['duration_minutes']} minutes",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🤝 Draw!",
                    value=f"Both duelists fell simultaneously!\n⏱️ Duration: {result['duration_minutes']} minutes",
                    inline=False
                )
        else:
            # Continue the duel
            if is_tie:
                # On tie, both players cast again immediately - keep current turn structure
                embed.add_field(
                    name="🔄 Tie Round - Cast Again!",
                    value=f"Both duelists must cast new spells!\n**{duel.challenger.username}** goes first, then **{duel.opponent.username}**",
                    inline=False
                )
            else:
                # Normal next round - challenger always goes first
                embed.add_field(
                    name="🔄 Next Round",
                    value=f"**{duel.challenger.username}** goes first! 12 hours to cast.",
                    inline=False
                )
            
            # Reset turn to challenger for next round
            duel.current_turn = 'challenger'
            duel.turn_deadline = datetime.now(timezone.utc) + timedelta(hours=12)
            db.session.commit()
        
        await ctx.send(embed=embed)
    
    @bot.command(name='duels')
    async def active_duels_list(ctx):
        """Show currently active HP-based duels with turn information"""
        # Clean up expired duels first
        cleanup_expired_duels()
        
        # Get active duels from database
        active_duels_db = ActiveDuel.query.filter_by(status='active').all()
        
        if not active_duels_db:
            await ctx.send("🕊️ No active duels right now. Challenge someone with `%duel @username`!")
            return
        
        embed = create_duel_embed(
            "⚔️ Active HP-Based Duels",
            f"There are currently {len(active_duels_db)} active duels with 3 HP each:",
            discord.Color.purple()
        )
        
        for duel in active_duels_db:
            # Calculate time remaining for current turn
            current_time = datetime.now(timezone.utc)
            time_remaining = duel.turn_deadline - current_time
            hours_remaining = max(0, int(time_remaining.total_seconds() / 3600))
            
            # Determine whose turn it is
            current_player = duel.challenger.username if duel.current_turn == 'challenger' else duel.opponent.username
            
            # HP display
            challenger_hp = "❤️" * duel.challenger_hp + "💔" * (3 - duel.challenger_hp)
            opponent_hp = "❤️" * duel.opponent_hp + "💔" * (3 - duel.opponent_hp)
            
            # Turn status
            if hours_remaining > 0:
                turn_info = f"**{current_player}'s turn** ({hours_remaining}h left)"
            else:
                turn_info = "⚠️ Turn expired"
            
            embed.add_field(
                name=f"{duel.challenger.username} vs {duel.opponent.username}",
                value=f"HP: {challenger_hp} vs {opponent_hp}\n{turn_info}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @bot.command(name='cancelduels')
    async def cancel_duel(ctx):
        """Cancel any active HP-based duels you're participating in"""
        # Clean up expired duels
        cleanup_expired_duels()
        
        # Find user's active duels
        user_duels = ActiveDuel.query.filter(
            ((ActiveDuel.challenger_id == ctx.author.id) | (ActiveDuel.opponent_id == ctx.author.id)) &
            (ActiveDuel.status == 'active')
        ).all()
        
        if not user_duels:
            await ctx.send("❌ You're not currently in any active duels.")
            return
        
        cancelled_count = 0
        for duel in user_duels:
            duel.status = 'cancelled'
            cancelled_count += 1
        
        db.session.commit()
        
        await ctx.send(f"✅ Cancelled {cancelled_count} duel(s).")
    
    @bot.command(name='duelstats')
    async def duel_stats(ctx, member: discord.Member = None):
        """Show duel statistics for a player"""
        target = member or ctx.author
        stats = get_player_stats(target.id)
        
        if not stats:
            await ctx.send(f"❌ {target.display_name} hasn't participated in any duels yet!")
            return
        
        player = stats['player']
        win_rate = stats['win_rate']
        
        embed = create_duel_embed(
            f"📊 Duel Statistics - {player.username}",
            "Complete duel performance overview",
            discord.Color.blue()
        )
        
        # Win/Loss record
        embed.add_field(
            name="🏆 Record",
            value=f"**Wins:** {player.total_wins}\n**Losses:** {player.total_losses}\n**Draws:** {player.total_draws}",
            inline=True
        )
        
        # Win rate
        embed.add_field(
            name="📈 Performance",
            value=f"**Win Rate:** {win_rate:.1f}%\n**Games Played:** {player.games_played}",
            inline=True
        )
        
        # Activity
        embed.add_field(
            name="📅 Activity",
            value=f"**Joined:** {player.created_at.strftime('%b %d, %Y')}\n**Last Active:** {player.last_active.strftime('%b %d, %Y')}",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @bot.command(name='spells')
    async def spell_guide(ctx):
        """Display all available spells and their strategic relationships"""
        embed = discord.Embed(
            title="📚 Spell Guide - Strategic Combat System",
            description="Learn about all available spells and their effectiveness against each other!",
            color=discord.Color.purple()
        )
        
        # Spell descriptions with strategic info
        spells_info = [
            ("🔥 **Fireball**", "A blazing projectile of pure flame.\n**Beats:** Frostbolt, Heal\n**Loses to:** Shield, Lightning"),
            ("❄️ **Frostbolt**", "An icy shard that freezes enemies.\n**Beats:** Lightning, Magic Missile\n**Loses to:** Fireball, Heal"),
            ("⚡ **Lightning**", "A crackling bolt of electricity.\n**Beats:** Fireball, Shield\n**Loses to:** Frostbolt, Magic Missile"),
            ("🛡️ **Shield**", "A protective magical barrier.\n**Beats:** Magic Missile, Fireball\n**Loses to:** Lightning, Heal"),
            ("✨ **Heal**", "Restorative magic that counters damage.\n**Beats:** Shield, Frostbolt\n**Loses to:** Fireball, Magic Missile"),
            ("💫 **Magic Missile**", "Unerring arcane projectiles.\n**Beats:** Heal, Lightning\n**Loses to:** Shield, Frostbolt")
        ]
        
        for spell_name, spell_desc in spells_info:
            embed.add_field(
                name=spell_name,
                value=spell_desc,
                inline=True
            )
        
        embed.add_field(
            name="🎯 Strategic Tips",
            value=(
                "• Each spell beats 2 others and loses to 2 others\n"
                "• Spells are hidden until both players cast\n"
                "• Ties result in another spell cast - no random winners!\n"
                "• Choose wisely in each round!\n"
                "• HP-based combat: 3 HP each, first to 0 HP loses!\n"
                "• Turn-based: 12 hours per turn for casual play"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚔️ How to Duel",
            value=(
                "`%duel @user` - Start an HP-based duel (3 HP each)\n"
                "`%cast <spell>` - Cast on your turn (12h time limit)\n"
                "`%duels` - View active duels with HP and turns\n"
                "`%duelstats` - Check your win/loss record\n"
                "`%cancelduels` - Cancel if you need to back out"
            ),
            inline=False
        )
        
        embed.set_footer(text="May your spells be ever in your favor!")
        await ctx.send(embed=embed)
    
    # ---------------- AUTOMATIC RESPONSES ----------------
    @bot.listen('on_message')
    async def auto_responses(message):
        """Respond to certain keywords automatically"""
        # Don't respond to bots or commands
        if message.author.bot or message.content.startswith('%'):
            return
        
        content = message.content.lower()
        
        # Magic-themed responses
        if any(word in content for word in ['abracadabra', 'alakazam', 'hocus pocus']):
            responses = ["✨ *magical sparkles fill the air*", "🎩 *tips wizard hat*", "⭐ The magic is strong with this one!"]
            await message.add_reaction('✨')
            await message.channel.send(random.choice(responses))
        
        elif any(word in content for word in ['spell', 'magic', 'wizard', 'enchant']):
            await message.add_reaction('🧙‍♂️')
        
        elif any(word in content for word in ['potion', 'brew', 'cauldron']):
            await message.add_reaction('🧪')
        
        elif 'good morning' in content or 'morning everyone' in content:
            await message.add_reaction('🌅')
            if random.randint(1, 3) == 1:  # 1/3 chance
                await message.channel.send("🌅 Good morning, fellow wizards! May your spells be strong today!")
        
        elif 'good night' in content or 'goodnight' in content:
            await message.add_reaction('🌙')
            if random.randint(1, 3) == 1:  # 1/3 chance
                await message.channel.send("🌙 Sweet dreams! May your magical energies restore overnight!")
        
        elif any(word in content for word in ['thanks magic', 'thank you magic', 'thanks bot']):
            responses = ["🤖 You're welcome!", "✨ Happy to help!", "🎩 At your service!"]
            await message.channel.send(random.choice(responses))
        
        # Training encouragement
        elif any(phrase in content for phrase in ['failed', 'lost', 'defeated', 'bad day']):
            if random.randint(1, 4) == 1:  # 1/4 chance to avoid spam
                encouragements = [
                    "💪 Every great wizard has faced defeat. Keep practicing!",
                    "🌟 Failure is just practice in disguise. You've got this!",
                    "⚡ Even Gandalf had bad days. Tomorrow is a new chance!"
                ]
                await message.channel.send(random.choice(encouragements))
        
        elif any(phrase in content for phrase in ['won', 'victory', 'succeeded', 'great job']):
            await message.add_reaction('🎉')
            if random.randint(1, 5) == 1:  # 1/5 chance
                celebrations = [
                    "🎉 Excellent work! Your training is paying off!",
                    "🏆 Victory well deserved! Keep up the great work!",
                    "⭐ Outstanding! The Arcane Order grows stronger!"
                ]
                await message.channel.send(random.choice(celebrations))
    
    # ---------------- AUTOMATED MONTHLY SCHEDULER ----------------
    @tasks.loop(hours=24)
    async def monthly_scheduler():
        now = datetime.utcnow().date()
        weekday = now.weekday()  # Monday=0, Tuesday=1, ... Sunday=6

        # First Monday of the month
        if weekday == 0 and 1 <= now.day <= 7:
            await post_signup_message()

        # Wednesday after first Monday
        if weekday == 2 and 8 <= now.day <= 14:
            await assign_matches()
    
    # Store scheduler task in bot for access from events
    bot.monthly_scheduler = monthly_scheduler
    
    # Error handling for commands
    @bot.event
    async def on_command_error(ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Command not found. Use `%helpme` to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument. Use `%helpme` for usage information.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid argument provided. Please check the command usage.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command. Admin privileges required.")
        elif isinstance(error, commands.BotMissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            await ctx.send(f"❌ I'm missing permissions: {missing_perms}. Please check my role settings.")
        else:
            print(f"Unhandled command error: {error}")
            await ctx.send("❌ An unexpected error occurred while executing the command.")
    
    print("✅ Commands loaded successfully!")
