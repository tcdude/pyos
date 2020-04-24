"""
Provides multiplayer data storage in a sqlite3 db file locally.
"""

from sqlalchemy import Boolean, Column, Float, Integer, Unicode, SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import true
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from loguru import logger

from mpclient import Result

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
class User(Base):
    """"
    Holds user information. Only users with a relationship are stored in this
    table.

    The `rtype` field is one of:
        0 = Sent friend request
        1 = Received friend request
        2 = Friend
        3 = Blocked
    """
    __tablename__ = 'user'
    user_id = Column(Integer, primary_key=True)
    name = Column(Unicode(30), nullable=False)
    rtype = Column(SmallInteger)
    draw_count_preference = Column(SmallInteger)

    def __repr__(self):
        return f'User(id={self.id}, name={self.name}, rtype={self.rtype})'


class State(Base):
    """"Holds a single record with state information."""
    __tablename__ = 'state'
    timestamp = Column(Integer, primary_key=True)

    def __repr__(self):
        return f'State(timestamp={self.timestamp})'


class Challenge(Base):
    """
    Holds challenge information.

    The `status` field is one of:
        0 = Sent request
        1 = Received request
        2 = Accepted / Active
        3 = Played Finished
        4 = Rejected
    """
    __tablename__ = 'challenge'
    challenge_id = Column(Integer, primary_key=True)
    status = Column(SmallInteger, default=0)
    otherid = Column(Integer, nullable=False)
    rounds = Column(SmallInteger, nullable=False)
    active = Column(Boolean, default=True)
    timestamp = Column(Integer)

    def __repr__(self):
        return f'Challenge(id={self.id})'


class ChallengeRound(Base):
    """Holds challenge round information."""
    __tablename__ = 'challenge_round'
    challenge_id = Column(Integer, primary_key=True)
    roundno = Column(SmallInteger, primary_key=True)
    draw = Column(SmallInteger, nullable=False)
    chtype = Column(SmallInteger, nullable=False)
    seed = Column(Integer, default=0)
    user_duration = Column(Float, default=-1.0)
    user_points = Column(SmallInteger, default=-1)
    user_moves = Column(SmallInteger, default=-1)
    other_duration = Column(Float, default=-1.0)
    other_points = Column(SmallInteger, default=-1)
    other_moves = Column(SmallInteger, default=-1)


class Leaderboard(Base):
    """Holds the retrieved leaderboard ranks."""
    __tablename__ = 'leaderboard'
    rank = Column(Integer, primary_key=True)
    points = Column(Integer)
    name = Column(Unicode(30))


class UserData(Base):
    """Holds user related information."""
    __tablename__ = 'user_data'
    id = Column(Integer, primary_key=True)
    draw_count_preference = Column(SmallInteger, default=0)
    rank = Column(Integer)
    points = Column(Integer)


class DDScore(Base):
    """Holds day deal best scores."""
    __tablename__ = 'dd_score'
    draw = Column(SmallInteger, primary_key=True)
    dayoffset = Column(SmallInteger, primary_key=True)
    duration = Column(Float)
    points = Column(SmallInteger)
    moves = Column(SmallInteger)
# pylint: enable=too-few-public-methods


