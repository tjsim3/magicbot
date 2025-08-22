import os
import sqlite3
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session

# Use declarative base for SQLAlchemy
Base = declarative_base()

class DuelPlayer(Base):
    __tablename__ = 'duel_players'
    
    id = Column(BigInteger, primary_key=True)  # Discord user ID
    username = Column(String(100), nullable=False)
    total_wins = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)
    total_draws = Column(Integer, default=0)
    games_played = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_active = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    challenger_duels = relationship("ActiveDuel", foreign_keys="ActiveDuel.challenger_id", back_populates="challenger")
    opponent_duels = relationship("ActiveDuel", foreign_keys="ActiveDuel.opponent_id", back_populates="opponent")
    
    def __repr__(self):
        return f'<DuelPlayer {self.username}>'


class ActiveDuel(Base):
    __tablename__ = 'active_duels'
    
    id = Column(Integer, primary_key=True)
    challenger_id = Column(BigInteger, ForeignKey('duel_players.id'), nullable=False)
    opponent_id = Column(BigInteger, ForeignKey('duel_players.id'), nullable=False)
    
    # HP System
    challenger_hp = Column(Integer, default=3)
    opponent_hp = Column(Integer, default=3)
    
    # Turn System
    current_turn = Column(String(20))  # 'challenger' or 'opponent'
    turn_deadline = Column(DateTime)  # 12-hour deadline for current turn
    
    # Current Turn Spells
    challenger_spell = Column(String(50), nullable=True)
    opponent_spell = Column(String(50), nullable=True)
    
    # Game Status
    status = Column(String(20), default='active')  # 'active', 'finished', 'expired'
    winner_id = Column(BigInteger, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_action = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    challenger = relationship("DuelPlayer", foreign_keys=[challenger_id], back_populates="challenger_duels")
    opponent = relationship("DuelPlayer", foreign_keys=[opponent_id], back_populates="opponent_duels")
    
    def __repr__(self):
        return f'<ActiveDuel {self.challenger.username if self.challenger else "Unknown"} vs {self.opponent.username if self.opponent else "Unknown"}>'


class DuelHistory(Base):
    __tablename__ = 'duel_history'
    
    id = Column(Integer, primary_key=True)
    challenger_id = Column(BigInteger, ForeignKey('duel_players.id'), nullable=False)
    opponent_id = Column(BigInteger, ForeignKey('duel_players.id'), nullable=False)
    winner_id = Column(BigInteger, ForeignKey('duel_players.id'), nullable=True)
    
    # Final Stats
    challenger_hp_final = Column(Integer)
    opponent_hp_final = Column(Integer)
    total_rounds = Column(Integer)
    duration_minutes = Column(Integer)
    
    # Game Result
    result = Column(String(20))  # 'challenger_win', 'opponent_win', 'draw', 'timeout'
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    challenger = relationship("DuelPlayer", foreign_keys=[challenger_id])
    opponent = relationship("DuelPlayer", foreign_keys=[opponent_id])
    winner = relationship("DuelPlayer", foreign_keys=[winner_id])
    
    def __repr__(self):
        return f'<DuelHistory {self.result}>'


# Database setup without Flask
def get_database_url():
    """Get database URL from environment or use SQLite"""
    if os.environ.get('DATABASE_URL'):
        return os.environ.get('DATABASE_URL')
    else:
        # Use SQLite as fallback
        os.makedirs('data', exist_ok=True)
        return 'sqlite:///data/duels.db'

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
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def get_or_create_player(discord_id, username):
    """Get or create a player in the database"""
    try:
        player = db_session.query(DuelPlayer).filter_by(id=discord_id).first()
        if not player:
            player = DuelPlayer(id=discord_id, username=username)
            db_session.add(player)
            db_session.commit()
        return player
    except Exception as e:
        print(f"❌ Error getting/creating player: {e}")
        # Create a simple player object without database if needed
        return type('SimplePlayer', (), {'id': discord_id, 'username': username})()

def cleanup_expired_duels():
    """Clean up duels where turn deadline has passed"""
    try:
        now = datetime.now(timezone.utc)
        expired_duels = db_session.query(ActiveDuel).filter(
            ActiveDuel.turn_deadline < now,
            ActiveDuel.status == 'active'
        ).all()
        
        for duel in expired_duels:
            duel.status = 'expired'
        
        db_session.commit()
        return len(expired_duels)
    except Exception as e:
        print(f"❌ Error cleaning up expired duels: {e}")
        return 0

def get_player_stats(discord_id):
    """Get player statistics"""
    try:
        player = db_session.query(DuelPlayer).filter_by(id=discord_id).first()
        if not player:
            return None
        
        if player.games_played > 0:
            win_rate = (player.total_wins / player.games_played) * 100
        else:
            win_rate = 0
        
        return {
            'player': player,
            'win_rate': win_rate
        }
    except Exception as e:
        print(f"❌ Error getting player stats: {e}")
        return None

# Initialize database on import
try:
    init_database()
    print("✅ Database module loaded successfully!")
except Exception as e:
    print(f"⚠️ Database module loaded with warning: {e}")

# Simple function to replace the Flask app creation
def create_app():
    """Compatibility function for existing code"""
    print("✅ Database is already initialized!")
    return type('SimpleApp', (), {})()
