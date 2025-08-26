import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
import asyncio
import random
import os
import time
import re
from tribe_detector import detect_tribes_for_discord
import sqlite3
import json
from datetime import datetime

# Global variables for signup system (in-memory only)
signup_message_id = None
signups = set()

#initialize database
def init_database():
    """Initialize the SQLite database for game logs"""
    conn = sqlite3.connect('game_logs.db')
    c = conn.cursor()
    
    # Create games table
    c.execute('''CREATE TABLE IF NOT EXISTS games
                 (game_id TEXT PRIMARY KEY, 
                  config TEXT,
                  players TEXT,
                  created_at TIMESTAMP,
                  created_by INTEGER)''')
    
    # Create logs table  
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  game_id TEXT,
                  turn INTEGER,
                  scores TEXT,
                  notes TEXT,
                  logged_at TIMESTAMP,
                  FOREIGN KEY (game_id) REFERENCES games (game_id))''')
    
    conn.commit()
    conn.close()



# Helper functions
def get_game_id_from_channel(channel_name):
    """Extract game ID from channel name"""
    patterns = [r'game[_-]?(\d+)', r'match[_-]?(\d+)', r'g[_-]?(\d+)', r'(\d{3,})']
    for pattern in patterns:
        match = re.search(pattern, channel_name, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

async def create_log_interactive(ctx):
    """Interactive createlog with buttons"""
    # This would create a message with buttons for config selection
    # Then prompt for player names step by step
    # More complex to implement fully

def get_db_connection():
    return sqlite3.connect('game_logs.db')

def format_uptime(seconds):
    """Format uptime seconds into human readable string"""
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"

def create_duel_embed(title, description, color):
    """Create a standardized embed"""
    return discord.Embed(
        title=title,
        description=description,
        color=color
    )

async def setup_commands(bot):
    """Setup all bot commands"""
    init_database()
    global signup_message_id, signups
    
    # Get configuration from environment variables
    GUILD_ID = int(os.getenv('GUILD_ID', 0))
    CHANNEL_ID = int(os.getenv('CHANNEL_ID', 0))
    
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
                await channel.send(f"**Match {i}:** {mention_list}")
            
            await channel.send(f"\n✅ **{len(matches)} matches created** from {len(signups)} signups!")
        else:
            await channel.send("Not enough players to form matches. Need at least 2 people with appropriate roles (Wizard, Apprentice, or Sage).")


    #----------------- BOT COMMANDS --------------------

    #----------------- LOG COMMANDS
    @bot.command(name='createlog')
    async def create_log(ctx, config: str, *players_and_id):
        """Create a new game log. Usage: %createlog 2v2 player1 player2 player3 player4 [gameID]"""
        # Separate players from optional game_id
        if players_and_id and players_and_id[-1].isdigit() and len(players_and_id[-1]) >= 3:
            game_id = players_and_id[-1]
            players_list = list(players_and_id[:-1])  # Changed variable name
        else:
            game_id = get_game_id_from_channel(ctx.channel.name)
            players_list = list(players_and_id)  # Changed variable name
        
        if game_id is None:
            await ctx.send("❌ No game ID provided and couldn't find one in channel name!")
            return
        
        # Validate config and player count
        if config.lower() not in ['2v2', '3v3']:
            await ctx.send("❌ Config must be '2v2' or '3v3'")
            return
        
        expected_players = 4 if config.lower() == '2v2' else 6
        if len(players_list) != expected_players:  # Changed variable name
            await ctx.send(f"❌ {config} requires {expected_players} players, got {len(players_list)}")  # Changed variable name
            return
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # Check if game already exists
            c.execute("SELECT game_id FROM games WHERE game_id = ?", (game_id,))
            if c.fetchone():
                await ctx.send(f"❌ Game {game_id} already exists!")
                conn.close()
                return
            
            # Insert new game - USE players_list instead of player_list
            c.execute('''INSERT INTO games (game_id, config, players, created_at, created_by)
                         VALUES (?, ?, ?, ?, ?)''',
                     (game_id, config, json.dumps(players_list), datetime.now(), ctx.author.id))  # Changed variable name
            
            conn.commit()
            conn.close()
            
            await ctx.send(f"✅ Game log created for {config} game {game_id} with players: {', '.join(players_list)}")  # Changed variable name
            
        except Exception as e:
            await ctx.send(f"❌ Error creating log: {str(e)}")
    
    @bot.command(name='log')
    async def add_log(ctx, *args):
        """Add turn log to a game. Usage: %log score1 score2 score3 score4 [notes] [gameID]"""
        # Get game ID from channel name first
        game_id = get_game_id_from_channel(ctx.channel.name)
        
        # Parse arguments
        scores = []
        notes = "No notes"
        provided_game_id = None
        
        # Check if last argument is a game ID (3+ digits)
        if args and args[-1].isdigit() and len(args[-1]) >= 3:
            provided_game_id = args[-1]
            args = args[:-1]
        
        # Use provided game ID or channel-detected game ID
        game_id = provided_game_id or game_id
        
        if game_id is None:
            await ctx.send("❌ No game ID provided and couldn't find one in channel name!")
            return
        
        # Check if there are notes (non-numeric argument)
        if args and not args[-1].isdigit():
            notes = args[-1]
            args = args[:-1]
        
        # The remaining args should be scores
        try:
            scores = [int(arg) for arg in args]
        except ValueError:
            await ctx.send("❌ Scores must be integers")
            return
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # Get game config to validate score count
            c.execute("SELECT config, players FROM games WHERE game_id = ?", (game_id,))
            game = c.fetchone()
            
            if not game:
                await ctx.send(f"❌ Game {game_id} not found! Use %createlog first.")
                conn.close()
                return
            
            config = game[0]
            expected_scores = 4 if config.lower() == '2v2' else 6
            
            if len(scores) != expected_scores:
                await ctx.send(f"❌ {config} requires {expected_scores} scores, got {len(scores)}")
                conn.close()
                return
            
            # Get next turn number
            c.execute("SELECT COALESCE(MAX(turn), 0) + 1 FROM logs WHERE game_id = ?", (game_id,))
            next_turn = c.fetchone()[0]
            
            # Insert log
            c.execute('''INSERT INTO logs (game_id, turn, scores, notes, logged_at)
                         VALUES (?, ?, ?, ?, ?)''',
                     (game_id, next_turn, json.dumps(scores), notes, datetime.now()))
            
            conn.commit()
            
            # Show confirmation
            c.execute("SELECT players FROM games WHERE game_id = ?", (game_id,))
            players_json = c.fetchone()[0]
            players = json.loads(players_json)
            
            confirmation = f"✅ **Turn {next_turn} logged successfully for game {game_id}:**\n"
            confirmation += "\n".join(f"{players[i]}: {scores[i]}" for i in range(len(scores)))
            if notes and notes != "No notes":
                confirmation += f"\n*Notes:* {notes}"
            
            await ctx.send(confirmation)
            conn.close()
            
        except Exception as e:
            await ctx.send(f"❌ Error adding log: {str(e)}")
    
    @bot.command(name='showlogs')
    async def show_logs(ctx, game_id: str = None, turn_range: str = None):
        """Show logs for a game. Usage: %showlogs [gameID] [turn|start-end]"""
        # Get game ID from channel name if not provided
        if game_id is None:
            game_id = get_game_id_from_channel(ctx.channel.name)
            if game_id is None:
                await ctx.send("❌ No game ID provided and couldn't find one in channel name!")
                return
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # Get game info FIRST
            c.execute("SELECT config, players FROM games WHERE game_id = ?", (game_id,))
            game = c.fetchone()
            
            if not game:
                await ctx.send(f"❌ Game {game_id} not found!")
                conn.close()
                return
            
            config, players_json = game  # This defines 'config' variable
            players = json.loads(players_json)
            
            # Parse turn range if provided
            start_turn = end_turn = None
            if turn_range:
                if '-' in turn_range:
                    try:
                        start_turn, end_turn = map(int, turn_range.split('-'))
                    except ValueError:
                        await ctx.send("❌ Turn range must be in format 'start-end' (e.g., '3-7')")
                        conn.close()
                        return
                else:
                    try:
                        start_turn = end_turn = int(turn_range)
                    except ValueError:
                        await ctx.send("❌ Turn must be a number")
                        conn.close()
                        return
            
            # Build query with optional turn filtering
            if start_turn is not None:
                query = "SELECT turn, scores, notes, logged_at FROM logs WHERE game_id = ? AND turn BETWEEN ? AND ? ORDER BY turn"
                params = (game_id, start_turn, end_turn)
            else:
                query = "SELECT turn, scores, notes, logged_at FROM logs WHERE game_id = ? ORDER BY turn"
                params = (game_id,)
            
            c.execute(query, params)
            logs = c.fetchall()
            conn.close()
            
            # Format output
            if not logs:
                range_text = f" (turns {turn_range})" if turn_range else ""
                await ctx.send(f"📝 Game {game_id} ({config}){range_text} - No logs found")
                return
            
            response = [f"**📝 Game {game_id} ({config}) - {len(logs)} turns**"]
            if turn_range:
                response[0] += f" (showing {turn_range})"
            response.append(f"**Players:** {', '.join(players)}")
            response.append("")
            
            for turn, scores_json, notes, logged_at in logs:
                scores = json.loads(scores_json)
                score_display = " | ".join(f"{players[i]}: {scores[i]}" for i in range(len(scores)))
                response.append(f"**Turn {turn}:** {score_display}")
                if notes and notes != "No notes":
                    response.append(f"   *Notes:* {notes}")
                response.append("")
            
            # Send in chunks if too long
            full_response = "\n".join(response)
            if len(full_response) > 2000:
                chunks = [full_response[i:i+2000] for i in range(0, len(full_response), 2000)]
                for chunk in chunks:
                    await ctx.send(chunk)
            else:
                await ctx.send(full_response)
                
        except Exception as e:
            await ctx.send(f"❌ Error showing logs: {str(e)}")
    
    @bot.command(name='deletelog')
    @commands.has_permissions(administrator=True)
    async def delete_log(ctx, game_id: str):
        """Delete a game log (Admin only). Usage: %deletelog gameID"""
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # Delete logs and game
            c.execute("DELETE FROM logs WHERE game_id = ?", (game_id,))
            c.execute("DELETE FROM games WHERE game_id = ?", (game_id,))
            
            conn.commit()
            conn.close()
            
            await ctx.send(f"✅ Game {game_id} and all logs deleted")
            
        except Exception as e:
            await ctx.send(f"❌ Error deleting log: {str(e)}")
    
    @bot.command(name='editlog')
    async def edit_log(ctx, turn: int, scores: str, notes: str = "No notes", game_id: str = None):
        """Edit a specific turn log. Usage: %editlog 5 "10,20,30,40" "New notes" [gameID]"""
        # Get game ID from channel name if not provided
        if game_id is None:
            game_id = get_game_id_from_channel(ctx.channel.name)
            if game_id is None:
                await ctx.send("❌ No game ID provided and couldn't find one in channel name!")
                return
        
        try:
            # Parse scores
            score_list = [int(s.strip()) for s in scores.split(',')]
            
            conn = get_db_connection()
            c = conn.cursor()
            
            # Get game config to validate score count
            c.execute("SELECT config FROM games WHERE game_id = ?", (game_id,))
            game = c.fetchone()
            
            if not game:
                await ctx.send(f"❌ Game {game_id} not found!")
                conn.close()
                return
            
            config = game[0]
            expected_scores = 4 if config.lower() == '2v2' else 6
            
            if len(score_list) != expected_scores:
                await ctx.send(f"❌ {config} requires {expected_scores} scores, got {len(score_list)}")
                conn.close()
                return
            
            # Update log
            c.execute('''UPDATE logs SET scores = ?, notes = ?, logged_at = ?
                         WHERE game_id = ? AND turn = ?''',
                     (json.dumps(score_list), notes, datetime.now(), game_id, turn))
            
            if c.rowcount == 0:
                await ctx.send(f"❌ Turn {turn} not found for game {game_id}")
            else:
                conn.commit()
                await ctx.send(f"✅ Turn {turn} updated for game {game_id}")
            
            conn.close()
            
        except ValueError:
            await ctx.send("❌ Scores must be integers separated by commas")
        except Exception as e:
            await ctx.send(f"❌ Error editing log: {str(e)}")

    #----------------- TRIBE DETECTOR COMMAND-----------
    @bot.command(name='detect')
    async def detect_tribes(ctx, map_name: str, game_size: str, max_points: int, *enemy_scores):
        """
        Detect opponent tribes with advanced filtering. Usage:
        %detect pangea 3v3 12 515 620 630
        %detect archi 2v2 10 515 620
        """
        # Check if user has Spellkeeper role
        spellkeeper_role = discord.utils.get(ctx.author.roles, name="Spellkeeper")
        if not spellkeeper_role:
            await ctx.send("❌ You need the **Spellkeeper** role to use this command!")
            return
        
        # Input validation - remove quotes if user added them
        map_name = map_name.strip('"\'')
        game_size = game_size.strip('"\'')
        
        # Map name aliases and auto-correction
        map_aliases = {
            'pang': 'pangea', 'pangea': 'pangea',
            'arch': 'archi', 'archi': 'archi', 'archipelago': 'archi',
            'cont': 'conti', 'conti': 'conti', 'continents': 'conti',
            'dry': 'dry', 'dryland': 'dry',
            'lake': 'lakes', 'lakes': 'lakes'
        }
        
        # Game size aliases
        game_aliases = {
            '2v2': '2v2', '2': '2v2', '22': '2v2',
            '3v3': '3v3', '3': '3v3', '33': '3v3'
        }
        
        # Auto-correct map name
        map_name_lower = map_name.lower()
        if map_name_lower in map_aliases:
            map_name = map_aliases[map_name_lower]
        else:
            await ctx.send(f"❌ Invalid map: {map_name}. Valid maps: pangea, archi, conti, dry, lakes")
            return
        
        # Auto-correct game size
        game_size_lower = game_size.lower()
        if game_size_lower in game_aliases:
            game_size = game_aliases[game_size_lower]
        else:
            await ctx.send("❌ Game size must be '2v2' or '3v3'")
            return
        
        expected_count = 2 if game_size == "2v2" else 3
        if len(enemy_scores) != expected_count:
            await ctx.send(f"❌ {game_size} requires {expected_count} enemy scores, got {len(enemy_scores)}")
            return
        
        # Convert scores to integers (remove quotes if any)
        try:
            enemy_scores_int = []
            for score in enemy_scores:
                clean_score = str(score).strip('"\'')
                enemy_scores_int.append(int(clean_score))
        except ValueError:
            await ctx.send("❌ Enemy scores must be integers")
            return
        
        # Validate scores are within possible range (accounting for corner spawns -5)
        base_valid_scores = [415, 465, 515, 520, 530, 615, 620, 630, 730]
        corner_valid_scores = [score - 5 for score in base_valid_scores if score - 5 >= 0]
        all_valid_scores = list(set(base_valid_scores + corner_valid_scores))
        all_valid_scores.sort()
        
        for score in enemy_scores_int:
            if score not in all_valid_scores:
                await ctx.send(f"❌ Invalid score: {score}. Valid scores are: {', '.join(map(str, all_valid_scores))}")
                return
        
        # Validate max points is reasonable
        if max_points < 1 or max_points > 20:
            await ctx.send("❌ Max points must be between 1 and 20")
            return
        
        # Show processing message for long operations
        processing_msg = await ctx.send("🔍 Analyzing possible tribe combinations...")
        
        # Call the detection with enhanced filtering
        try:
            result = detect_tribes_for_discord(
                map_name, game_size, max_points, enemy_scores_int,
                consider_corner_spawns=True,
                min_points_threshold=2
            )
            
            # Delete processing message
            await processing_msg.delete()
            
            # Split long messages if needed
            if len(result) > 2000:
                parts = [result[i:i+2000] for i in range(0, len(result), 2000)]
                for part in parts:
                    await ctx.send(part)
                    await asyncio.sleep(1)
            else:
                await ctx.send(result)
                
        except Exception as e:
            try:
                await processing_msg.delete()
            except:
                pass
            await ctx.send(f"❌ Error in tribe detection: {str(e)}")
    # ---------------- REMINDER COMMANDS ----------------
    @bot.command()
    async def remindme(ctx, time_in_minutes: int, *, reminder_message: str):
        """Set a reminder in minutes. Usage: !remindme 10 Do the dishes"""
        if time_in_minutes <= 0:
            return await ctx.send("❌ Time must be greater than 0 minutes.")
        if time_in_minutes > 10080:  # 7 days limit
            return await ctx.send("❌ Reminders cannot be set for more than 7 days (10,080 minutes).")
        
        await ctx.send(f"⏰ Okay {ctx.author.mention}, I will remind you in {time_in_minutes} minute(s).")
        
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

    @bot.command(name='server')
    @is_high_mage()
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

    @bot.command(name='initiate')
    @is_high_mage()  # Uses your existing High Mage check
    async def initiate_member(ctx, member: discord.Member, path: str):
        """
        Add Spellkeeper role and assign either Warlocks or Sorcerers path.
        Usage: %initiate @Member warlocks  OR  %initiate @Member sorcerers
        """
        try:
            # Get the roles
            spellkeeper_role = discord.utils.get(ctx.guild.roles, name="Spellkeeper")
            warlocks_role = discord.utils.get(ctx.guild.roles, name="Warlocks")
            sorcerers_role = discord.utils.get(ctx.guild.roles, name="Sorcerers")
            
            # Check if roles exist
            if not spellkeeper_role:
                await ctx.send("❌ Spellkeeper role not found!")
                return
            
            path = path.lower()
            if path == "warlocks" and not warlocks_role:
                await ctx.send("❌ Warlocks role not found!")
                return
            elif path == "sorcerers" and not sorcerers_role:
                await ctx.send("❌ Sorcerers role not found!")
                return
            elif path not in ["warlocks", "sorcerers"]:
                await ctx.send("❌ Path must be either 'warlocks' or 'sorcerers'!")
                return
            
            # Add roles to member
            roles_to_add = [spellkeeper_role]
            if path == "warlocks" and warlocks_role:
                roles_to_add.append(warlocks_role)
            elif path == "sorcerers" and sorcerers_role:
                roles_to_add.append(sorcerers_role)
            
            await member.add_roles(*roles_to_add)
            
            await ctx.send(f"✅ {member.mention} has been initiated as a Spellkeeper on the {path.title()} path!")
            
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to manage roles!")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed to add roles: {e}")
        except Exception as e:
            await ctx.send(f"❌ Unexpected error: {e}")

    @bot.command(name="helpmeleader")
    @is_high_mage()
    async def helpme(ctx):
        """Show bot commands and usage"""
        embed = discord.Embed(
            title="📜 Bot Commands for the High Mages",
            description="Here are all available commands, glorious sorcerer:",
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
                    "`%serverstats` - Detailed server statistics\n"
                    "`%initiate` - Add Spellkeeper and either Sorcerers or Walocks role to a player"
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
        
        embed.set_footer(text="Training signups happen automatically on the first Monday of each month!")
        await ctx.send(embed=embed)
    
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
                "`%info` - Show bot information\n"
                "`%helpme` - Show this help message\n"
                "`%setemojis` - Set emoji header for game channels (Spellkeeper Only)\n"
                "`%detect` - Detect enemy tribes (Spellkeeper Only)"
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

    @bot.command(name='setemojis')
    async def emojis_command(ctx, emoji1: str, emoji2: str, emoji3: str = None, emoji4: str = None):
        """
        Replace emojis at the beginning of the channel name.
        Usage: %emojis 😊 👍 [optional_emoji3] [optional_emoji4]
        """
        print(f"🎯 Emojis command called by {ctx.author} with args: {emoji1}, {emoji2}, {emoji3}, {emoji4}")
        
        # Check if user has Spellkeeper role (exact match since it's capitalized)
        spellkeeper_role = discord.utils.get(ctx.author.roles, name="Spellkeeper")
        
        if not spellkeeper_role:
            # Debug: list all roles the user has
            user_roles = [role.name for role in ctx.author.roles]
            print(f"❌ User roles: {user_roles}")
            await ctx.send("❌ You need the **Spellkeeper** role to use this command!")
            return
        
        print(f"✅ User has Spellkeeper role: {spellkeeper_role}")
        
        # ADDED: Channel group restriction
        # Replace these IDs with your actual category/channel group IDs
        ALLOWED_CATEGORY_IDS = [1398755280384430130, 1398755544239444168]  # Replace with your actual category IDs
        
        if ctx.channel.category_id not in ALLOWED_CATEGORY_IDS:
            await ctx.send("❌ This command can only be used in specific channel groups!")
            print(f"❌ Command used in disallowed category: {ctx.channel.category_id}")
            return
        
        print(f"✅ Channel is in allowed category: {ctx.channel.category_id}")
        
        # Get all emojis provided (filter out None values)
        new_emojis = [emoji for emoji in [emoji1, emoji2, emoji3, emoji4] if emoji is not None]
        print(f"📝 New emojis to add: {new_emojis}")
        
        # Remove any existing emojis from the beginning of the channel name
        current_name = ctx.channel.name
        print(f"📋 Current channel name: '{current_name}'")
        
        # Regex to match emojis at the start (including custom emojis)
        cleaned_name = re.sub(r'^(\s*<a?:[a-zA-Z0-9_]+:[0-9]+>\s*|\s*[^\w\s]\s*)+', '', current_name)
        cleaned_name = cleaned_name.strip()
        print(f"🧹 Cleaned name: '{cleaned_name}'")
        
        # Combine new emojis with cleaned channel name
        emoji_string = ''.join(new_emojis)
        new_channel_name = f"{emoji_string} {cleaned_name}".strip()
        print(f"🆕 New channel name: '{new_channel_name}' (length: {len(new_channel_name)})")
        
        # Discord channel name limit is 100 characters
        if len(new_channel_name) > 100:
            await ctx.send("❌ The new channel name is too long! Maximum 100 characters.")
            return
        
        try:
            # Double-check bot permissions
            bot_perms = ctx.channel.permissions_for(ctx.guild.me)
            print(f"🔐 Bot permissions: Manage_Channels={bot_perms.manage_channels}, Administrator={bot_perms.administrator}")
            
            if not (bot_perms.manage_channels or bot_perms.administrator):
                await ctx.send("❌ I don't have permission to edit this channel!")
                return
            
            # Try to update the channel
            print("🔄 Attempting to update channel name...")
            await ctx.channel.edit(name=new_channel_name)
            await ctx.send(f"✅ Channel emojis updated to: {emoji_string}")
            print(f"🎉 Successfully updated channel name to: '{new_channel_name}'")
            
        except discord.Forbidden:
            error_msg = "❌ I don't have permission to edit this channel! (Forbidden)"
            print(error_msg)
            await ctx.send(error_msg)
        except discord.HTTPException as e:
            error_msg = f"❌ Failed to update channel: {e}"
            print(error_msg)
            print(f"🚨 Full error details: {repr(e)}")
            await ctx.send("❌ Failed to update channel. Check console for details.")
        except Exception as e:
            error_msg = f"❌ Unexpected error: {e}"
            print(error_msg)
            print(f"🚨 Unexpected error details: {repr(e)}")
            await ctx.send("❌ An unexpected error occurred. Check console for details.")
        
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
        result = random.choice(["Heads", "Tails", "Heads", "Tails", "Heads", "Tails", "Heads", "Tails", "Heads", "Tails", "Your Mom"])
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
        quotes = [
            
            ("The only way to do great work is to love what you do.", "Steve Jobs"),
            ("Magic is believing in yourself. If you can do that, you can make anything happen.", "Johann Wolfgang von Goethe"),
            ("The real magic happens when you start believing in yourself.", "Unknown"),
            ("Training is everything. The peach was once a bitter almond; cauliflower is nothing but cabbage with a college education.", "Mark Twain"),
            ("Excellence is never an accident. It is always the result of high intention, sincere effort, and skillful execution.", "Aristotle"),
            ("The expert in anything was once a beginner.", "Helen Hayes"),
            ("Practice makes progress, not perfection.", "Unknown"),
            ("A wizard is never late, nor is he early. He arrives precisely when he means to.", "Gandalf"),
            ("It does not do to dwell on dreams and forget to live.", "Albus Dumbledore"),
            ("You have plenty of courage, I am sure. All you need is confidence in yourself", "The Wizard of Oz"),
            ("It is our choices, Harry, that show what we truly are, far more than our abilities.", "Albus Dumbledore"),
            ("Things never happen the same way twice, dear one.", "Aslan"),
            ("The future is nothing but a hundred thousand threads, but the past is a fabric that can never be rewoven.", "Merlin")

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

        elif any(word in content for word in ['@Spellkeeper Please Welcome']):
            responses = ['Welcome, apprentice of the arcane. You step now into a realm where knowledge is power, silence holds secrets, and every spark you conjure shapes both your fate and the world around you. Walk with humility, seek with courage, and remember: true sorcery is not in the spell, but in the soul that casts it.']
            await message.channel.send(responses)
    
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

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='%', intents=intents)

# Store start time for uptime calculation
bot.start_time = time.time()

# Event handlers
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,  
            name="use %helpme"  # No space between % and helpme
        )
    )
    
    # Setup commands and start scheduler
    await setup_commands(bot)
    bot.monthly_scheduler.start()

@bot.event
async def on_reaction_add(reaction, user):
    """Handle reaction-based signups"""
    global signups
    
    # Skip bot reactions
    if user.bot:
        return
    
    # Check if this is the signup message
    if reaction.message.id == signup_message_id and str(reaction.emoji) == "🐼":
        signups.add(user.id)
        print(f"✅ {user.name} signed up for training matches")

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ DISCORD_TOKEN environment variable not set!")
        exit(1)
    bot.run(token)
