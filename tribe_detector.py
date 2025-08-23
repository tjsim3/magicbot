# %%
# Battle of Polytopia Tribe Detection Bot

##This notebook helps determine possible tribe combinations for opponents based on their starting scores and tribe point constraints in Battle of Polytopia.

## How it works:
#1. Each tribe has a specific starting score
#2. Each tribe has different point values depending on map type and game size
#3. Teams cannot have duplicate tribes
#4. Total tribe points cannot exceed the decided limit

## Supported Configurations:
##- **Map Types**: Pangea, Archi, Conti, Dry, Lakes
##- **Game Sizes**: 2v2, 3v3


# %%
from itertools import combinations

# Tribe starting scores (same for all map types and game sizes)
TRIBE_STARTING_SCORES = {
    'aquarion': 415,
    'luxidoor': 465,
    'xinxi': 515,
    'imperius': 515,
    'bardur': 515,
    'elyrion': 515,
    'kickoo': 515,
    'oumaji': 520,
    'polaris': 530,
    'zebasi': 615,
    'yaddak': 615,
    'aimo': 615,
    'hoodrick': 620,
    'quetzali': 620,
    'cymanti': 630,
    'vengir': 730
}

# Tribe points for different map types and game sizes
TRIBE_POINTS_CONFIG = {
    'pangea_2v2': {
        'cymanti': 5, 'elyrion': 5,
        'imperius': 4, 'zebasi': 4, 'bardur': 4,
        'kickoo': 3, 'oumaji': 3, 'quetzali': 3, 'aimo': 3,
        'luxidoor': 2, 'yaddak': 2, 'vengir': 2, 'aquarion': 2,
        'xinxi': 1, 'polaris': 1, 'hoodrick': 1
    },
    'pangea_3v3': {
        'elyrion': 6,
        'cymanti': 5,
        'zebasi': 4, 'bardur': 4, 'imperius': 4,
        'kickoo': 3, 'oumaji': 3, 'aimo': 3,
        'luxidoor': 2, 'vengir': 2, 'aquarion': 2, 'yaddak': 2, 'hoodrick': 2,
        'xinxi': 1, 'quetzali': 1
    },
    'archi_2v2': {
        'polaris': 7,
        'kickoo': 5, 'aquarion': 5,
        'imperius': 4, 'bardur': 4, 'zebasi': 4, 'cymanti': 4,
        'quetzali': 3, 'elyrion': 3, 'aimo': 3,
        'luxidoor': 2, 'oumaji': 2,
        'vengir': 1, 'hoodrick': 1, 'xinxi': 1, 'yaddak': 1
    },
    'archi_3v3': {
        'aquarion': 5, 'kickoo': 5,
        'bardur': 4, 'zebasi': 4, 'cymanti': 4, 'imperius': 4,
        'elyrion': 3, 'aimo': 3,
        'luxidoor': 2, 'quetzali': 2, 'oumaji': 2,
        'vengir': 1, 'hoodrick': 1, 'xinxi': 1, 'yaddak': 1
    },
    'dry_2v2': {
        'cymanti': 5, 'elyrion': 5, 'imperius': 5,
        'zebasi': 4, 'bardur': 4,
        'oumaji': 3, 'kickoo': 3, 'quetzali': 3, 'aimo': 3,
        'luxidoor': 2, 'yaddak': 2, 'hoodrick': 2, 'xinxi': 2,
        'vengir': 1, 'polaris': 1, 'aquarion': 1
    },
    'dry_3v3': {
        'elyrion': 6,
        'cymanti': 5,
        'zebasi': 4, 'bardur': 4, 'imperius': 4,
        'oumaji': 3, 'kickoo': 3, 'aimo': 3,
        'luxidoor': 2, 'hoodrick': 2, 'vengir': 2, 'yaddak': 2,
        'xinxi': 1, 'quetzali': 1, 'aquarion': 1
    },
    'conti_2v2': {
        'polaris': 6, 'aquarion': 6,
        'elyrion': 5,
        'cymanti': 4, 'imperius': 4,
        'kickoo': 3, 'zebasi': 3, 'bardur': 3, 'oumaji': 3,
        'aimo': 2, 'quetzali': 2, 'vengir': 2, 'yaddak': 2,
        'xinxi': 1, 'hoodrick': 1, 'luxidoor': 1
    },
    'conti_3v3': {
        'elyrion': 6,
        'aquarion': 5,
        'cymanti': 4,
        'kickoo': 3, 'zebasi': 3, 'bardur': 3, 'imperius': 3,
        'oumaji': 2, 'aimo': 2, 'vengir': 2, 'yaddak': 2,
        'luxidoor': 1, 'xinxi': 1, 'hoodrick': 1, 'quetzali': 1
    },
    'lakes_2v2': {
        'elyrion': 5, 'cymanti': 5, 'imperius': 5,
        'kickoo': 4, 'bardur': 4, 'zebasi': 4,
        'polaris': 3, 'quetzali': 3, 'oumaji': 3, 'aimo': 3, 'aquarion': 3,
        'luxidoor': 2, 'yaddak': 2,
        'vengir': 1, 'xinxi': 1, 'hoodrick': 1
    },
    'lakes_3v3': {
        'elyrion': 6,
        'cymanti': 5,
        'kickoo': 4, 'zebasi': 4, 'bardur': 4, 'imperius': 4,
        'aimo': 3, 'oumaji': 3, 'aquarion': 3,
        'hoodrick': 2, 'yaddak': 2, 'luxidoor': 2,
        'vengir': 1, 'quetzali': 1, 'xinxi': 1
    }
}

