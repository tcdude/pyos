"""
Data collection and preparation.
"""

import datetime
import time
from typing import Dict, List, Optional, Tuple, Union

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        Unicode, func)
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import true
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine
from loguru import logger

import common

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


class Statistic(Base):
    """Holds statistical information that are calculated in the background."""
    __tablename__ = 'statistic'
    id = Column(Integer, primary_key=True)
    last_update = Column(DateTime)
    deals_played_offline = Column(Integer, default=0)
    deals_solved_offline = Column(Integer, default=0)
    solved_ratio_offline = Column(Float, default=1.0)
    avg_attempts_offline = Column(Float, default=1.0)
    median_attempts_offline = Column(Float, default=1.0)
    win_streak = Column(Integer, default=0)
    deals_played_online = Column(Integer, default=0)
    deals_solved_online = Column(Integer, default=0)
    solved_ratio_online = Column(Float, default=1.0)
    avg_attempts_online = Column(Float, default=1.0)
    median_attempts_online = Column(Float, default=1.0)

    def __repr__(self):
        return f'Statistic(id={self.id}, ...)'


class Seed(Base):
    """Holds winable game seeds and the corresponding solution."""
    __tablename__ = 'seed'
    id = Column(Integer, primary_key=True)
    draw = Column(Integer)
    seed = Column(Integer)
    solution = Column(Unicode(500), default='')
    keep = Column(Boolean, default=True)
    played = Column(Boolean, default=False)
    need = Column(Boolean, default=False)


class Communication(Base):
    """Holds communication variables between the App and the solver threads."""
    __tablename__ = 'communication'
    id = Column(Integer, primary_key=True)
    exit_solver = Column(Boolean, default=False)
    exit_confirm = Column(Boolean, default=True)
    solver_running = Column(Boolean, default=False)
# pylint: enable=too-few-public-methods


