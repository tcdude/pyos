"""
Data collection and preparation.
"""

import datetime
from typing import Optional, Tuple, Union

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import true
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine
from loguru import logger

__author__ = 'Tiziano Bettio'
__copyright__ = """
Copyright (c) 2020 Tiziano Bettio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
__license__ = 'MIT'
__version__ = '0.3'

Base = declarative_base()  # pylint: disable=invalid-name


# pylint: disable=too-few-public-methods
class Game(Base):
    """"Holds information about individual games."""
    __tablename__ = 'game'
    id = Column(Integer, primary_key=True)
    seed = Column(Integer, nullable=False)
    draw = Column(Integer, nullable=False)
    windeal = Column(Boolean, nullable=False)
    daydeal = Column(Boolean, nullable=False)
    challenge = Column(Integer, nullable=True, default=-1)
    solution = Column(Boolean, default=False)  # Solution playback requested.
    attempts = relationship('Attempt', back_populates='game')

    def __repr__(self):
        return f'Game(id={self.id}, seed={self.seed}, draw={self.draw}, ' \
               f'windeal={self.windeal}, daydeal={self.daydeal}, ' \
               f'solution={self.solution})'


class Attempt(Base):
    """"Holds information about individual attempts."""
    __tablename__ = 'attempt'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('game.id'))
    game = relationship("Game", back_populates="attempts")
    solved = Column(Boolean, default=False)
    duration = Column(Float, default=-1.0)
    moves = Column(Integer, default=-1)
    invalid = Column(Integer, default=0)
    undo = Column(Integer, default=0)
    points = Column(Integer, default=-1)
    bonus = Column(Integer, default=-1)
    total = Column(Integer, default=-1)
    first_move = Column(DateTime)
    last_move = Column(DateTime)

    def __repr__(self):
        return f'Attempt(id={self.id}, game_id={self.game_id}, ' \
               f'solved={self.solved}, duration={self.duration}, ' \
               f'moves={self.moves}, invalid={self.invalid}, ' \
               f'undo={self.undo}, points={self.points}, bonus={self.bonus}, ' \
               f'total={self.total}, first_move={self.first_move}, ' \
               f'last_move={self.last_move})'


class Session(Base):
    """Holds information about how long the app is being used."""
    __tablename__ = 'session'
    id = Column(Integer, primary_key=True)
    start = Column(DateTime)
    start_local = Column(DateTime)
    end = Column(DateTime)

    def __repr__(self):
        return f'Session(id={self.id}, start={self.start}, ' \
               f'start_local={self.start_local}, end={self.end})'
# pylint: enable=too-few-public-methods


AllTables = Union[Game, Attempt]


