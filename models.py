import os
import json
import sqlite3
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, DateTime, BigInteger, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# Use declarative base for SQLAlchemy
Base = declarative_base()

class Game(Base):
    __tablename__ = 'games'
    
    game_id = Column(String(20), primary_key=True)  # 6-digit game ID
    config = Column(String(10), nullable=False)     # '2v2' or '3v3'
    players = Column(Text, nullable=False)          # JSON string of player list
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = Column(BigInteger, nullable=False) # Discord user ID

class GameLog(Base):
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(String(20), nullable=False)    # 6-digit game ID
    turn = Column(Integer, nullable=False)          # Turn number (starts at 0)
    scores = Column(Text, nullable=False)           # JSON string of scores
    notes = Column(Text, default="No notes")
    logged_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class CompletedGame(Base):
    __tablename__ = 'completed_games'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(String(20))
    result = Column(String(10))  # 'win' or 'loss'
    map_name = Column(String(20))
    tribe_points = Column(Integer)
    players = Column(Text)  # JSON: {player_name: tribe_name}
    enemy_team = Column(String(200))  # Team name or player list
    completed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(Text)

class PlayerStats(Base):
    __tablename__ = 'player_stats'
    
    player_name = Column(String(50), primary_key=True)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    incomplete = Column(Integer, default=0)
    favorite_tribes = Column(Text, default='{}')  # JSON: {tribe: count}
    favorite_maps = Column(Text, default='{}')    # JSON: {map: count}
    average_points = Column(Integer, default=0)
    total_games = Column(Integer, default=0)
    win_rate = Column(Integer, default=0)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class OngoingGame(Base):
    __tablename__ = 'ongoing_games'
    
    game_id = Column(String(20), primary_key=True)
    players = Column(Text)  # JSON list of player names
    map_name = Column(String(20))
    tribe_points = Column(Integer)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default='active')  # 'active', 'completed'


# Database setup
def get_database_url():
    # Force SQLite for now
    os.makedirs('data', exist_ok=True)
    return 'sqlite:///data/gamelogs.db'

# Create engine and session
engine = create_engine(
    get_database_url(),
    pool_recycle=300,
    pool_pre_ping=True,
    connect_args={'check_same_thread': False} if 'sqlite' in get_database_url() else {}
)

Session = scoped_session(sessionmaker(bind=engine))
db_session = Session()

def init_database():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(engine)
        print("✅ Game log database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

# Helper functions for game logs
def get_db_connection():
    """Get a raw SQLite connection for compatibility with existing code"""
    if 'sqlite' in get_database_url():
        # Extract the SQLite file path
        db_path = get_database_url().replace('sqlite:///', '')
        return sqlite3.connect(db_path)
    else:
        # For other databases, we'd need a different approach
        # This is a simple fallback that might need adjustment
        import tempfile
        return sqlite3.connect(tempfile.NamedTemporaryFile(delete=False).name)

def game_exists(game_id):
    """Check if a game exists"""
    try:
        game = db_session.query(Game).filter_by(game_id=game_id).first()
        return game is not None
    except Exception as e:
        print(f"❌ Error checking if game exists: {e}")
        return False

def get_game(game_id):
    """Get a game by ID"""
    try:
        return db_session.query(Game).filter_by(game_id=game_id).first()
    except Exception as e:
        print(f"❌ Error getting game: {e}")
        return None

def get_game_logs(game_id, start_turn=None, end_turn=None):
    """Get logs for a game, optionally filtered by turn range"""
    try:
        query = db_session.query(GameLog).filter_by(game_id=game_id)
        
        if start_turn is not None and end_turn is not None:
            query = query.filter(GameLog.turn.between(start_turn, end_turn))
        elif start_turn is not None:
            query = query.filter(GameLog.turn == start_turn)
            
        return query.order_by(GameLog.turn).all()
    except Exception as e:
        print(f"❌ Error getting game logs: {e}")
        return []

def get_max_turn(game_id):
    """Get the maximum turn number for a game"""
    try:
        max_turn = db_session.query(GameLog.turn).filter_by(game_id=game_id).order_by(GameLog.turn.desc()).first()
        return max_turn[0] if max_turn else -1
    except Exception as e:
        print(f"❌ Error getting max turn: {e}")
        return -1

# Initialize database on import
try:
    init_database()
    print("✅ Game log database module loaded successfully!")
except Exception as e:
    print(f"⚠️ Database module loaded with warning: {e}")

# Simple function to replace the Flask app creation
def create_app():
    """Compatibility function for existing code"""
    print("✅ Database is already initialized!")
    return type('SimpleApp', (), {})()