class Stats:
    """
    Handles everything related to storing and retrieving stats data.

    Args:
        db_file: The sqlite file to load/store data in.
    """
    # pylint: disable=too-many-public-methods
    def __init__(self, db_file: str) -> None:
        engine = create_engine(f'sqlite:///{db_file}')
        Base.metadata.create_all(engine)
        Base.metadata.bind = engine
        self._session = sessionmaker(bind=engine)()
        self._check_migrate(engine)
        self._stats_type = 0
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
                    Attempt.solved == true(), Game.challenge == -1) \
            .order_by(field.desc()).first()
        if res is None:
            return 0
        return res.Attempt.total if with_bonus else res.points

    def fastest(self, draw: int) -> float:
        """Returns fastest time achieved for the specified draw count."""
        res = self._session.query(Attempt, Game) \
            .filter(Attempt.game_id == Game.id, Game.draw == draw,
                    Attempt.solved == true(), Game.challenge == -1) \
            .order_by(Attempt.duration.asc()).first()
        if res is None:
            return float('inf')
        return res.Attempt.duration

    def least_moves(self, draw: int) -> int:
        """Returns least moves achieved for the specified draw count."""
        res = self._session.query(Attempt, Game) \
            .filter(Attempt.game_id == Game.id, Game.draw == draw,
                    Attempt.solved == true(), Game.challenge == -1) \
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

    def request_solution(self, draw: int, seed: int) -> None:
        """Request a solution for a specific deal."""
        res = self._session.query(Seed) \
            .filter(Seed.draw == draw, Seed.seed == seed).first()
        if res is None:
            res = Seed()
            res.draw = draw
            res.seed = seed
            self._session.add(res)
        res.need = True
        self._session.commit()

    def update_seed(self, draw: int, seed: int, solution: str = None,
                    keep: bool = None) -> None:
        """Update a seed in the database."""
        res = self._session.query(Seed) \
            .filter(Seed.draw == draw, Seed.seed == seed).first()
        if res is None:
            res = Seed()
            res.draw = draw
            res.seed = seed
            self._session.add(res)
        if solution is not None:
            res.solution = solution
        if keep is not None:
            res.keep = keep
        self._session.commit()

    def clean_seeds(self) -> None:
        """Deletes all seeds that aren't needed anymore."""
        self._session.query(Seed).filter(Seed.keep != true()).delete()
        self._session.commit()

    def get_seed(self, draw: int) -> None:
        """Retrieves a seed from the database and marks it as played."""
        while True:
            res = self._session.query(Seed) \
                .filter(Seed.draw == draw,
                        Seed.played != true(),
                        Seed.need != true()).first()
            if res is not None:
                res.played = True
                self._session.commit()
                return res.seed
            time.sleep(0.05)

    def get_solution(self, draw: int, seed: int) -> str:
        """
        Retrieves a solution from the database and marks the game as solution
        shown.
        """
        game = self._session.query(Game) \
            .filter(Game.draw == draw, Game.seed == seed).first()
        if game is None:
            logger.error('Requested solution for an unknown game.')
            return ''
        game.solution = True
        res = self._session.query(Seed) \
            .filter(Seed.draw == draw, Seed.seed == seed).first()
        if res is None or not res.solution:
            self.request_solution(draw, seed)
        else:
            if not res.played:
                res.played = True
                self._session.commit()
            return res.solution
        while True:
            res = self._session.query(Seed) \
                .filter(Seed.draw == draw, Seed.seed == seed).first()
            if res is not None:
                res.played = True
                self._session.commit()
                return res.solution
            time.sleep(0.05)

    def update_statistics(self) -> None:
        """Update statistics if necessary."""
        attempt = self._session.query(Attempt) \
            .order_by(Attempt.id.desc()).first()
        if not attempt.solved:
            delta = datetime.datetime.utcnow() - attempt.last_move
            if delta.total_seconds() < 30:
                return
        last_move = attempt.last_move
        stat: Statistic = self._session.query(Statistic).first()
        if stat is None:
            stat = Statistic()
            stat.last_update = common.START_DATE
            self._session.add(stat)
        if stat.last_update >= last_move:
            self._session.commit()
            return
        logger.info('Updating statistics')
        stat.deals_played_offline = self._session.query(Attempt, Game) \
            .join(Game, Game.id == Attempt.game_id) \
            .filter(Attempt.moves > 0, Game.challenge == -1) \
            .group_by(Attempt.game_id).count()
        stat.deals_solved_offline = self._session.query(Game.id) \
            .join(Attempt, Attempt.game_id == Game.id) \
            .filter(Attempt.solved == true(),
                    Game.challenge == -1) \
            .group_by(Game.id).count()
        if stat.deals_played_offline:
            self._update_offline_stats(stat)

        # TODO: stat.win_streak =

        stat.deals_played_online = self._session.query(Game) \
            .filter(Game.challenge > -1).count()
        stat.deals_solved_online = self._session.query(Game.id) \
            .join(Attempt, Attempt.game_id == Game.id) \
            .filter(Attempt.solved == true(),
                    Game.challenge > -1) \
            .group_by(Game.id).count()
        if stat.deals_played_online:
            self._update_online_stats(stat)
        stat.last_update = datetime.datetime.utcnow()
        self._session.commit()

    def _update_offline_stats(self, stat: Statistic) -> None:
        stat.solved_ratio_offline = (stat.deals_solved_offline
                                     / stat.deals_played_offline)
        attempts = self._session.query(Attempt, Game) \
            .join(Game, Game.id == Attempt.game_id) \
            .filter(Attempt.moves > 0, Game.challenge == -1).count()
        stat.avg_attempts_offline = attempts / stat.deals_played_offline
        games = self._session.query(func.count(Attempt.id)) \
            .join(Game, Game.id == Attempt.game_id) \
            .filter(Game.challenge == -1, Attempt.moves > 1) \
            .group_by(Game.id).order_by(func.count(Attempt.id)).all()
        numgames = len(games)
        if numgames % 2:
            med = games[numgames // 2][0]
        else:
            med = (games[numgames // 2 - 1][0]
                   + games[numgames // 2 - 1][0]) / 2
        stat.median_attempts_offline = med

    def _update_online_stats(self, stat: Statistic) -> None:
        stat.solved_ratio_online = (stat.deals_solved_online
                                    / stat.deals_played_online)
        attempts = self._session.query(Attempt, Game) \
            .join(Game, Game.id == Attempt.game_id) \
            .filter(Attempt.moves > 0, Game.challenge > -1).count()
        stat.avg_attempts_online = attempts / stat.deals_played_online
        games = self._session.query(func.count(Attempt.id)) \
            .join(Game, Game.id == Attempt.game_id) \
            .filter(Game.challenge > -1, Attempt.moves > 1) \
            .group_by(Game.id).order_by(func.count(Attempt.id)).all()
        numgames = len(games)
        if numgames % 2:
            med = games[numgames // 2][0]
        else:
            med = (games[numgames // 2 - 1][0]
                   + games[numgames // 2 - 1][0]) / 2
        stat.median_attempts_online = med

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
        res: Statistic = self._session.query(Statistic).first()
        if res is None:
            return 0
        if self._stats_type == 1:
            return res.deals_played_online
        return res.deals_played_offline

    @property
    def deals_solved(self) -> int:
        """Returns the number of individual games solved."""
        res: Statistic = self._session.query(Statistic).first()
        if res is None:
            return 0
        if self._stats_type == 1:
            return res.deals_solved_online
        return res.deals_solved_offline

    @property
    def solved_ratio(self) -> float:
        """Returns the ratio of games played to games solved."""
        res: Statistic = self._session.query(Statistic).first()
        if res is None:
            return 0
        if self._stats_type == 1:
            return res.solved_ratio_online
        return res.solved_ratio_offline

    @property
    def avg_attempts(self) -> float:
        """Returns average attempts per deal."""
        res: Statistic = self._session.query(Statistic).first()
        if res is None:
            return 0
        if self._stats_type == 1:
            return res.avg_attempts_online
        return res.avg_attempts_offline

    @property
    def median_attempts(self) -> float:
        """Returns median attempts per deal."""
        res: Statistic = self._session.query(Statistic).first()
        if res is None:
            return 0
        if self._stats_type == 1:
            return res.median_attempts_online
        return res.median_attempts_offline

    @property
    def stats_type(self) -> int:
        """
        Can be used to set the stats type, that is returned by the above
        properties. 0 for offline, 1 for online.
        """
        return self._stats_type

    @stats_type.setter
    def stats_type(self, stype: int) -> None:
        self._stats_type = stype

    @property
    def exit_solver(self) -> bool:
        """Whether the solver thread should exit."""
        comm = self._session.query(Communication).first()
        if comm is None:
            comm = Communication()
            self._session.add(comm)
            self._session.commit()
        return comm.exit_solver

    @exit_solver.setter
    def exit_solver(self, value: bool) -> None:
        comm = self._session.query(Communication).first()
        if comm is None:
            comm = Communication()
            self._session.add(comm)
        comm.exit_solver = value
        if value:
            comm.exit_confirm = False
        self._session.commit()

    @property
    def exit_confirm(self) -> bool:
        """Whether the solver thread has exited."""
        comm = self._session.query(Communication).first()
        if comm is None:
            comm = Communication()
            self._session.add(comm)
            self._session.commit()
        return comm.exit_confirm

    @exit_confirm.setter
    def exit_confirm(self, value: bool) -> None:
        comm = self._session.query(Communication).first()
        if comm is None:
            comm = Communication()
            self._session.add(comm)
        comm.exit_confirm = value
        self._session.commit()

    @property
    def solver_running(self) -> bool:
        """Whether the solver thread is running."""
        comm = self._session.query(Communication).first()
        if comm is None:
            comm = Communication()
            self._session.add(comm)
            self._session.commit()
        return comm.solver_running

    @solver_running.setter
    def solver_running(self, value: bool) -> None:
        comm = self._session.query(Communication).first()
        if comm is None:
            comm = Communication()
            self._session.add(comm)
        comm.solver_running = value
        self._session.commit()

    @property
    def solutions_needed(self) -> List[Tuple[int, int]]:
        """Returns all requested seeds that have no solution yet."""
        return self._session.query(Seed.draw, Seed.seed) \
            .filter(Seed.need == true(), Seed.solution == '').all()

    @property
    def seed_count(self) -> Dict[int, int]:
        """Returns a dict mapping the number of seeds per draw count."""
        ret = {1: 0, 3: 0}
        for i in self._session.query(Seed.draw, func.count(Seed.id)) \
              .filter(Seed.keep == true(),
                      Seed.solution != '',
                      Seed.played != true()).group_by(Seed.draw).all():
            ret[i[0]] = i[1]
        return ret