class Stats:
    """
    Handles everything related to storing and retrieving stats data.

    Args:
        db_file: The sqlite file to load/store data in.
    """
    def __init__(self, db_file: str) -> None:
        engine = create_engine(f'sqlite:///{db_file}')
        Base.metadata.create_all(engine)
        Base.metadata.bind = engine
        self._session = sessionmaker(bind=engine)()
        self._check_migrate(engine)
        logger.debug('Stats initialized')

    def new_deal(self, seed: int, draw: int, windeal: bool,
                 daydeal: bool = False, challenge: int = -1) -> int:
        """Makes sure a game with the given information exists in the db."""
        # pylint: disable=too-many-arguments
        res = self._session.query(Game)\
            .filter(Game.seed == seed, Game.draw == draw,
                    Game.windeal == windeal, Game.daydeal == daydeal,
                    Game.challenge == challenge).first()
        if res is not None:
            logger.debug(f'existing deal {res.id}')
            return res.id
        game = Game(seed=seed, draw=draw, windeal=windeal, daydeal=daydeal,
                    challenge=challenge)
        self._session.add(game)
        self._session.commit()
        logger.debug(f'new deal {game.id}')
        return game.id

    def new_attempt(self, seed: int, draw: int, windeal: bool,
                    daydeal: bool = False, challenge: int = -1) -> None:
        """Creates a new attempt with the given information."""
        # pylint: disable=too-many-arguments
        game_id = self.new_deal(seed, draw, windeal, daydeal, challenge)
        attempt = Attempt(game_id=game_id)
        self._session.add(attempt)
        self._session.commit()
        logger.debug(f'new attempt {attempt.id}')

    def update_attempt(self, **kwargs) -> None:
        """
        Updates the last attempt created through new_attempt.

        Args:
            **kwargs: Valid field names for Attempt, excluding id/game_id and
                both datetime fields.
        """
        res = self._session.query(Attempt).order_by(Attempt.id.desc()).first()
        if res is None:
            raise RuntimeError('No attempt created through new_attempt yet.')
        if res.solved:
            raise RuntimeError('Attempt already solved.')
        for k in kwargs:
            if k in ('id', 'game_id', 'first_move', 'last_move'):
                continue
            if not hasattr(res, k):
                raise ValueError(f'Unknown field name "{k}".')
            setattr(res, k, kwargs[k])
        if res.solved:
            res.total = res.points + res.bonus
        dt = datetime.datetime.utcnow()
        if res.first_move is None:
            res.first_move = dt
        res.last_move = dt
        self._session.commit()
        logger.debug(f'attempt updated {res}')

    def start_session(self) -> None:
        """Starts a new session."""
        session = Session()
        session.start = datetime.datetime.utcnow()
        session.start_local = datetime.datetime.now()
        self._session.add(session)
        self._session.commit()
        logger.debug(f'start session {session}')

    def end_session(self) -> None:
        """Ends the current session."""
        res = self._session.query(Session).order_by(Session.id.desc()).first()
        if res is None:
            raise RuntimeError('No session created through start_session yet.')
        res.end = datetime.datetime.utcnow()
        self._session.commit()
        logger.debug(f'end session {res}')

    def close(self) -> None:
        """Calls commit and closes the open database session."""
        self._session.commit()
        self._session.close()
        logger.debug('closing database session')

    def result(self, seed: int, draw: int, windeal: bool,
               daydeal: bool = False, challenge: int = -1
               ) -> Union[Tuple[float, int, int, int], None]:
        """Returns the result of a game, if available otherwise None."""
        # pylint: disable=too-many-arguments
        if challenge == -1:  # Normal result
            res = self._session.query(Attempt).join(Game) \
                .filter(Game.seed == seed, Game.draw == draw,
                        Game.windeal == windeal, Game.daydeal == daydeal,
                        Game.challenge == challenge, Attempt.solved == true()) \
                .order_by(Attempt.total.desc()).first()
            if res:
                return res.duration, res.moves, res.points, res.bonus
            return None
        # Challenge result, totalized no bonus
        res = self._session.query(Attempt).join(Game) \
            .filter(Game.seed == seed, Game.draw == draw,
                    Game.challenge == challenge) \
                    .order_by(Attempt.last_move.desc()).all()
        if not res:
            return None
        duration, moves = 0, 0
        points = res[0].points
        solved = False
        for i in res:
            solved = solved or i.solved
            duration += i.duration
            moves += i.moves
        if solved:
            return duration, moves, points, 0
        return None

    def attempt_total(self, seed: int, draw: int, challenge: int,
                      gametype: int, current: bool) -> Union[int, float]:
        """Returns the previous made moves or duration for a challenge round."""
        if gametype == 2:  # No accumulation for points
            return 0
        game = self._session.query(Game) \
            .filter(Game.challenge == challenge, Game.seed == seed,
                    Game.draw == draw).first()
        if game is None:
            return 0
        res = self._session.query(Attempt) \
            .filter(Attempt.game_id == game.id) \
            .order_by(Attempt.id.desc()).all()
        duration, moves = 0.0, 0
        for i in res:
            if not current:
                current = True
                continue
            duration += i.duration
            moves += i.moves
        return duration if gametype == 0 else moves

    def highscore(self, draw: int, with_bonus: Optional[bool] = True) -> int:
        """
        Returns the highest score achieved for the specified draw count.

        Args:
            draw:
            with_bonus: Whether to include the bonus in the returned score.
        """
        if with_bonus:
            field = Attempt.total
        else:
            field = Attempt.points
        res = self._session.query(Attempt, Game) \
            .filter(Attempt.game_id == Game.id, Game.draw == draw,
                    Attempt.solved == true()) \
            .order_by(field.desc()).first()
        if res is None:
            return 0
        return res.Attempt.total if with_bonus else res.points

    def fastest(self, draw: int) -> float:
        """Returns fastest time achieved for the specified draw count."""
        res = self._session.query(Attempt, Game) \
            .filter(Attempt.game_id == Game.id, Game.draw == draw,
                    Attempt.solved == true()) \
            .order_by(Attempt.duration.asc()).first()
        if res is None:
            return float('inf')
        return res.Attempt.duration

    def least_moves(self, draw: int) -> int:
        """Returns least moves achieved for the specified draw count."""
        res = self._session.query(Attempt, Game) \
            .filter(Attempt.game_id == Game.id, Game.draw == draw,
                    Attempt.solved == true()) \
            .order_by(Attempt.moves.asc()).first()
        if res is None:
            return 2**32
        return res.Attempt.moves

    def issolved(self, seed: int, draw: int, windeal: bool,
                 daydeal: bool = False) -> bool:
        """Returns whether the specified deal is solved."""
        return self._session.query(Attempt).join(Game) \
            .filter(Attempt.solved == true(), Game.seed == seed,
                    Game.draw == draw, Game.windeal == windeal,
                    Game.daydeal == daydeal).count() > 0

    def _check_migrate(self, engine):
        try:
            _ = self.first_launch
        except OperationalError:
            # Alter table Game here
            col = Column('challenge', Integer, nullable=True, default=-1)
            # pylint: disable=no-value-for-parameter
            colname = col.compile(dialect=engine.dialect)
            # pylint: enable=no-value-for-parameter
            coltype = col.type.compile(engine.dialect)
            engine.execute(f'ALTER TABLE game ADD COLUMN {colname} {coltype}')
        else:
            return
        engine.execute(f'UPDATE game SET challenge=-1 WHERE challenge IS NULL')
        _ = self.first_launch

    @property
    def first_launch(self) -> bool:
        """Returns true if no games are stored yet."""
        if self._session.query(Game).first():
            return False
        return True

    @property
    def deals_played(self) -> int:
        """
        Returns the number of individual games played, that have at least one
        attempt.
        """
        return self._session.query(Attempt) \
            .filter(Attempt.moves > 0) \
            .group_by(Attempt.game_id).count()

    @property
    def solved_ratio(self) -> float:
        """Returns the ratio of attempts to attempts_solved."""
        solved = self._session.query(Attempt) \
            .filter(Attempt.solved == true()).group_by(Attempt.game_id).count()
        attempts = self.deals_played
        if attempts:
            return solved / attempts
        return 0.0

    @property
    def avg_attempts(self) -> float:
        """Returns average attempts per deal."""
        attempts = self._session.query(Attempt) \
            .filter(Attempt.moves > 0).count()
        deals = self.deals_played
        if deals:
            return attempts / deals
        return 0.0

    @property
    def median_attempts(self) -> float:
        """Returns median attempts per deal."""
        attempts = []
        for i in self._session.query(Game).all():
            cnt = self._session.query(Attempt) \
                .filter(Attempt.game_id == i.id).count()
            if cnt:
                attempts.append(cnt)
        attempts.sort()
        numattempts = len(attempts)
        if numattempts % 2:
            return attempts[numattempts // 2]
        return sum(attempts[numattempts // 2 - 1:numattempts // 2 + 1]) / 2