# Create reverse mapping from scores to possible tribes
SCORE_TO_TRIBES = {}
for tribe, score in TRIBE_STARTING_SCORES.items():
    if score not in SCORE_TO_TRIBES:
        SCORE_TO_TRIBES[score] = []
    SCORE_TO_TRIBES[score].append(tribe)

print("Tribe Starting Scores:")
for score in sorted(SCORE_TO_TRIBES.keys()):
    tribes = ', '.join(SCORE_TO_TRIBES[score])
    print(f"{score}: {tribes}")

print("\nSupported configurations:")
for config in TRIBE_POINTS_CONFIG.keys():
    map_type, game_size = config.split('_')
    print(f"- {map_type.title()} {game_size.upper()}")


# %%
def get_possible_tribes_from_score(score):
    """Get all possible tribes that could have the given starting score."""
    return SCORE_TO_TRIBES.get(score, [])

def get_tribe_points_for_config(map_type, game_size):
    """Get the tribe points configuration for a specific map type and game size."""
    config_key = f"{map_type.lower()}_{game_size.lower()}"
    if config_key not in TRIBE_POINTS_CONFIG:
        raise ValueError(f"Unsupported configuration: {map_type} {game_size}")
    return TRIBE_POINTS_CONFIG[config_key]

def calculate_tribe_combinations(opponent_scores, max_tribe_points, map_type, game_size, consider_corner_spawns=True, min_points_threshold=2):
    """
    Calculate tribe combinations with additional filtering options.
    
    Args:
        opponent_scores: List of scores observed from opponents
        max_tribe_points: Maximum total tribe points allowed
        map_type: Map type (pangea, archi, conti, dry, lakes)
        game_size: Game size (2v2, 3v3)
        consider_corner_spawns: Whether to account for corner spawns (-5 score)
        min_points_threshold: Only show results within X points of max (e.g., 2 means max-2 or higher)
    """
    # Get the correct tribe points configuration
    tribe_points = get_tribe_points_for_config(map_type, game_size)
    
    # Get all possible tribes for each score (with corner spawn consideration)
    possible_tribes_per_score = []
    for score in opponent_scores:
        tribes = get_possible_tribes_from_score(score, consider_corner_spawns)
        if not tribes:
            return []
        possible_tribes_per_score.append(tribes)
    
    # Generate all possible combinations
    valid_combinations = []
    seen_combinations = set()  # To track duplicate combinations
    
    def generate_combinations(index, current_combination, used_tribes):
        if index == len(possible_tribes_per_score):
            # Sort the combination to identify duplicates regardless of order
            sorted_combo = tuple(sorted(current_combination))
            
            # Skip duplicate combinations (same tribes in different order)
            if sorted_combo in seen_combinations:
                return
            
            # Check if this combination is valid
            total_points = sum(tribe_points.get(tribe, 0) for tribe in current_combination)
            
            # Apply minimum points threshold (only show results close to max)
            if total_points <= max_tribe_points and total_points >= (max_tribe_points - min_points_threshold):
                valid_combinations.append((current_combination.copy(), total_points))
                seen_combinations.add(sorted_combo)
            return
        
        # Try each possible tribe for the current score
        for tribe in possible_tribes_per_score[index]:
            if tribe not in used_tribes:  # No duplicate tribes allowed
                current_combination.append(tribe)
                used_tribes.add(tribe)
                generate_combinations(index + 1, current_combination, used_tribes)
                current_combination.pop()
                used_tribes.remove(tribe)
    
    generate_combinations(0, [], set())
    
    # Sort by total points (descending)
    valid_combinations.sort(key=lambda x: x[1], reverse=True)
    
    return valid_combinations

