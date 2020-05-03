"""
Provides multiplayer data storage in a sqlite3 db file locally.
"""

from typing import List, Tuple

from sqlalchemy import Boolean, Column, Float, Integer, Unicode, SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import true
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, or_, and_
from loguru import logger

import common
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
    rank = Column(Integer, default=0)
    points = Column(Integer, default=0)
    won = Column(Integer, default=0)
    lost = Column(Integer, default=0)
    draw = Column(Integer, default=0)

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
    rank = Column(Integer, default=0)
    points = Column(Integer, default=0)


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
        if self._session.query(User).filter(User.user_id == userid).count() > 0:
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

    def update_user(self, userid: int, username: str = None, rtype: int = None,
                    draw_count_preference: int = None, rank: int = None,
                    points: int = None, stats: Tuple[int, int, int] = None
                    ) -> bool:
        """Update user."""
        # pylint: disable=too-many-arguments
        user = self._session.query(User).filter(User.user_id == userid).first()
        if user is None and not None in (username, rtype,
                                         draw_count_preference):
            if not self.add_user(userid, username, rtype,
                                 draw_count_preference):
                return False
            if rank is points is None:
                return True
            user = self._session.query(User) \
                .filter(User.user_id == userid).first()
        user.name = username or user.name
        user.rtype = rtype or user.rtype
        dpref = user.draw_count_preference
        user.draw_count_preference = draw_count_preference or dpref
        user.rank = rank or user.rank
        user.points = points or user.points
        if stats is not None:
            user.won, user.lost, user.draw = stats
        self._session.commit()
        return True

    def get_username(self, userid: int) -> str:
        """Retrieves a users name if present in the local database."""
        usr = self._session.query(User).filter(User.user_id == userid).first()
        if usr is None:
            return ''
        return usr.name

    def update_user_ranking(self, rank: int, points: int) -> None:
        """Update the users rank and points."""
        usrdata = self._session.query(UserData).first()
        if usrdata is None:
            usrdata = UserData()
            self._session.add(usrdata)
        usrdata.rank = rank
        usrdata.points = points
        self._session.commit()

    def delete_user(self, userid: int) -> bool:
        """Attempts to delete a user."""
        user = self._session.query(User).filter(User.user_id == userid).first()
        if user is None:
            return False
        self._session.delete(user)
        self._session.commit()
        return True

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
                               resother: Result = None) -> bool:
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

    def userstats(self, userid: int) -> Tuple[int, int, int, int, int]:
        """Returns the stats for a user (rank, points, won, lost, draw)."""
        user = self._session.query(User).filter(User.user_id == userid).first()
        if user is None:
            logger.error('Unknown user')
            return (0, ) * 5
        return user.rank, user.points, user.won, user.lost, user.draw

    def canchallenge(self, userid: int) -> bool:
        """Returns `True` when the user can be sent a challenge request."""
        return self._session.query(Challenge) \
            .filter(Challenge.active == true(),
                    Challenge.otherid == userid).count() == 0

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

    @property
    def draw_count_preference(self) -> int:
        """The users draw count preference or `4` if not loaded yet."""
        data = self._session.query(UserData).first()
        if data is None:
            return 4
        return data.draw_count_preference

    @draw_count_preference.setter
    def draw_count_preference(self, pref: int) -> None:
        data = self._session.query(UserData).first()
        if data is None:
            data = UserData()
            self._session.add(data)
        data.draw_count_preference = pref
        self._session.commit()

    @property
    def userids(self) -> List[int]:
        """Returns a list of all user ids."""
        ret = []
        for i in self._session.query(User).all():
            ret.append(i.user_id)
        return ret

    @property
    def friends(self) -> List[Tuple[int, str]]:
        """Returns all friends as a list."""
        ret = []
        for i in self._session.query(User).filter(User.rtype == 2).all():
            ret.append((i.user_id, i.name))
        return ret

    @property
    def pending(self) -> List[Tuple[int, str]]:
        """
        Returns all pending friend requests, prefixed with i=incoming and
        o=sent by the user.
        """
        ret = []
        for i in self._session.query(User).filter(User.rtype == 0).all():
            ret.append((i.user_id, 'o' + i.name))
        for i in self._session.query(User).filter(User.rtype == 1).all():
            ret.append((i.user_id, 'i' + i.name))
        return ret

    @property
    def blocked(self) -> List[Tuple[int, str]]:
        """Returns all blocked users as a list."""
        ret = []
        for i in self._session.query(User).filter(User.rtype == 3).all():
            ret.append((i.user_id, i.name))
        return ret

    @property
    def chmyturn(self) -> List[Tuple[int, str]]:
        """Returns all challenges where it's the users turn."""
        act = []
        new = []
        res = self._session.query(Challenge) \
            .filter(Challenge.active == true(),
                    Challenge.status.in_([1, 2])).all()
        for i in res:
            user = self._session.query(User) \
                .filter(User.user_id == i.otherid).first()
            if user is None:
                logger.error('User in challenge not present in DB')
                continue
            if i.status == 1:
                txt = f'NEW ({user.name} / {i.rounds})'
                new.append((i.challenge_id, txt))
                continue
            chround = self._session.query(ChallengeRound) \
                .filter(ChallengeRound.challenge_id == i.challenge_id,
                        ChallengeRound.seed != 0,
                        ChallengeRound.user_duration == -1.0,
                        ChallengeRound.user_moves == -1,
                        ChallengeRound.user_points == -1) \
                .order_by(ChallengeRound.roundno.desc()).first()
            if chround is None:
                continue
            txt = f'{user.name} D{chround.draw}/{chround.roundno}/{i.rounds}'
            act.append((i.challenge_id, txt))
        new.sort(key=lambda x: x[1])
        act.sort(key=lambda x: x[1])
        return new + act

    @property
    def chwaiting(self) -> List[Tuple[int, str]]:
        """Returns all challenges where it's the other users turn."""
        req = []
        wait = []
        res = self._session.query(Challenge) \
            .filter(Challenge.active == true(),
                    Challenge.status.in_([0, 2])).all()
        for i in res:
            user = self._session.query(User) \
                .filter(User.user_id == i.otherid).first()
            if user is None:
                logger.error('User in challenge not present in DB')
                continue
            if i.status == 0:
                txt = f'{common.OUT_SYM} ({user.name} / {i.rounds})'
                req.append((i.challenge_id, txt))
                continue
            chround = self._session.query(ChallengeRound) \
                .filter(ChallengeRound.challenge_id == i.challenge_id,
                        ChallengeRound.user_duration != -1.0,
                        ChallengeRound.user_moves != -1,
                        ChallengeRound.user_points != -1,
                        ChallengeRound.other_duration == -1.0,
                        ChallengeRound.other_moves == -1,
                        ChallengeRound.other_points == -1) \
                .order_by(ChallengeRound.roundno.desc()).first()
            if chround is None:
                continue
            txt = f'{user.name} D{chround.draw}/{chround.roundno}/{i.rounds}'
            wait.append((i.challenge_id, txt))
        req.sort(key=lambda x: x[1])
        wait.sort(key=lambda x: x[1])
        return wait + req

    @property
    def chfinished(self) -> List[Tuple[int, str]]:
        """Returns all locally stored finished challenges."""
        ret = []
        res = self._session.query(Challenge) \
            .filter(Challenge.active != true(),
                    Challenge.status == 3) \
            .order_by(Challenge.challenge_id.desc()).all()
        for i in res:
            user = self._session.query(User) \
                .filter(User.user_id == i.otherid).first()
            if user is None:
                logger.error('User in challenge not present in DB')
                continue
            txt = f'{common.ACC_SYM} ({user.name} / {i.rounds})'
            ret.append((i.challenge_id, txt))
        return ret

    @property
    def challenge_available(self) -> List[Tuple[int, str]]:
        """Returns all users against whom a challenge can be requested."""
        ret = []
        userdata = self._session.query(UserData).first()
        if userdata is None or userdata.draw_count_preference == 3:
            logger.warning('User does not want to multiplay')
            return ret
        if userdata.draw_count_preference == 0:
            acceptable = (0, 1, 2)
        else:
            acceptable = (userdata.draw_count_preference, )
        for i in self._session.query(User) \
              .filter(User.draw_count_preference.in_(acceptable),
                      User.rtype == 2) \
              .order_by(User.name).all():
            if self._session.query(Challenge) \
                  .filter(Challenge.active == true(),
                          Challenge.otherid == i.user_id).count() > 0:
                continue
            ret.append((i.user_id, i.name))
        return ret
