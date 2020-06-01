"""
Provides multiplayer data storage in a sqlite3 db file locally.
"""
# pylint: disable=too-many-lines

import datetime
import time
from typing import List, Tuple, Union

from sqlalchemy import (Boolean, Column, DateTime, Float, Integer, Unicode,
                        SmallInteger, func)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import true
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, or_, and_
from loguru import logger

import common
from common import Result

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

# Activities as defined in the table Activity
CHALLENGE = 0
USER = 1

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
    chwon = Column(Integer, default=0)
    chlost = Column(Integer, default=0)
    chdraw = Column(Integer, default=0)
    rwon = Column(Integer, default=0)
    rlost = Column(Integer, default=0)
    rdraw = Column(Integer, default=0)

    def __repr__(self):
        return f'User(id={self.user_id}, name={self.name}, ' \
               f'rtype={self.rtype}, dcp={self.draw_count_preference})'


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
    userturn = Column(Boolean, default=False)
    unseen = Column(Boolean, default=True)
    start_date = Column(DateTime(timezone=True),
                        server_default=func.now())

    def __repr__(self):
        return f'Challenge(id={self.challenge_id}, status={self.status}, ' \
               f'rounds={self.rounds}, otherid={self.otherid}, ' \
               f'active={self.active}, userturn={self.userturn})'


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
    result_sent = Column(Boolean, default=False)

    def __repr__(self):
        user = self.user_duration, self.user_points, self.user_moves
        other = self.other_duration, self.other_points, self.other_moves
        return f'ChallengeRound(id={self.challenge_id}, ' \
               f'roundno={self.roundno}, draw={self.draw}, ' \
               f'chtype={self.chtype}, seed={self.seed}, user={repr(user)}, ' \
               f'other={repr(other)}, result_sent={self.result_sent})'


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
    duration = Column(Float, default=-1.0)
    points = Column(SmallInteger, default=0)
    moves = Column(SmallInteger, default=0)
    score_sent = Column(Boolean, default=False)


class Activity(Base):
    """
    Flexible way to store timestamps. The field activity holds an int related to
    what the timestamp is referring to:

    0 = Last Challenge/ChallengeRound update
    """
    __tablename__ = 'activity'
    id = Column(Integer, primary_key=True)
    key = Column(Integer)
    activity = Column(Integer, nullable=False)
    timestamp = Column(Integer, default=lambda: int(time.time()))


class UserID(Base):
    """Holds the users own id."""
    __tablename__ = 'user_id'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
# pylint: enable=too-few-public-methods


