import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
#from discord_components import DiscordComponents, Button, ButtonStyle, Select, SelectOption
from datetime import datetime, timedelta, timezone
import asyncio
from discord import ui, ButtonStyle
import random
import os
import time
import re
from tribe_detector import detect_tribes_for_discord
import sqlite3
import json
from datetime import datetime


#button classes
class MapSelectView(ui.View):
    def __init__(self, ctx, timeout=60):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.map_name = None
        self.value = None
    
    @ui.button(label="Pangea", style=ButtonStyle.primary)
    async def pangea(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command author can interact!", ephemeral=True)
            return
        self.map_name = "pangea"
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @ui.button(label="Archi", style=ButtonStyle.primary)
    async def archi(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command author can interact!", ephemeral=True)
            return
        self.map_name = "archi"
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @ui.button(label="Conti", style=ButtonStyle.primary)
    async def conti(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command author can interact!", ephemeral=True)
            return
        self.map_name = "conti"
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @ui.button(label="Dry", style=ButtonStyle.primary)
    async def dry(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command author can interact!", ephemeral=True)
            return
        self.map_name = "dry"
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @ui.button(label="Lakes", style=ButtonStyle.primary)
    async def lakes(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command author can interact!", ephemeral=True)
            return
        self.map_name = "lakes"
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @ui.button(label="Cancel", style=ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command author can interact!", ephemeral=True)
            return
        self.value = False
        self.stop()
        await interaction.response.defer()

class GameSizeView(ui.View):
    def __init__(self, ctx, timeout=60):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.game_size = None
        self.value = None
    
    @ui.button(label="2v2", style=ButtonStyle.primary)
    async def two_v_two(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command author can interact!", ephemeral=True)
            return
        self.game_size = "2v2"
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @ui.button(label="3v3", style=ButtonStyle.primary)
    async def three_v_three(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command author can interact!", ephemeral=True)
            return
        self.game_size = "3v3"
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @ui.button(label="Cancel", style=ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command author can interact!", ephemeral=True)
            return
        self.value = False
        self.stop()
        await interaction.response.defer()

class ConfigView(ui.View):
    def __init__(self, ctx, timeout=60):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.config = None
        self.value = None
    
    @ui.button(label="2v2", style=ButtonStyle.primary)
    async def config_2v2(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command author can interact!", ephemeral=True)
            return
        self.config = "2v2"
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @ui.button(label="3v3", style=ButtonStyle.primary)
    async def config_3v3(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command author can interact!", ephemeral=True)
            return
        self.config = "3v3"
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @ui.button(label="Cancel", style=ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command author can interact!", ephemeral=True)
            return
        self.value = False
        self.stop()
        await interaction.response.defer()

class ConfirmView(ui.View):
    def __init__(self, ctx, timeout=60):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.value = None
    
    @ui.button(label="✅ Confirm", style=ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command author can interact!", ephemeral=True)
            return
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @ui.button(label="❌ Cancel", style=ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command author can interact!", ephemeral=True)
            return
        self.value = False
        self.stop()
        await interaction.response.defer()

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
async def can_use_log_commands(ctx):
    """Check if user is admin or teammate in this PolyELO game channel"""
    # Allow admins
    if ctx.author.guild_permissions.administrator:
        return True
    
    # Check if this is a PolyELO game channel by looking for game ID
    game_id = get_game_id_from_channel(ctx.channel.name)
    if not game_id:
        return False
    
    # Get the last 100 messages to find the PolyELO team announcement
    try:
        async for message in ctx.channel.history(limit=100):
            if message.author.bot and "Your teammates are" in message.content:
                # Extract user IDs from the message
                import re
                user_ids = re.findall(r'<@!?(\d+)>', message.content)
                
                # Check if current user is one of the teammates
                if str(ctx.author.id) in user_ids:
                    return True
                
                # Also check if user is mentioned in the teams section
                teams_section = re.search(r'Side.*?:(.*?)(?=Side|$)', message.content, re.DOTALL)
                if teams_section:
                    team_text = teams_section.group(1)
                    # Check if user's display name appears in the team roster
                    author_display_name = ctx.author.display_name
                    if author_display_name in team_text:
                        return True
                
                break  # Stop after finding the PolyELO message
        
        return False
        
    except Exception as e:
        print(f"Error checking PolyELO permissions: {e}")
        return False
            

def get_game_id_from_channel(channel_name):
    """Extract 6-digit game ID from channel name"""
    # Look for exactly 6 consecutive digits
    match = re.search(r'(\d{6})', channel_name)
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

   #----------------- LOG COMMANDS --------------------

# Load logs from JSON file
def load_logs():
    try:
        with open('logs.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"games": {}, "logs": {}}

# Save logs to JSON file
def save_logs(logs_data):
    with open('logs.json', 'w') as f:
        json.dump(logs_data, f, indent=2)

@bot.command(name='createlog')
@commands.check(can_use_log_commands)
async def create_log(ctx, config: str = None, *players_and_id):
    """Create a new game log with interactive guidance"""
    
    # If no arguments provided, start interactive mode
    if config is None:
        await start_interactive_createlog(ctx)
        return
    
    # Otherwise proceed with normal command processing
    # ... (your existing createlog logic) ...

async def start_interactive_createlog(ctx):
    """Interactive create log with native Discord buttons"""
    # Step 1: Config selection
    embed = discord.Embed(
        title="🎮 Create Game Log - Step 1/3",
        description="Select the game configuration:",
        color=0x00ff00
    )
    embed.add_field(name="2v2", value="4 players total", inline=True)
    embed.add_field(name="3v3", value="6 players total", inline=True)
    embed.set_footer(text="This message will guide you through creating a game log.")
    
    view = ConfigView(ctx)
    message = await ctx.send(embed=embed, view=view)
    
    # Wait for button click
    await view.wait()
    
    if view.value is False or view.config is None:
        await message.edit(content="❌ Game creation cancelled.", embed=None, view=None)
        return
    
    config = view.config
    expected_players = 4 if config == "2v2" else 6
    
    # Step 2: Get players
    embed = discord.Embed(
        title=f"🎮 Create Game Log - Step 2/3",
        description=f"**Configuration:** {config}\n\nPlease enter the player names for all {expected_players} players (separated by commas or new lines):",
        color=0x00ff00
    )
    embed.add_field(
        name="Example", 
        value="```player1, player2, player3, player4```" if config == "2v2" else "```player1, player2, player3, player4, player5, player6```",
        inline=False
    )
    
    await message.edit(embed=embed, view=None)
    
    # Wait for player input
    try:
        player_msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id,
            timeout=120.0
        )
        
        # Parse players
        players_text = player_msg.content
        players_list = [p.strip() for p in players_text.split(',') if p.strip()]
        
        # Also check for newlines if commas didn't work
        if len(players_list) != expected_players and '\n' in players_text:
            players_list = [p.strip() for p in players_text.split('\n') if p.strip()]
        
        # Validate player count
        if len(players_list) != expected_players:
            await ctx.send(f"❌ {config} requires {expected_players} players, but you provided {len(players_list)}. Please try `%createlog` again.")
            return
        
        # Step 3: Confirm and create
        game_id = get_game_id_from_channel(ctx.channel.name)
        
        embed = discord.Embed(
            title=f"🎮 Create Game Log - Step 3/3",
            description="**Please review the details:**",
            color=0x00ff00
        )
        embed.add_field(name="Configuration", value=config, inline=True)
        embed.add_field(name="Game ID", value=game_id or "Auto-detected", inline=True)
        embed.add_field(name="Players", value="\n".join(players_list), inline=False)
        
        confirm_view = ConfirmView(ctx)
        await message.edit(embed=embed, view=confirm_view)
        
        # Wait for confirmation
        await confirm_view.wait()
        
        if confirm_view.value is False:
            await message.edit(content="❌ Game creation cancelled.", embed=None, view=None)
            return
        
        # Create the game
        await message.edit(content="🔄 Creating game...", embed=None, view=None)
        
        try:
            logs_data = load_logs()
            final_game_id = game_id or str(ctx.channel.id)[-6:]
            
            # Check if game exists
            if final_game_id in logs_data["games"]:
                await ctx.send(f"❌ Game {final_game_id} already exists!")
                return
            
            # Create new game
            logs_data["games"][final_game_id] = {
                "config": config,
                "players": players_list,
                "created_at": datetime.now().isoformat(),
                "created_by": ctx.author.id
            }
            
            # Initialize empty logs for this game
            logs_data["logs"][final_game_id] = {}
            
            save_logs(logs_data)
            
            # Clean up
            try:
                await player_msg.delete()
            except:
                pass
            
            # Success
            success_embed = discord.Embed(
                title="✅ Game Log Created Successfully!",
                description=f"**Game ID:** {final_game_id}\n**Config:** {config}",
                color=0x00ff00
            )
            success_embed.add_field(name="Players", value="\n".join(players_list), inline=False)
            success_embed.add_field(
                name="Next Steps", 
                value=f"Use `%log` to add turns:\n`%log 500 500 500 500`",
                inline=False
            )
            
            await message.edit(content=None, embed=success_embed, view=None)
            
        except Exception as e:
            await ctx.send(f"❌ Error creating game: {str(e)}")
            
    except asyncio.TimeoutError:
        await message.edit(content="⏰ Input timed out. Please try `%createlog` again.", embed=None, view=None)


@bot.command(name='log')
@commands.check(can_use_log_commands)
async def add_log(ctx, *args):
    """Add turn log to a game. Usage: %log score1 score2 score3 score4 [notes] [gameID]"""
    # Get game ID from channel name first
    game_id = get_game_id_from_channel(ctx.channel.name)
    
    # Parse arguments
    scores = []
    notes = "No notes"
    provided_game_id = None
    
    # Only check for game ID if it's 6 digits (actual game ID length)
    if args and args[-1].isdigit() and len(args[-1]) == 6:
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
        logs_data = load_logs()
        
        # Get game config to validate score count
        if game_id not in logs_data["games"]:
            await ctx.send(f"❌ Game {game_id} not found! Use %createlog first.")
            return
        
        game = logs_data["games"][game_id]
        config = game["config"]
        expected_scores = 4 if config.lower() == '2v2' else 6
        
        if len(scores) != expected_scores:
            await ctx.send(f"❌ {config} requires {expected_scores} scores, got {len(scores)}")
            return
        
        # Get next turn number - CHANGED TO START AT 0
        game_logs = logs_data["logs"][game_id]
        next_turn = max(game_logs.keys(), default=-1) + 1
        
        # Add log
        logs_data["logs"][game_id][next_turn] = {
            "scores": scores,
            "notes": notes,
            "logged_at": datetime.now().isoformat()
        }
        
        save_logs(logs_data)
        
        # Show confirmation
        players = game["players"]
        
        confirmation = f"✅ **Turn {next_turn} logged successfully for game {game_id}:**\n"
        confirmation += "\n".join(f"{players[i]}: {scores[i]}" for i in range(len(scores)))
        if notes and notes != "No notes":
            confirmation += f"\n*Notes:* {notes}"
        
        await ctx.send(confirmation)
        
    except Exception as e:
        await ctx.send(f"❌ Error adding log: {str(e)}")


@bot.command(name='undo')
@commands.check(can_use_log_commands)
async def undo_last_turn(ctx, game_id: str = None):
    """Remove the most recent turn. Usage: %undo [gameID]"""
    # Get game ID from channel name if not provided
    if game_id is None:
        game_id = get_game_id_from_channel(ctx.channel.name)
        if game_id is None:
            await ctx.send("❌ No game ID provided and couldn't find one in channel name!")
            return
    
    try:
        logs_data = load_logs()
        
        # First check if game exists
        if game_id not in logs_data["games"]:
            await ctx.send(f"❌ Game {game_id} not found!")
            return
        
        game = logs_data["games"][game_id]
        game_logs = logs_data["logs"][game_id]
        
        # Get the most recent turn
        if not game_logs:
            await ctx.send(f"❌ No turns found for game {game_id}!")
            return
        
        turn_number = max(game_logs.keys())
        turn_data = game_logs[turn_number]
        scores = turn_data["scores"]
        notes = turn_data["notes"]
        
        # Get players for display
        players = game["players"]
        
        # Confirm deletion
        confirmation_msg = (
            f"⚠️ **Are you sure you want to delete Turn {turn_number}?**\n"
            f"**Scores:** {', '.join(f'{players[i]}: {scores[i]}' for i in range(len(scores)))}\n"
            f"**Notes:** {notes}\n\n"
            f"Type `confirm` in the next 30 seconds to proceed, or anything else to cancel."
        )
        
        await ctx.send(confirmation_msg)
        
        # Wait for confirmation
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            response = await bot.wait_for('message', timeout=30.0, check=check)
            
            if response.content.lower() == 'confirm':
                # Delete the turn
                del logs_data["logs"][game_id][turn_number]
                save_logs(logs_data)
                
                # Check if any turns remain
                remaining_turns = len(logs_data["logs"][game_id])
                
                await ctx.send(f"✅ **Turn {turn_number} deleted successfully!**\n"
                              f"**Game {game_id}** now has {remaining_turns} turn{'s' if remaining_turns != 1 else ''}.")
            else:
                await ctx.send("❌ Turn deletion cancelled.")
                
        except asyncio.TimeoutError:
            await ctx.send("⏰ Turn deletion timed out. Please try again.")
        
    except Exception as e:
        await ctx.send(f"❌ Error undoing turn: {str(e)}")

@bot.command(name='showlogs')
@commands.check(can_use_log_commands)
async def show_logs(ctx, game_id: str = None, turn_range: str = None):
    """Show logs for a game. Usage: %showlogs [gameID] [turn|start-end]"""
    # Get game ID from channel name if not provided
    if game_id is None:
        game_id = get_game_id_from_channel(ctx.channel.name)
        if game_id is None:
            await ctx.send("❌ No game ID provided and couldn't find one in channel name!")
            return
    
    try:
        logs_data = load_logs()
        
        # Get game info FIRST
        if game_id not in logs_data["games"]:
            await ctx.send(f"❌ Game {game_id} not found!")
            return
        
        game = logs_data["games"][game_id]
        config = game["config"]
        players = game["players"]
        
        # Parse turn range if provided
        start_turn = end_turn = None
        if turn_range:
            if '-' in turn_range:
                try:
                    start_turn, end_turn = map(int, turn_range.split('-'))
                except ValueError:
                    await ctx.send("❌ Turn range must be in format 'start-end' (e.g., '3-7')")
                    return
            else:
                try:
                    start_turn = end_turn = int(turn_range)
                except ValueError:
                    await ctx.send("❌ Turn must be a number")
                    return
        
        # Get logs with optional turn filtering
        game_logs = logs_data["logs"][game_id]
        
        # Filter logs by turn range if specified
        if start_turn is not None:
            logs = {turn: data for turn, data in game_logs.items() 
                   if start_turn <= turn <= end_turn}
        else:
            logs = game_logs
        
        # Sort by turn number
        sorted_logs = sorted(logs.items(), key=lambda x: x[0])
        
        # Format output
        if not sorted_logs:
            range_text = f" (turns {turn_range})" if turn_range else ""
            await ctx.send(f"📝 Game {game_id} ({config}){range_text} - No logs found\n**Players:** {', '.join(players)}")
            return
        
        response = [f"**📝 Game {game_id} ({config}) - {len(sorted_logs)} turns**"]
        if turn_range:
            response[0] += f" (showing {turn_range})"
        response.append(f"**Players:** {', '.join(players)}")
        response.append("")
        
        for turn, turn_data in sorted_logs:
            scores = turn_data["scores"]
            notes = turn_data["notes"]
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
@commands.check(can_use_log_commands)
async def delete_log(ctx, game_id: str = None):
    """Delete a game log (Admin only). Usage: %deletelog [gameID]"""
    # If no game ID provided, try to detect from channel name
    if game_id is None:
        game_id = get_game_id_from_channel(ctx.channel.name)
        if game_id is None:
            await ctx.send("❌ No game ID provided and couldn't find one in channel name!")
            return
    
    try:
        logs_data = load_logs()
        
        # Check if game exists first
        if game_id not in logs_data["games"]:
            await ctx.send(f"❌ Game {game_id} not found!")
            return
        
        # Delete game and logs
        del logs_data["games"][game_id]
        if game_id in logs_data["logs"]:
            del logs_data["logs"][game_id]
        
        save_logs(logs_data)
        
        await ctx.send(f"✅ Game {game_id} and all logs deleted")
        
    except Exception as e:
        await ctx.send(f"❌ Error deleting log: {str(e)}")

@bot.command(name='editlog')
@commands.check(can_use_log_commands)
async def edit_log(ctx, turn: int, *args):
    """Edit a specific turn log. Usage: %editlog 5 10 20 30 40 [notes] [gameID]"""
    # Get game ID from channel name if not provided
    game_id = get_game_id_from_channel(ctx.channel.name)
    
    # Parse arguments
    scores = []
    notes = "No notes"
    provided_game_id = None
    
    # Check if last argument is a game ID (6 digits)
    if args and args[-1].isdigit() and len(args[-1]) == 6:
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
        logs_data = load_logs()
        
        # Get game config to validate score count
        if game_id not in logs_data["games"]:
            await ctx.send(f"❌ Game {game_id} not found!")
            return
        
        game = logs_data["games"][game_id]
        config = game["config"]
        expected_scores = 4 if config.lower() == '2v2' else 6
        
        if len(scores) != expected_scores:
            await ctx.send(f"❌ {config} requires {expected_scores} scores, got {len(scores)}")
            return
        
        # Update log
        if turn not in logs_data["logs"][game_id]:
            await ctx.send(f"❌ Turn {turn} not found for game {game_id}")
            return
        
        logs_data["logs"][game_id][turn] = {
            "scores": scores,
            "notes": notes,
            "logged_at": datetime.now().isoformat()
        }
        
        save_logs(logs_data)
        await ctx.send(f"✅ Turn {turn} updated for game {game_id}")
        
    except Exception as e:
        await ctx.send(f"❌ Error editing log: {str(e)}")

    #----------------- TRIBE DETECTOR COMMAND-----------
    @bot.command(name='detect')
    async def detect_tribes(ctx, map_name: str = None, game_size: str = None, max_points: int = None, *enemy_scores):
        """
        Detect opponent tribes with interactive guidance. Usage:
        %detect pangea 3v3 12 515 620 630
        %detect archi 2v2 10 515 620
        Or just %detect for interactive mode
        """
        # Check if user has Spellkeeper role
        spellkeeper_role = discord.utils.get(ctx.author.roles, name="Spellkeeper")
        if not spellkeeper_role:
            await ctx.send("❌ You need the **Spellkeeper** role to use this command!")
            return
        
        # Interactive mode if no arguments provided
        if map_name is None:
            await start_interactive_detect(ctx)
            return
        
        # Otherwise proceed with normal command processing
        # ... (your existing detect logic) ...
    
    async def start_interactive_detect(ctx):
        """Interactive tribe detection with native Discord buttons"""
        # Step 1: Map selection
        embed = discord.Embed(
            title="🔍 Tribe Detection - Step 1/4",
            description="Select the map type:",
            color=0x00ff00
        )
        embed.add_field(name="Pangea", value="Island surrounded by water", inline=True)
        embed.add_field(name="Archi", value="T-Sims' favorite", inline=True)
        embed.add_field(name="Conti", value="Continents with a large ocean", inline=True)
        embed.add_field(name="Dry", value="No water", inline=True)
        embed.add_field(name="Lakes", value="Random lakes", inline=True)
        
        view = MapSelectView(ctx)
        message = await ctx.send(embed=embed, view=view)
        
        # Wait for map selection
        await view.wait()
        
        if view.value is False or view.map_name is None:
            await message.edit(content="❌ Tribe detection cancelled.", embed=None, view=None)
            return
        
        map_name = view.map_name
        
        # Step 2: Game size selection
        embed = discord.Embed(
            title="🔍 Tribe Detection - Step 2/4",
            description=f"**Map:** {map_name.title()}\n\nSelect the game size:",
            color=0x00ff00
        )
        
        size_view = GameSizeView(ctx)
        await message.edit(embed=embed, view=size_view)
        
        # Wait for game size selection
        await size_view.wait()
        
        if size_view.value is False or size_view.game_size is None:
            await message.edit(content="❌ Tribe detection cancelled.", embed=None, view=None)
            return
        
        game_size = size_view.game_size
        expected_scores = 2 if game_size == "2v2" else 3
        
        # Step 3: Get max points
        embed = discord.Embed(
            title="🔍 Tribe Detection - Step 3/4",
            description=f"**Map:** {map_name.title()}\n**Game Size:** {game_size.upper()}\n\nEnter the maximum tribe points allowed:",
            color=0x00ff00
        )
        
        await message.edit(embed=embed, view=None)
        
        # Wait for max points input
        try:
            points_msg = await bot.wait_for(
                "message",
                check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id,
                timeout=60.0
            )
            
            try:
                max_points = int(points_msg.content.strip())
                if max_points < 1 or max_points > 20:
                    await ctx.send("❌ Max points must be between 1 and 20. Please try again.")
                    return
            except ValueError:
                await ctx.send("❌ Max points must be a number. Please try again.")
                return
            
            # Step 4: Get enemy scores
            embed = discord.Embed(
                title="🔍 Tribe Detection - Step 4/4",
                description=f"**Map:** {map_name.title()}\n**Game Size:** {game_size.upper()}\n**Max Points:** {max_points}\n\nEnter the enemy starting scores (separated by spaces):",
                color=0x00ff00
            )
            embed.add_field(
                name="Example", 
                value="515 620 630" if game_size == "3v3" else "515 620",
                inline=False
            )
            embed.add_field(
                name="Valid Scores", 
                value="415, 465, 515, 520, 530, 615, 620, 630, 730\n(Note: Corner spawns = score -5)",
                inline=False
            )
            
            await message.edit(embed=embed, view=None)
            
            # Wait for scores input
            try:
                scores_msg = await bot.wait_for(
                    "message",
                    check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id,
                    timeout=120.0
                )
                
                # Parse scores
                scores_text = scores_msg.content.strip()
                enemy_scores = []
                for score in scores_text.split():
                    try:
                        enemy_scores.append(int(score))
                    except ValueError:
                        await ctx.send(f"❌ Invalid score: {score}. Scores must be numbers.")
                        return
                
                # Validate score count
                if len(enemy_scores) != expected_scores:
                    await ctx.send(f"❌ {game_size} requires {expected_scores} enemy scores, got {len(enemy_scores)}")
                    return
                
                # Validate scores are within possible range
                valid_scores = [415, 465, 515, 520, 530, 615, 620, 630, 730, 410, 460, 510, 515, 525, 610, 615, 625, 725]
                for score in enemy_scores:
                    if score not in valid_scores:
                        await ctx.send(f"❌ Invalid score: {score}. Valid scores: 415, 465, 515, 520, 530, 615, 620, 630, 730 (corner spawns: -5)")
                        return
                
                # Process the detection
                await message.edit(content="🔍 Analyzing possible tribe combinations...", embed=None, view=None)
                
                # Call your existing detection function
                result = detect_tribes_for_discord(
                    map_name, game_size, max_points, enemy_scores,
                    consider_corner_spawns=True,
                    min_points_threshold=2
                )
                
                # Clean up input messages
                try:
                    await points_msg.delete()
                    await scores_msg.delete()
                except:
                    pass
                
                # Send results
                if len(result) > 2000:
                    parts = [result[i:i+2000] for i in range(0, len(result), 2000)]
                    for part in parts:
                        await ctx.send(part)
                        await asyncio.sleep(1)
                else:
                    await ctx.send(result)
                    
            except asyncio.TimeoutError:
                await message.edit(content="⏰ Score input timed out. Please try `%detect` again.", embed=None, view=None)
                
        except asyncio.TimeoutError:
            await message.edit(content="⏰ Points input timed out. Please try `%detect` again.", embed=None, view=None)

    
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
    @commands.check(can_use_log_commands)
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