def display_tribe_points_for_config(map_type, game_size):
    """Display the tribe points for a specific configuration."""
    try:
        tribe_points = get_tribe_points_for_config(map_type, game_size)
        print(f"\n{map_type.title()} {game_size.upper()} Tribe Points:")
        
        # Group by points and sort
        points_to_tribes = {}
        for tribe, points in tribe_points.items():
            if points not in points_to_tribes:
                points_to_tribes[points] = []
            points_to_tribes[points].append(tribe)
        
        for points in sorted(points_to_tribes.keys(), reverse=True):
            tribes = ', '.join(sorted(points_to_tribes[points]))
            print(f"{points}: {tribes}")
            
    except ValueError as e:
        print(f"Error: {e}")

def apply_corner_spawn_adjustment(score):
    """Adjust score for corner spawn (-5 points)"""
    return score - 5

def get_possible_tribes_from_score(score, consider_corner_spawns=True):
    """Get all possible tribes that could have the given starting score, with corner spawn option."""
    possible_tribes = SCORE_TO_TRIBES.get(score, [])
    
    if consider_corner_spawns:
        # Also check for tribes that could be in corner spawns (score + 5)
        corner_adjusted_score = score + 5
        corner_tribes = SCORE_TO_TRIBES.get(corner_adjusted_score, [])
        possible_tribes.extend(corner_tribes)
    
    return list(set(possible_tribes))  # Remove duplicates


        # ===== DISCORD BOT WRAPPER FUNCTION =====
# ADD THIS AFTER ALL THE OTHER FUNCTIONS BUT BEFORE THE TEST CODE

def detect_tribes_for_discord(map_name: str, game_size: str, max_tribe_points: int, enemy_scores: list, consider_corner_spawns=True, min_points_threshold=2):
    """
    Wrapper function for Discord bot usage with enhanced filtering
    """
    map_type = map_name.lower()
    game_size = game_size.lower()
    
    try:
        # Get tribe points configuration
        tribe_points = get_tribe_points_for_config(map_type, game_size)
        
        # Calculate combinations with filtering options
        combinations = calculate_tribe_combinations(
            enemy_scores, max_tribe_points, map_type, game_size, 
            consider_corner_spawns, min_points_threshold
        )
        
        if not combinations:
            return "❌ No valid tribe combinations found with the given constraints!"
        
        # Format results for Discord
        result = []
        result.append(f"**{map_name.title()} {game_size.upper()} Tribe Detection**")
        result.append(f"Enemy scores: {enemy_scores}")
        result.append(f"Max tribe points: {max_tribe_points}")
        if consider_corner_spawns:
            result.append(f"*Considering corner spawns (-5 score adjustment)*")
        result.append(f"*Showing only combinations within {min_points_threshold} points of max*")
        result.append("")
        
        # Show top combinations
        for i, (combo, total_points) in enumerate(combinations[:8], 1):
            tribe_details = []
            for j, tribe in enumerate(combo):
                points = tribe_points.get(tribe, 0)
                base_score = TRIBE_STARTING_SCORES.get(tribe, "?")
                
                # CORRECT corner spawn detection:
                observed_score = enemy_scores[j]
                is_corner = (observed_score == base_score - 5)
                corner_note = " (corner spawn)" if is_corner else ""
                
                tribe_details.append(f"{tribe.title()}{corner_note} ({points} points)")
            
            result.append(f"**Possibility {i}:** {', '.join(tribe_details)}")
            result.append(f"   Total: {total_points} points")
            
            # Add explanation for 515-score tribes when corner spawns are possible
            if 510 in enemy_scores or 515 in enemy_scores:
                five_fifteen_tribes = []
                for j, tribe in enumerate(combo):
                    if tribe in ['xinxi', 'imperius', 'bardur', 'elyrion', 'kickoo']:
                        observed_score = enemy_scores[j]
                        if observed_score == 510:
                            five_fifteen_tribes.append(f"{tribe.title()} (corner)")
                        elif observed_score == 515:
                            five_fifteen_tribes.append(f"{tribe.title()} (normal)")
                
                if five_fifteen_tribes:
                    result.append(f"   Note: {', '.join(five_fifteen_tribes)}")
            
            result.append("")
        
        if len(combinations) > 8:
            result.append(f"*... and {len(combinations) - 8} more possibilities*")
        
        return "\n".join(result)
        
    except ValueError as e:
        return f"❌ Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