class MPDBHandler:
    """
    Handles everything related to caching multiplayer data.

    Args:
        db_file: The sqlite file to store data in.
    """
    # pylint: disable=too-many-public-methods
    def __init__(self, db_file: str) -> None:
        engine = create_engine(f'sqlite:///{db_file}')
        Base.metadata.create_all(engine)
        Base.metadata.bind = engine
        self._session = sessionmaker(bind=engine)()
        self._populate_missing_activity()
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
            self._session.add(userdata)
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
        self._update_activity(USER, userid)
        self._session.commit()
        return True

    def update_user(self, userid: int, username: str = None, rtype: int = None,
                    draw_count_preference: int = None, rank: int = None,
                    points: int = None,
                    stats: Tuple[int, int, int, int, int, int] = None) -> bool:
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
        changed = False
        if username is not None and username != user.name:
            changed = True
            user.name = username
        if rtype is not None and rtype != user.rtype:
            changed = True
            user.rtype = rtype
        if draw_count_preference is not None:
            if user.draw_count_preference != draw_count_preference:
                changed = True
            user.draw_count_preference = draw_count_preference
        if rank is not None and rank != user.rank:
            changed = True
            user.rank = rank or user.rank
        if points is not None and points != user.points:
            changed = True
            user.points = points
        if stats is not None:
            flds = ('chwon', 'chlost', 'chdraw', 'rwon', 'rlost', 'rdraw')
            for val, fld in zip(stats, flds):
                if val != getattr(user, fld):
                    changed = True
                    setattr(user, fld, val)
        if changed:
            logger.info('User has changed')
            self._update_activity(USER, userid)
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

    def update_dd_score(self, draw: int, dayoffset: int, result: Result = None,
                        sent: bool = None):
        """Update DDScore."""
        dds = self._session.query(DDScore)\
            .filter(DDScore.draw == draw,
                    DDScore.dayoffset == dayoffset).first()
        if dds is None:
            dds = DDScore()
            dds.draw = draw
            dds.dayoffset = dayoffset
            self._session.add(dds)
        if sent is not None:
            dds.score_sent = sent
        if result is not None:
            dds.duration, dds.moves, dds.points = result
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
        self._update_activity(CHALLENGE, challenge_id)
        self._update_activity(USER, otherid)
        self._session.commit()
        return True

    def update_challenge(self, challenge_id: int, otherid: int, rounds: int,
                         status: int, active: bool, userturn: bool = False
                         ) -> bool:
        """Update an existing challenge."""
        # pylint: disable=too-many-arguments
        challenge = self._session.query(Challenge) \
            .filter(Challenge.challenge_id == challenge_id).first()
        if challenge is None:
            if not self.add_challenge(challenge_id, otherid, rounds, status,
                                      active):
                return False
            challenge = self._session.query(Challenge) \
                .filter(Challenge.challenge_id == challenge_id).first()
        changed = False
        if status != challenge.status:
            changed = True
            challenge.status = status
        if challenge.active != active:
            changed = True
            challenge.active = active
        if challenge.userturn != userturn:
            changed = True
            challenge.userturn = userturn
        if changed:
            self._update_activity(CHALLENGE, challenge_id)
            self._update_activity(USER, otherid)
            self._session.commit()
        return True

    def reject_challenge(self, challenge_id: int) -> bool:
        """Reject a received challenge request."""
        challenge = self._session.query(Challenge) \
            .filter(Challenge.challenge_id == challenge_id).first()
        if challenge is None:
            return False
        challenge.status = 4
        challenge.active = False
        self._session.commit()
        return True

    def inactive_challenge(self, challenge_id: int) -> bool:
        """Set active flag to False and update status."""
        challenge = self._session.query(Challenge) \
            .filter(Challenge.challenge_id == challenge_id).first()
        if challenge is None:
            return False
        challenge.active = False
        if challenge.status == 2:
            challenge.status = 3
            self._update_activity(CHALLENGE, challenge_id)
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
        self._update_activity(CHALLENGE, challenge_id)
        self._update_activity(USER, self.opponent_id(challenge_id))
        self._session.commit()
        return True

    def update_challenge_round(self, challenge_id: int, roundno: int,
                               draw: int = None, chtype: int = None,
                               seed: int = None, resuser: Result = None,
                               resother: Result = None, result_sent: bool = None
                               ) -> bool:
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
                                        seed or 0):
                chround = self._session.query(ChallengeRound) \
                    .filter(ChallengeRound.challenge_id == challenge_id,
                            ChallengeRound.roundno == roundno).first()
            else:
                logger.error('Unable to create non-existing ChallengeRound')
                return False
        changed = False
        if seed is not None and seed != chround.seed:
            changed = True
            chround.seed = seed
        if resuser is not None and resuser[0] != chround.user_duration:
            changed = True
            chround.user_duration = resuser[0]
            chround.user_points = resuser[1]
            chround.user_moves = resuser[2]
        if resother is not None and resother[0] != chround.other_duration:
            changed = True
            chround.other_duration = resother[0]
            chround.other_points = resother[1]
            chround.other_moves = resother[2]
        if result_sent is not None and result_sent != chround.result_sent:
            changed = True
            chround.result_sent = result_sent
        if changed:
            self._update_activity(CHALLENGE, challenge_id)
            self._update_activity(USER, self.opponent_id(challenge_id))
            self._session.commit()
        self._check_challenge_complete(challenge_id)
        return True

    def challenge_result(self, challenge_id: int) -> Tuple[int, int, int, bool]:
        """
        Returns the current or final result of a challenge as rounds won, lost,
        draw and whether the challenge is finished.
        """
        challenge = self._session.query(Challenge) \
            .filter(Challenge.challenge_id == challenge_id).first()
        if challenge is None:
            return -1, -1, -1, False
        won, lost, draw = 0, 0, 0
        finished = True
        for i in range(challenge.rounds):
            res = self.round_won(challenge_id, i + 1)
            if res in (-1, 3):
                finished = False
                break
            if res == 0:
                won += 1
            elif res == 1:
                lost += 1
            elif res == 2:
                draw += 1
        return won, lost, draw, finished

    def num_rounds(self, challenge_id: int) -> int:
        """Returns the number of rounds to be played in a given challenge."""
        challenge = self._session.query(Challenge) \
            .filter(Challenge.challenge_id == challenge_id).first()
        if challenge is None:
            logger.error('Unknown challenge id')
            return -1
        return challenge.rounds

    def get_round_info(self, challenge_id: int, roundno: int = None
                       ) -> Tuple[int, int, int]:
        """
        Returns seed, draw, score type for a challenge id. If no roundno is
        specified, the information of the highest available round number will be
        returned.
        """
        if roundno is None:
            chround = self._session.query(ChallengeRound) \
                .filter(ChallengeRound.challenge_id == challenge_id) \
                .order_by(ChallengeRound.roundno.desc()).first()
        else:
            chround = self._session.query(ChallengeRound) \
                .filter(ChallengeRound.challenge_id == challenge_id,
                        ChallengeRound.roundno == roundno).first()
        if chround is None:
            logger.error('Requested unknown round info')
            return -1, -1, -1
        return chround.seed, chround.draw, chround.chtype

    def round_won(self, challenge_id: int, roundno: int = None) -> int:
        """
        Round result: 0=won, 1=lost, 2=draw, 3=first result, -1=invalid round.
        """
        if roundno is None:
            chround = self._session.query(ChallengeRound) \
                .filter(ChallengeRound.challenge_id == challenge_id) \
                .order_by(ChallengeRound.roundno.desc()).first()
        else:
            chround = self._session.query(ChallengeRound) \
                .filter(ChallengeRound.challenge_id == challenge_id,
                        ChallengeRound.roundno == roundno).first()
        ret = None
        if chround is None:
            logger.error('Requested unknown round info')
            ret = -1
        elif -1.0 in (chround.other_duration, chround.user_duration):
            ret = 3
        elif chround.user_duration == chround.other_duration == -2.0:
            ret = 2
        elif chround.other_duration == -2.0:
            ret = 0
        elif chround.user_duration == -2.0:
            ret = 1
        if ret is not None:
            return ret
        comp = (
            (chround.user_duration, chround.user_moves, chround.other_points),
            (chround.other_duration, chround.other_moves, chround.user_points))
        if comp[0][chround.chtype] == comp[1][chround.chtype]:
            return 2
        return 0 if comp[0][chround.chtype] < comp[1][chround.chtype] else 1

    def round_result(self, challenge_id: int, roundno: int) -> Result:
        """
        Returns the users result in a challenge round.
        """
        chround = self._session.query(ChallengeRound.user_duration,
                                      ChallengeRound.user_points,
                                      ChallengeRound.user_moves) \
            .filter(ChallengeRound.challenge_id == challenge_id,
                    ChallengeRound.roundno == roundno).first()
        if None in chround:
            return -1.0, 0, 0
        return chround

    def round_other_result(self, challenge_id: int, roundno: int
                           ) -> Union[int, float]:
        """
        Returns the relevant part of the result of the other player in a
        challenge round. Special values -1 = No result yet, -2 = Forfeited and
        -3 = Unable to find the challenge round.
        """
        chround = self._session.query(ChallengeRound) \
            .filter(ChallengeRound.challenge_id == challenge_id,
                    ChallengeRound.roundno == roundno).first()
        if chround is None:
            return -3
        if chround.other_duration == -2.0:
            return -2
        if chround.other_duration == -1.0:
            return -1
        ret = (chround.other_duration, chround.other_moves,
               chround.other_points)
        return ret[chround.chtype]

    def userstats(self, userid: int) -> Tuple[int, int, int, int, int, int, int,
                                              int]:
        """
        Return the stats for a user (rank, points, challenges [won, lost, draw],
        rounds [won, lost, draw]).
        """
        user = self._session.query(User).filter(User.user_id == userid).first()
        if user is None:
            logger.error('Unknown user')
            return (0, ) * 5
        return (user.rank, user.points, user.chwon, user.chlost, user.chdraw,
                user.rwon, user.rlost, user.rdraw)

    def canchallenge(self, userid: int) -> bool:
        """Returns `True` when the user can be sent a challenge request."""
        return self._session.query(Challenge) \
            .filter(Challenge.active == true(),
                    Challenge.otherid == userid).count() == 0

    def available_draw(self, challenge_id: int) -> List[int]:
        """Returns a list of draw counts that can be used in a challenge."""
        userdata = self._session.query(UserData).first()
        if userdata is None:
            userdcp = 0
        else:
            userdcp = userdata.draw_count_preference
        other = self._session.query(User) \
            .join(Challenge, Challenge.otherid == User.user_id) \
            .filter(Challenge.challenge_id == challenge_id,
                    Challenge.active == true()).first()
        if other is None:
            logger.error('Unable to find challenge')
            return []
        otherdcp = other.draw_count_preference
        if 3 in (userdcp, otherdcp):
            return []
        if userdcp == otherdcp == 0:
            return [1, 3]
        if userdcp == 1 or otherdcp == 1:
            return [1]
        if userdcp == 2 or otherdcp == 2:
            return [3]
        return []

    def roundno(self, challenge_id: int) -> int:
        """
        Returns the current round number of a challenge or 0 if no round has
        been created yet. -1 if the challenge is not in the DB.
        """
        if self._session.query(Challenge) \
              .filter(Challenge.challenge_id == challenge_id).count() != 1:
            return -1
        return self._session.query(ChallengeRound) \
            .filter(ChallengeRound.challenge_id == challenge_id).count()

    def newround(self, challenge_id: int) -> bool:
        """Whether the user can choose a gametype."""
        challenge = self._session.query(Challenge) \
            .filter(Challenge.challenge_id == challenge_id).first()
        if challenge is None:
            logger.warning('Unknown challenge id')
            return False
        chround = self._session.query(ChallengeRound) \
            .filter(ChallengeRound.challenge_id == challenge_id) \
            .order_by(ChallengeRound.roundno.desc()).first()
        if chround is None and challenge.status == 1:
            return True
        if chround is None and challenge.status != 1:
            return False

        uplayed = chround.user_duration != -1.0
        oplayed = chround.other_duration != -1.0

        if chround.roundno == challenge.rounds and uplayed and oplayed \
              or (chround.seed != 0 and not uplayed):
            return False
        if uplayed is oplayed is False and challenge.status > 0 \
              or (uplayed and oplayed and chround.roundno < challenge.rounds):
            return True
        logger.warning(f'Unhandled case {challenge} {chround}')
        return False

    def opponent_id(self, challenge_id: int) -> int:
        """Returns the user id of the opponent in a challenge."""
        other = self._session.query(User) \
            .join(Challenge, Challenge.otherid == User.user_id) \
            .filter(Challenge.challenge_id == challenge_id).first()
        if other is None:
            logger.error('Unable to find challenge')
            return -1
        return other.user_id

    def challenge_view(self, challenge_id: int) -> str:
        """Generates an overview text of a challenge."""
        challenge = self._session.query(Challenge) \
            .filter(Challenge.challenge_id == challenge_id).first()
        if challenge is None:
            logger.error('Invalid challenge')
            return 'Challenge not found!'
        other = self._session.query(User) \
            .filter(User.user_id == challenge.otherid).first()
        if other is None:
            logger.error('Unable to find other user')
            return 'Unable to find other user!'
        other = other.name
        roundno = self.roundno(challenge_id)
        txt = f'{other} ({roundno}/{challenge.rounds}) '
        txt += f'{challenge.start_date.strftime("%d.%m.%Y")}\n\n'
        res = self.challenge_result(challenge_id)
        txt += f'Rounds won {res[0]}, lost {res[1]}, draw {res[2]}\n'
        txt += 'Status: '
        if not res[3]:
            txt += 'Active'
        elif res[0] > res[1]:
            txt += 'You WON'
        elif res[0] < res[1]:
            txt += 'You LOST'
        else:
            txt += 'DRAW'
        txt += '\n\n'
        if len(other) > 9:
            other = other[:8] + '.'
        rounds = self._session.query(ChallengeRound) \
            .filter(ChallengeRound.challenge_id == challenge_id) \
            .order_by(ChallengeRound.roundno).all()
        res = []
        mxt, mxu, mxo = 0, 0, 0
        for i in rounds:
            res.append([])
            ltxt = f'{i.roundno}/{i.draw}: '
            ltxt += ('Time', 'Moves', 'Points')[i.chtype]
            res[-1].append(ltxt)
            if i.user_duration == -1.0:
                res[-1].append('?')
            elif i.user_duration == -2.0:
                res[-1].append('Forfeit')
            elif i.chtype == 0:
                res[-1].append(common.format_duration(i.user_duration))
            else:
                if i.chtype == 1:
                    res[-1].append(f'{i.user_moves}')
                else:
                    res[-1].append(f'{i.user_points}')
            ores = self.round_other_result(challenge_id, i.roundno)
            if i.user_duration == -1.0:
                res[-1].append('?')
            elif ores == -2:
                res[-1].append('Forfeit')
            elif ores == -1:
                res[-1].append('?')
            elif i.chtype == 0:
                res[-1].append(common.format_duration(ores))
            else:
                res[-1].append(f'{ores}')
            res[-1].append(
                (chr(0xf118), chr(0xf119), chr(0xf11a), chr(0xf252),
                 chr(0xf128))[self.round_won(challenge_id, i.roundno)])
            mxt = max(mxt, len(res[-1][0]))
            mxu = max(mxu, len(res[-1][1]))
            mxo = max(mxo, len(res[-1][2]))
        leftlen = mxt + mxu + 1
        rightlen = mxo + 2
        txt += f'Round/Draw{" " * max(leftlen - 13, 1)}You - '
        if len(other) > rightlen:
            tpad = 0
            rpad = len(other) - rightlen
        else:
            tpad = rightlen - len(other)
            rpad = 0
        lpad = 0
        if leftlen < 14:
            lpad = 14 - leftlen
        txt += f'{other}{" " * tpad}\n\n'
        for i in res:
            txt += f'{i[0]}{" " * (leftlen - len(i[0]) - len(i[1]) - 1 + lpad)}'
            txt += f' {i[1]} - {i[2]} ' + ' ' * (mxo - len(i[2]) + rpad)
            txt += f'{i[3]}\n'
        txt += '\n'
        return txt

    def challenge_complete(self, challenge_id: int) -> bool:
        """Returns True if all round results are present."""
        challenge = self._session.query(Challenge) \
            .filter(Challenge.challenge_id == challenge_id).first()
        if challenge is None:
            logger.error('Challenge not found')
            return False
        return self._session.query(ChallengeRound) \
            .filter(ChallengeRound.challenge_id == challenge_id,
                    ChallengeRound.user_duration != -1.0,
                    ChallengeRound.other_duration != -1.0) \
            .count() == challenge.rounds

    def round_complete(self, challenge_id: int, roundno: int) -> bool:
        """Returns whether a challenge round is stored with full result."""
        return self._session.query(ChallengeRound) \
            .filter(ChallengeRound.challenge_id == challenge_id,
                    ChallengeRound.roundno == roundno,
                    or_(ChallengeRound.user_duration == -2.0,
                        ChallengeRound.user_duration > 0),
                    or_(ChallengeRound.other_duration == -2.0,
                        ChallengeRound.other_duration > 0)).count() == 1

    def userid(self, username: str) -> int:
        """
        Returns the user id if present as friend, -1 if present as blocked user,
        -2 if a friendrequest is pending or -3 if not present in user table.
        """
        user = self._session.query(User).filter(User.name == username).first()
        if user is None:
            return -3
        if user.rtype == 2:
            return user.user_id
        if user.rtype == 3:
            return -1
        return -2

    def dd_score(self, draw: int, dayoffset: int) -> Result:
        """
        Returns a dd best score if available, otherwise -1.0 in duration.
        """
        res = self._session.query(DDScore) \
            .filter(DDScore.draw == draw,
                    DDScore.dayoffset == dayoffset).first()
        if res is None or res.duration == -1.0:
            return -1.0, 0, 0
        return res.duration, res.moves, res.points

    def purge_database(self) -> None:
        """Purge all user related data in the database!"""
        logger.warning('Purging all user data')
        self._session.query(User).delete()
        self._session.query(State).delete()
        self._session.query(UserData).delete()
        self._session.query(Challenge).delete()
        self._session.query(ChallengeRound).delete()
        self._session.query(Activity).delete()
        self._session.query(UserID).delete()
        self._session.commit()

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
            challenge.status = 3
            self._session.commit()

    def _populate_missing_activity(self) -> None:
        """Populates pre update entries to activities."""
        act = self._session.query(Activity.key) \
            .filter(Activity.activity == CHALLENGE)
        chg = self._session.query(Challenge.challenge_id, Challenge.otherid) \
            .filter(Challenge.challenge_id.notin_(act)).all()
        now = int(time.time())
        if act.count() > 0:
            now = 0
        user = []
        for challenge_id, otherid in chg:
            act = Activity()
            act.key = challenge_id
            act.activity = CHALLENGE
            act.timestamp = now
            self._session.add(act)
            if otherid not in user:
                user.append(otherid)
        for otherid in user:
            self._update_activity(USER, otherid, only_new=True)
        for usr in self._session.query(User) \
              .filter(User.user_id.notin_(user)).all():
            self._update_activity(USER, usr.user_id, only_new=True)
        self._session.commit()

    def _update_activity(self, activity: int, key: int, commit: bool = False,
                         only_new: bool = False) -> None:
        """Update an activity/key pair."""
        act = self._session.query(Activity) \
            .filter(Activity.activity == activity, Activity.key == key).first()
        if act is None:
            act = Activity()
            act.activity = activity
            act.key = key
            self._session.add(act)
        elif only_new:
            return
        act.timestamp = int(time.time())
        if commit:
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
        for i in self._session.query(User) \
              .join(Activity, Activity.key == User.user_id) \
              .filter(User.rtype == 2,
                      Activity.activity == USER) \
              .order_by(Activity.timestamp.desc()).all():
            ret.append((i.user_id, i.name))
        return ret

    @property
    def pending(self) -> List[Tuple[int, str]]:
        """
        Returns all pending friend requests, prefixed with i=incoming and
        o=sent by the user.
        """
        ret = []
        for i in self._session.query(User) \
              .join(Activity, Activity.key == User.user_id) \
              .filter(User.rtype == 0,
                      Activity.activity == USER) \
              .order_by(Activity.timestamp.desc()).all():
            ret.append((i.user_id, 'o' + i.name))
        for i in self._session.query(User) \
              .join(Activity, Activity.key == User.user_id) \
              .filter(User.rtype == 1,
                      Activity.activity == USER) \
              .order_by(Activity.timestamp.desc()).all():
            ret.append((i.user_id, 'i' + i.name))
        return ret

    @property
    def blocked(self) -> List[Tuple[int, str]]:
        """Returns all blocked users as a list."""
        ret = []
        for i in self._session.query(User) \
              .join(Activity, Activity.key == User.user_id) \
              .filter(User.rtype == 3,
                      Activity.activity == USER) \
              .order_by(Activity.timestamp.desc()).all():
            ret.append((i.user_id, i.name))
        return ret

    @property
    def chmyturn(self) -> List[Tuple[int, str]]:
        """Returns all challenges where it's the users turn."""
        act = []
        new = []
        res = self._session.query(Challenge) \
            .join(Activity, Activity.key == Challenge.challenge_id) \
            .filter(Challenge.active == true(),
                    Challenge.status.in_([1, 2]),
                    Activity.activity == CHALLENGE) \
            .order_by(Activity.timestamp.desc()).all()
        for i in res:
            user = self._session.query(User) \
                .filter(User.user_id == i.otherid).first()
            if user is None:
                logger.error('User in challenge not present in DB')
                continue
            if i.status == 1:
                txt = common.NEW_SYM + f' {user.name} - {i.rounds} Rounds'
                new.append((i.challenge_id, txt))
                continue
            chround = self._session.query(ChallengeRound) \
                .join(Challenge,
                      Challenge.challenge_id == ChallengeRound.challenge_id) \
                .filter(ChallengeRound.challenge_id == i.challenge_id,
                        ChallengeRound.seed != 0,
                        Challenge.userturn == true(),
                        or_(ChallengeRound.user_duration == -1.0,
                            and_(ChallengeRound.user_duration != -1.0,
                                 ChallengeRound.other_duration != -1.0))) \
                .order_by(ChallengeRound.roundno.desc()).first()
            if chround is None:
                continue
            txt = f'{user.name} D{chround.draw} - ' \
                  f'Round {chround.roundno}/{i.rounds}'
            act.append((i.challenge_id, txt))
        return new + act

    @property
    def chwaiting(self) -> List[Tuple[int, str]]:
        """Returns all challenges where it's the other users turn."""
        req = []
        wait = []
        res = self._session.query(Challenge) \
            .join(Activity, Activity.key == Challenge.challenge_id) \
            .filter(Challenge.active == true(),
                    Challenge.status.in_([0, 2]),
                    Activity.activity == CHALLENGE) \
            .order_by(Activity.timestamp.desc()).all()
        for i in res:
            user = self._session.query(User) \
                .filter(User.user_id == i.otherid).first()
            if user is None:
                logger.error('User in challenge not present in DB')
                continue
            if i.status == 0:
                txt = f'{common.OUT_SYM} {user.name} - {i.rounds} Rounds'
                req.append((i.challenge_id, txt))
                continue
            chround = self._session.query(ChallengeRound) \
                .join(Challenge,
                      Challenge.challenge_id == ChallengeRound.challenge_id) \
                .filter(ChallengeRound.challenge_id == i.challenge_id,
                        Challenge.userturn != true()) \
                .order_by(ChallengeRound.roundno.desc()).first()
            if chround is None:
                continue
            txt = f'{user.name} D{chround.draw} - ' \
                  f'Round {chround.roundno}/{i.rounds}'
            wait.append((i.challenge_id, txt))
        return wait + req

    @property
    def chwaiting_last_round(self) -> List[int]:
        """Returns all challenge ids where the last round is pending."""
        res = self._session.query(Challenge.challenge_id) \
            .join(ChallengeRound,
                  ChallengeRound.challenge_id == Challenge.challenge_id) \
            .filter(Challenge.active == true(),
                    ChallengeRound.roundno == Challenge.rounds,
                    ChallengeRound.user_duration != -1.0,
                    ChallengeRound.other_duration == -1.0).all()
        return res

    @property
    def chfinished(self) -> List[Tuple[int, str]]:
        """Returns all locally stored finished challenges."""
        ret = []
        res = self._session.query(Challenge) \
            .join(Activity, Activity.key == Challenge.challenge_id) \
            .filter(Challenge.active != true(),
                    Challenge.status == 3,
                    Activity.activity == CHALLENGE) \
            .order_by(Activity.timestamp.desc(),
                      Challenge.start_date.desc()).all()
        for i in res:
            user = self._session.query(User) \
                .filter(User.user_id == i.otherid).first()
            if user is None:
                logger.error('User in challenge not present in DB')
                continue
            txt = '* ' if i.unseen else ''
            txt += f'{common.ACC_SYM} {user.name} - {i.rounds} / ' \
                   f'{i.start_date.strftime("%d.%m.%Y")}'
            ret.append((i.challenge_id, txt))
            if i.unseen:
                i.unseen = False
        self._session.commit()
        return ret

    @property
    def challenge_available(self) -> List[Tuple[int, str]]:
        """Returns all users against whom a challenge can be requested."""
        ret = []
        userdata = self._session.query(UserData).first()
        if userdata is None:
            logger.warning('UserData is not present!')
            userdata = UserData()
            userdata.points = 0
            userdata.rank = 0
            self._session.add(userdata)
            self._session.commit()
        elif userdata.draw_count_preference == 3:
            logger.warning('User does not want to multiplay')
            return ret
        if userdata.draw_count_preference == 0:
            acceptable = (0, 1, 2)
        else:
            acceptable = (userdata.draw_count_preference, 0)
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

    @property
    def active_challenges(self) -> List[int]:
        """Returns all challenge ids that are marked active."""
        return self._session.query(Challenge.challenge_id) \
            .filter(Challenge.active == true()).all()

    @property
    def unsent_results(self) -> List[Tuple[int, int]]:
        """
        Returns all challenge id/roundno where the result_sent flag is False.
        """
        return self._session \
            .query(ChallengeRound.challenge_id, ChallengeRound.roundno) \
            .join(Challenge,
                  Challenge.challenge_id == ChallengeRound.challenge_id) \
            .filter(ChallengeRound.result_sent != true(),
                    ChallengeRound.seed != 0).all()

    @property
    def leaderboard(self) -> List[Tuple[int, int, str]]:
        """
        Returns the leaderboard as a list of tuples, containing rank, points and
        name.
        """
        return self._session \
            .query(Leaderboard.rank, Leaderboard.points, Leaderboard.name) \
            .order_by(Leaderboard.rank).all()

    @property
    def rankmax(self) -> int:
        """Returns the highest rank number, stored in the leaderboard."""
        rank = self._session.query(func.max(Leaderboard.rank)).first()
        return 0 if rank[0] is None else rank[0]

    @property
    def challenge_actions(self) -> int:
        """How many challenges require the users attention."""
        return len(self.chmyturn) + self._session.query(Challenge) \
            .filter(Challenge.active != true(),
                    Challenge.unseen == true()).count()

    @property
    def friend_actions(self) -> int:
        """How many pending friend requests."""
        return self._session.query(User).filter(User.rtype == 1).count()

    @property
    def unsent_dd_scores(self) -> List[Tuple[int, int]]:
        """
        Returns a list of unsent dd scores as list of tuples containing day and
        draw count.
        """
        today = datetime.datetime.utcnow()
        start_i = today - common.START_DATE - datetime.timedelta(days=9)
        unsent = []
        for i in range(10):
            for k in (1, 3):
                if self._session.query(DDScore) \
                      .filter(DDScore.draw == k,
                              DDScore.dayoffset == start_i.days + i,
                              DDScore.score_sent == true()).count() == 1:
                    continue
                unsent.append((start_i.days + i, k))
        return unsent

    @property
    def own_userid(self) -> int:
        """Returns the users own id or -1 if None is present."""
        userid = self._session.query(UserID).first()
        if userid is None:
            return -1
        return userid.user_id

    @own_userid.setter
    def own_userid(self, new_id: int) -> None:
        userid = self._session.query(UserID).first()
        if userid is None:
            userid = UserID()
            self._session.add(userid)
        userid.user_id = new_id
        self._session.commit()
