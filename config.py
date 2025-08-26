# config.py
import os

# Channel IDs (set these in your Discord server)
VICTORY_CHANNEL_ID = int(os.getenv('VICTORY_CHANNEL_ID', 0))
LEADERBOARD_CHANNEL_ID = int(os.getenv('LEADERBOARD_CHANNEL_ID', 0))
LEADER_ROLE_NAMES = ['Leader', 'Captain', 'Co-Leader']  # Adjust as needed

# Team configuration
TEAM_NAMES = {
    'enemy_team_1': 'The Dragons',
    'enemy_team_2': 'Ocean Masters', 
    'enemy_team_3': 'Mountain Kings',
    # Add more team mappings as needed
}

def is_leader(member):
    """Check if a member has leader role"""
    return any(role.name in LEADER_ROLE_NAMES for role in member.roles)