# ===== END OF DISCORD WRAPPER =====

# Test the functions
print("Functions defined successfully!")


# %%



# %%
# ===== INPUT YOUR MATCH DATA HERE =====

# Match configuration
map_type = "pangea"        # Options: pangea, archi, conti, dry, lakes
game_size = "3v3"          # Options: 2v2, 3v3

# Opponent data
opponent_scores = [515, 620, 630]  # Replace with actual opponent scores
max_tribe_points = 12              # Replace with your agreed tribe point limit
opponent_usernames = ["Player1", "Player2", "Player3"]  # Optional: replace with actual usernames

# ===== ANALYSIS =====

print("=== Match Analysis ===")
print(f"Configuration: {map_type.title()} {game_size.upper()}")
print(f"Opponent scores: {opponent_scores}")
print(f"Maximum tribe points allowed: {max_tribe_points}")
if opponent_usernames:
    print(f"Opponent usernames: {opponent_usernames}")

# Show the tribe points for this configuration
display_tribe_points_for_config(map_type, game_size)

print("\n" + "="*50)

# Analyze the combinations
try:
    combinations = calculate_tribe_combinations(opponent_scores, max_tribe_points, map_type, game_size)
    
    if combinations:
        print(f"\nFound {len(combinations)} possible tribe combinations for your opponents:")
        print("(Sorted by likelihood - most likely combinations first based on maximizing tribe strength)")
        print()
        
        for i, (combo, total_points) in enumerate(combinations, 1):
            print(f"Possibility {i}: {', '.join(combo)} (Total: {total_points} points)")
            
            # Show detailed breakdown
            print("   Detailed breakdown:")
            tribe_points = get_tribe_points_for_config(map_type, game_size)
            for j, tribe in enumerate(combo):
                score = opponent_scores[j]
                points = tribe_points.get(tribe, 0)
                username = opponent_usernames[j] if j < len(opponent_usernames) else f"Opponent{j+1}"
                print(f"   - {username}: {score} → {tribe} ({points} points)")
            print()
    else:
        print("\nNo valid combinations found with the given constraints!")
        
except ValueError as e:
    print(f"\nError: {e}")
    print("Please check your map_type and game_size values.")


# %%
## Quick Reference

### Map Types and Game Sizes:
###- **Pangea**: 2v2, 3v3
###- **Archi**: 2v2, 3v3  
###- **Conti**: 2v2, 3v3
###- **Dry**: 2v2, 3v3
###- **Lakes**: 2v2, 3v3

### Tribe Starting Scores:
###- **415**: Aquarion
###- **465**: Luxidoor
###- **515**: Xinxi, Imperius, Bardur, Elyrion, Kickoo
###- **520**: Oumaji
###- **530**: Polaris
###- **615**: Zebasi, Yaddak, Aimo
###- **620**: Hoodrick, Quetzali
###- **630**: Cymanti
###- **730**: Vengir

### How to Use:
###1. Observe your opponents' starting scores in the game
###2. Note the map type and game size for your match
###3. Note the maximum tribe points agreed upon for your match
###4. Edit the values in the "Interactive Input Section" above:
###   - `map_type`: Set to your map (pangea, archi, conti, dry, lakes)
###   - `game_size`: Set to your game size (2v2, 3v3)
###   - `opponent_scores`: List of observed scores
###   - `max_tribe_points`: Your agreed point limit
###   - `opponent_usernames`: Optional usernames for clarity
###5. Run the cell to see all possible tribe combinations your opponents could be using
###6. Use this information to plan your strategy!

###The bot will show you the tribe point values for your specific configuration and then list all valid combinations sorted by likelihood (highest points first).


# %%



# %%



# %%



# %%






