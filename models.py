import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

class DuelPlayer(db.Model):
    __tablename__ = 'duel_players'
    
    id = db.Column(db.BigInteger, primary_key=True)  # Discord user ID
    username = db.Column(db.String(100), nullable=False)
    total_wins = db.Column(db.Integer, default=0)
    total_losses = db.Column(db.Integer, default=0)
    total_draws = db.Column(db.Integer, default=0)
    games_played = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DuelPlayer {self.username}>'


class ActiveDuel(db.Model):
    __tablename__ = 'active_duels'
    
    id = db.Column(db.Integer, primary_key=True)
    challenger_id = db.Column(db.BigInteger, db.ForeignKey('duel_players.id'), nullable=False)
    opponent_id = db.Column(db.BigInteger, db.ForeignKey('duel_players.id'), nullable=False)
    
    # HP System
    challenger_hp = db.Column(db.Integer, default=3)
    opponent_hp = db.Column(db.Integer, default=3)
    
    # Turn System
    current_turn = db.Column(db.String(20))  # 'challenger' or 'opponent'
    turn_deadline = db.Column(db.DateTime)  # 12-hour deadline for current turn
    
    # Current Turn Spells
    challenger_spell = db.Column(db.String(50), nullable=True)
    opponent_spell = db.Column(db.String(50), nullable=True)
    
    # Game Status
    status = db.Column(db.String(20), default='active')  # 'active', 'finished', 'expired'
    winner_id = db.Column(db.BigInteger, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_action = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    challenger = db.relationship('DuelPlayer', foreign_keys=[challenger_id], backref='challenger_duels')
    opponent = db.relationship('DuelPlayer', foreign_keys=[opponent_id], backref='opponent_duels')
    winner = db.relationship('DuelPlayer', foreign_keys=[winner_id])
    
    def __repr__(self):
        return f'<ActiveDuel {self.challenger.username} vs {self.opponent.username}>'


class DuelHistory(db.Model):
    __tablename__ = 'duel_history'
    
    id = db.Column(db.Integer, primary_key=True)
    challenger_id = db.Column(db.BigInteger, db.ForeignKey('duel_players.id'), nullable=False)
    opponent_id = db.Column(db.BigInteger, db.ForeignKey('duel_players.id'), nullable=False)
    winner_id = db.Column(db.BigInteger, db.ForeignKey('duel_players.id'), nullable=True)
    
    # Final Stats
    challenger_hp_final = db.Column(db.Integer)
    opponent_hp_final = db.Column(db.Integer)
    total_rounds = db.Column(db.Integer)
    duration_minutes = db.Column(db.Integer)
    
    # Removed ELO system per user request
    
    # Game Result
    result = db.Column(db.String(20))  # 'challenger_win', 'opponent_win', 'draw', 'timeout'
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    challenger = db.relationship('DuelPlayer', foreign_keys=[challenger_id])
    opponent = db.relationship('DuelPlayer', foreign_keys=[opponent_id])
    winner = db.relationship('DuelPlayer', foreign_keys=[winner_id])
    
    def __repr__(self):
        return f'<DuelHistory {self.challenger.username} vs {self.opponent.username} - {self.result}>'


# Initialize Flask app and database
def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a secret key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    return app