class MPDBHandler:
    """
    Handles everything related to caching multiplayer data.

    Args:
        db_file: The sqlite file to store data in.
    """
    def __init__(self, db_file: str) -> None:
        engine = create_engine(f'sqlite:///{db_file}')
        Base.metadata.create_all(engine)
        Base.metadata.bind = engine
        self._session = sessionmaker(bind=engine)()
        logger.debug('MPDBHandler initialized')

    def update_timestamp(self, timestamp: int) -> None:
        """Update the timestamp."""
        state = self._session.query(State).first()
        if state is None:
            state = State()
            state.timestamp = timestamp
            self._session.add(state)
        else:
            state.timestamp = timestamp
        self._session.commit()

    def update_draw_count_pref(self, pref: int) -> bool:
        """Update the users draw count preference."""
        userdata = self._session.query(UserData).first()
        if userdata is None:
            userdata = UserData()
            userdata.points = 0
            userdata.rank = 0
        userdata.draw_count_preference = pref
        self._session.commit()

    def add_user(self, userid: int, username: str, rtype: int,
                 draw_count_preference: int) -> bool:
        """Add a new user."""
        if self._session.query(User).filter(User.id == userid).count() > 0:
            logger.error('User with userid already exists')
            return False
        user = User()
        user.user_id = userid
        user.name = username
        user.rtype = rtype
        user.draw_count_preference = draw_count_preference
        self._session.add(user)
        self._session.commit()
        return True

    def update_user(self, userid: int, username: str, rtype: int,
                    draw_count_preference: int) -> bool:
        """Update username and/or rtype."""
        user = self._session.query(User).filter(User.id == userid).first()
        if user is None:
            if not self.add_user(userid, username, rtype,
                                 draw_count_preference):
                return False
            return True
        user.name = username
        user.rtype = rtype
        user.draw_count_preference = draw_count_preference
        self._session.commit()
        return True

    def get_username(self, userid: int) -> str:
        """Retrieves a users name if present in the local database."""
        usr = self._session.query(User).filter(User.user_id == userid).first()
        if usr is None:
            return ''
        return usr.name

    def update_user_ranking(self, rank: int, points: int):
        """Update the users rank and points."""
        usrdata = self._session.query(UserData).first()
        if usrdata is None:
            usrdata = UserData()
            self._session.add(usrdata)
        usrdata.rank = rank
        usrdata.points = points
        self._session.commit()

    def update_dd_score(self, draw: int, dayoffset: int, result: Result):
        """Update DDScore."""
        dds = self._session.query(DDScore)\
            .filter(DDScore.draw == draw,
                    DDScore.dayoffset == dayoffset).first()
        if dds is None:
            dds = DDScore()
            dds.draw = draw
            dds.dayoffset = dayoffset
            self._session.add(dds)
        dds.duration, dds.points, dds.moves = result
        self._session.commit()

    def update_leaderboard(self, rank: int, points: int, username: str) -> None:
        """Update an entry in the leaderboard."""
        lbe = self._session.query(Leaderboard) \
            .filter(Leaderboard.rank == rank).first()
        if lbe is None:
            lbe = Leaderboard()
            lbe.rank = rank
            self._session.add(lbe)
        lbe.points = points
        lbe.name = username
        self._session.commit()

    def add_challenge(self, challenge_id: int, otherid: int, rounds: int,
                      status: int = 0, active: bool = True) -> bool:
        """Add a new challenge."""
        # pylint: disable=too-many-arguments
        if self._session.query(Challenge) \
              .filter(Challenge.challenge_id == challenge_id).count() > 0:
            logger.error('Challenge already exists')
            return False
        challenge = Challenge()
        challenge.challenge_id = challenge_id
        challenge.status = status
        challenge.otherid = otherid
        challenge.rounds = rounds
        challenge.active = active
        self._session.add(challenge)
        self._session.commit()
        return True

    def update_challenge(self, challenge_id: int, otherid: int, rounds: int,
                         status: int, active: bool) -> bool:
        """Update an existing challenge."""
        # pylint: disable=too-many-arguments
        challenge = self._session.query(Challenge) \
            .filter(Challenge.challenge_id == challenge_id).first()
        if challenge is None:
            if not self.add_challenge(challenge_id, otherid, rounds, status,
                                      active):
                return False
            return True
        challenge.status = status
        challenge.active = active
        self._session.commit()
        return True

    def add_challenge_round(self, challenge_id: int, roundno: int, draw: int,
                            chtype: int, seed: int = 0) -> bool:
        """Add a new challenge round to a challenge."""
        # pylint: disable=too-many-arguments
        if self._session.query(ChallengeRound) \
              .filter(ChallengeRound.challenge_id == challenge_id,
                      ChallengeRound.roundno == roundno).count() > 0:
            logger.error('Round already exists')
            return False
        chround = ChallengeRound()
        chround.challenge_id = challenge_id
        chround.roundno = roundno
        chround.draw = draw
        chround.chtype = chtype
        chround.seed = seed
        self._session.add(chround)
        self._session.commit()
        return True

    def update_challenge_round(self, challenge_id: int, roundno: int,
                               draw: int = None, chtype: int = None,
                               seed: int = 0, resuser: Result = None,
                               resother: Result = None ) -> bool:
        """Update an existing challenge round."""
        # pylint: disable=too-many-arguments
        chround = self._session.query(ChallengeRound) \
            .filter(ChallengeRound.challenge_id == challenge_id,
                    ChallengeRound.roundno == roundno).first()
        if chround is None:
            if draw is None or chtype is None:
                logger.error('ChallengeRound does not exists and cannot be '
                             'created w/o "draw" and "chtype" argument')
                return False
            if self.add_challenge_round(challenge_id, roundno, draw, chtype,
                                        seed):
                return True
            logger.error('Unable to create non-existing ChallengeRound')
            return False
        chround.seed = seed
        if resuser is not None:
            chround.user_duration = resuser[0]
            chround.user_points = resuser[1]
            chround.user_moves = resuser[2]
        if resother is not None:
            chround.other_duration = resother[0]
            chround.other_points = resother[1]
            chround.other_moves = resother[2]
        self._session.commit()
        self._check_challenge_complete(challenge_id)
        return True

    def _check_challenge_complete(self, challenge_id: int) -> None:
        """Finalizes a challenge if all rounds have been played."""
        count = self._session.query(ChallengeRound) \
            .filter(ChallengeRound.challenge_id == challenge_id,
                    ChallengeRound.user_duration != -1.0,
                    ChallengeRound.user_points != -1,
                    ChallengeRound.user_moves != -1,
                    ChallengeRound.other_duration != -1.0,
                    ChallengeRound.other_points != -1,
                    ChallengeRound.other_moves != -1).count()
        challenge = self._session.query(Challenge) \
            .filter(Challenge.challenge_id == challenge_id,
                    Challenge.rounds == count).first()
        if challenge is not None:
            challenge.active = False
            self._session.commit()

    @property
    def timestamp(self) -> int:
        """Return the last timestamp or 0 if not recorded yet."""
        state = self._session.query(State).first()
        if state is None:
            return 0
        return state.timestamp
