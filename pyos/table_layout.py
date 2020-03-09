"""
Provides the TableLayout class.
"""

from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from dataclasses import dataclass

from foolysh.animation import BlendType
from foolysh.animation import PosInterval
from foolysh.animation import RotationInterval
from foolysh.scene import node
from foolysh.tools import aabb
from foolysh.tools import vec2

import card
import common
from table import Table

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
__version__ = '0.2'


@dataclass
class TableConfig:
    """Typed representation of table configuration values."""
    card_size: Tuple[float, float]
    padding: float
    status_size: Tuple[float, float]
    toolbar_size: Tuple[float, float]


@dataclass
class TableNodes:
    """Typed representation of table nodes."""
    root: Type[node.Node]
    stack: Type[node.Node]
    waste: Type[node.Node]
    foundation: Type[node.Node]
    tableau: Type[node.Node]
    status: Type[node.Node]
    toolbar: Type[node.Node]


@dataclass
class ChildNodes:
    """Typed representation of child nodes of table nodes."""
    waste: List[Type[node.Node]]
    foundation: List[Type[node.Node]]
    tableau: List[Type[node.Node]]


@dataclass
class RelativePositions:
    """Relative positions of anchor nodes."""
    stack: vec2.Vec2
    waste: List[vec2.Vec2]
    foundation: List[vec2.Vec2]
    tableau: List[vec2.Vec2]


@dataclass
class CardNode:
    """Typed representation of a card."""
    k: Tuple[int, int]
    node: node.ImageNode
    location: common.TableLocation


@dataclass
class DragInfo:
    """Retains info about current drag interactions."""
    active: Optional[bool] = False
    drag_card: Optional[CardNode] = None
    child_cards: Optional[List[CardNode]] = None
    v_offset: Optional[float] = 0.0


@dataclass
class DepthQueueItem:
    """Holds information about a queued depth step."""
    card: CardNode
    expiration: float
    depth: int


class DepthQueue:
    """Retains information about deferred depth processing."""

    def __init__(self):
        self._time: float = 0.0
        self._queue: Optional[Dict[Tuple[int, int], DepthQueueItem]] = {}

    @property
    def time(self) -> float:
        """Return the current retained time."""
        return self._time

    def update_time(self, delta_time: float) -> None:
        """Update the time"""
        self._time += delta_time

    def pop_items(self) -> Optional[List[DepthQueueItem]]:
        """
        To be called after update_time to retrieve all expired queue items.
        """
        pop_list = []
        res = []
        for k in self._queue:
            item = self._queue[k]
            if item.expiration <= self._time:
                pop_list.append(k)
                res.append(item)
        if pop_list:
            for i in pop_list:
                self._queue.pop(i)
            return res
        return None

    def append(self, item: DepthQueueItem) -> None:
        """Insert a new item to the queue."""
        self._queue[item.card.k] = item


class TableLayout:
    """
    Provides an adaptable layout of nodes for the card table, switchable between
    portrait and landscape orientation to be used as placement helpers. The
    :meth:`TableLayout.setup` method should be called on every resolution change
    and the :attr:`TableLayout.root` property should be reparented to a node in
    the scene once.

    Args:
        card_ratio: ``float`` card height divided by width.
        padding: ``float`` padding between cards/elements.
        status_size: ``Tuple[float, float]`` width and height of status row.
        toolbar_size: ``Tuple[float, float]`` width and height of toolbar.
    """
    # pylint: disable=too-many-instance-attributes

    def __init__(
            self,
            card_ratio: float,
            padding: float,
            status_size: Tuple[float, float],
            toolbar_size: Tuple[float, float]
        ) -> None:
        card_size = (
            1 / (7 + 8 * padding),
            card_ratio * (1 / (7 + 8 * padding))
        )
        self._cfg = TableConfig(
            card_size=card_size,
            padding=(card_size[0] * padding, card_size[1] * padding),
            status_size=status_size,
            toolbar_size=toolbar_size
        )
        root = node.Node('Table Root')
        root.distance_relative = True
        root.depth = -100
        self._nodes = TableNodes(
            root=root,
            stack=root.attach_image_node('Stack', common.STACK),
            waste=root.attach_node('Waste Root'),
            foundation=root.attach_node('Foundation Root'),
            tableau=root.attach_node('Tableau Root'),
            status=root.attach_node('Status'),
            toolbar=root.attach_node('Toolbar')
        )
        self._children = ChildNodes(
            waste=[
                self._nodes.waste.attach_image_node(
                    f'Waste {i}',
                    common.WASTE
                ) if not i else self._nodes.waste.attach_node(
                    f'Waste {i}'
                ) for i in range(4)
            ],
            foundation=[
                self._nodes.foundation.attach_image_node(
                    f'Foundation {i}',
                    common.FOUNDATION
                ) for i in range(4)
            ],
            tableau=[
                self._nodes.tableau.attach_image_node(
                    f'Tableau {i}',
                    common.TABLEAU
                ) for i in range(7)
            ]
        )

        # Background
        background = self._nodes.root.attach_node('BG Root')
        background.depth = -500
        offset = .1
        for x_pos in range(26):
            for y_pos in range(26):
                tmp_node = background.attach_image_node(image=common.BACKGROUND)
                tmp_node.pos = x_pos * offset, y_pos * offset
        self._v_offset = (0.0, self._cfg.card_size[1] / 3)

        # Cards
        card_dummy = self._nodes.root.attach_node('Card Layer')
        card_dummy.depth = 99
        self._cards: Dict[Tuple[int, int], CardNode] = {
            (suit, value): CardNode(
                k=(suit, value),
                node=card_dummy.attach_image_node(
                    f'{suit},{value}',
                    f'images/{common.COLORS[suit]}'
                    f'{common.DENOMINATIONS[value]}.png'
                ),
                location=common.TableLocation(
                    area=common.TableArea.NONE,
                    visible=False
                )
            ) for suit in range(4) for value in range(13)
        }
        for k in self._cards:
            self._cards[k].node.add_image(common.CARDBACK)
            self._cards[k].node.index = 1

        self._drag_info: DragInfo = DragInfo()
        self._depth_queue = DepthQueue()
        self._relative_positions = RelativePositions(
            stack=vec2.Vec2(),
            waste=[vec2.Vec2() for _ in range(4)],
            foundation=[vec2.Vec2() for _ in range(4)],
            tableau=[vec2.Vec2() for _ in range(7)]
        )
        self._table: Optional[Table] = None

    @property
    def root(self) -> Type[node.Node]:
        """Root node of the layout."""
        return self._nodes.root

    @property
    def stack(self) -> Type[node.Node]:
        """Stack node of the layout."""
        return self._nodes.stack

    @property
    def waste(self) -> List[Type[node.Node]]:
        """Waste node of the layout."""
        return self._children.waste

    @property
    def foundation(self) -> List[Type[node.Node]]:
        """Foundation node of the layout."""
        return self._children.foundation

    @property
    def tableau(self) -> List[Type[node.Node]]:
        """Tableau node of the layout."""
        return self._children.tableau

    @property
    def status(self) -> Type[node.Node]:
        """Status node of the layout."""
        return self._nodes.status

    @property
    def toolbar(self) -> Type[node.Node]:
        """Toolbar node of the layout."""
        return self._nodes.toolbar

    @property
    def callback(self) -> Callable[[card.Card, common.TableLocation], None]:
        """Callback to pass into Table."""
        return self._callback

    def set_table(self, table: Table) -> None:
        """Set the Table instance to retrieve TableRepresentation."""
        self._table = table

    def get_card(self, k: Tuple[int, int]) -> node.ImageNode:
        """Get the ImageNode of the specified card for outside usage."""
        return self._cards[k].node

    def process(self, dt):
        """Task to be registered on the App side for processing."""
        # pylint: disable=invalid-name
        self._relative_positions = RelativePositions(
            stack=self._nodes.stack.relative_pos,
            waste=[self._children.waste[i].relative_pos for i in range(4)],
            foundation=[
                self._children.foundation[i].relative_pos for i in range(4)
            ],
            tableau=[
                self._children.tableau[i].relative_pos for i in range(7)
            ]
        )
        self._depth_queue.update_time(dt)
        queue = self._depth_queue.pop_items()
        if queue is not None:
            for item in queue:
                item.card.node.depth = item.depth
        self._drag_task()

    def _drag_task(self) -> None:
        """Updates cards during drag and drop interaction."""
        if not self._drag_info.active or not self._drag_info.child_cards:
            return
        drag_pos = self._drag_info.drag_card.node.pos
        offset = vec2.Vec2(0, self._drag_info.v_offset)
        for i, card_node in enumerate(self._drag_info.child_cards):
            card_node.node.pos = drag_pos + ((i + 1) * offset)

    def on_drag(
            self,
            drag_card: Tuple[int, int],
            child_cards: Optional[List[Tuple[int, int]]] = None,
            pile_size: Optional[int] = 1
        ) -> None:
        """
        Called to start a drag.
        """
        self._drag_info.active = True
        self._drag_info.drag_card = self._cards[drag_card]
        self._drag_info.drag_card.node.depth = 200
        if child_cards:
            self._drag_info.child_cards = [self._cards[k] for k in child_cards]
            self._drag_info.v_offset = self.v_offset(pile_size)
            for i, card_node in enumerate(self._drag_info.child_cards):
                card_node.node.depth = 201 + i
        else:
            self._drag_info.child_cards = None

    def on_drop(self) -> None:
        """
        Called when a drop occurs.
        """
        d_i = self._drag_info
        if d_i.active:
            d_i.active = False
            card_nodes = [d_i.drag_card]
            if d_i.child_cards:
                card_nodes += d_i.child_cards
            for card_node in card_nodes:
                card_node.node.depth = card_node.location.card_id

    def click_area(
            self,
            mouse_pos: vec2.Vec2()
        ) -> Optional[Tuple[common.TableArea, Tuple[int, int]]]:
        """
        Find the area and if applicable the index of the specified mouse
        position.

        Args:
            mouse_pos: Vec2 -> the mouse pointer position.
            tableau_piles: List[int] -> the number of cards on each tableau
                pile.

        Returns:
            Tuple[TableArea, Tuple[int, int]] for the mouse position, if a valid
            area and indices, if applicable, were found. Otherwise returns None.
        """
        m_x, m_y = mouse_pos.x, mouse_pos.y
        if self._nodes.stack.aabb.inside_tup(m_x, m_y):
            return common.TableArea.STACK, (0, 0)
        if self._children.waste[0].aabb.inside_tup(m_x, m_y):
            return common.TableArea.WASTE, (0, 0)
        for i, f_node in enumerate(self._children.foundation):
            if f_node.aabb.inside_tup(m_x, m_y):
                return common.TableArea.FOUNDATION, (i, 0)

        tableau_piles = [len(i) for i in self._table.table.tableau]
        for i, t_node in enumerate(self._children.tableau):
            if tableau_piles[i] == 0:
                if not t_node.aabb.inside_tup(m_x, m_y):
                    continue
                return common.TableArea.TABLEAU, (i, 0)
            t_x, t_y = t_node.aabb.pos
            h_w, h_h = t_node.aabb.size
            v_offset = self.v_offset(tableau_piles[i])
            for j in reversed(range(tableau_piles[i])):
                t_aabb = aabb.AABB(
                    t_x,
                    t_y + j * v_offset,
                    h_w,
                    h_h
                )
                if t_aabb.inside_tup(m_x, m_y):
                    return common.TableArea.TABLEAU, (i, j)
        return None

    def v_offset(self, cards: int) -> float:
        """
        Vertical offset for cards placed on the tableau.

        Args:
            cards: ``int`` number of cards on the stack
        """
        offset = (1 - cards / 19) * (self._v_offset[1] - self._v_offset[0])
        return offset + self._v_offset[0]

    def setup(
            self,
            screen_size: Tuple[int, int],
            left_handed: Optional[bool] = False
        ) -> None:
        """
        Setup the node positions to reflect screen size and left vs right
        handed.

        Args:
            screen_size: ``Tuple[int, int]`` width and height of the screen.
            left_handed: ``bool`` whether to place stack/waste on the left.
        """
        if screen_size[0] < screen_size[1]:  # Portrait
            self._setup_portrait(screen_size, left_handed)
        else:  # Landscape
            self._setup_landscape(screen_size, left_handed)

    def _setup_portrait(
            self,
            screen_size: Tuple[int, int],
            left_handed: bool
        ) -> None:
        """
        Setup node positions for portrait layout.

        Args:
            screen_size: ``Tuple[int, int]`` width and height of the screen.
            left_handed: ``bool`` whether to place stack/waste on the left.
        """
        card_w, card_h = self._cfg.card_size
        pad = self._cfg.padding
        self._nodes.status.pos = (1 - self._cfg.status_size[0]) / 2, pad[1]
        y_pos = 2 * pad[1] + self._cfg.status_size[1]
        if left_handed:
            self._nodes.stack.pos = pad[0], y_pos
            self._nodes.waste.pos = self.stack.x + card_w + pad[0], y_pos
            for i, waste_node in enumerate(self._children.waste):
                waste_node.x = i * (card_w / 3 + pad[0] / 3)
            self._nodes.foundation.pos = 1 - (4 * card_w + 4 * pad[0]), y_pos
        else:
            self._nodes.stack.pos = 1 - card_w - pad[0], y_pos
            self._nodes.waste.pos = self.stack, -(card_w + pad[0]), 0
            for i, waste_node in enumerate(self._children.waste):
                waste_node.x = -i * (card_w / 3 + pad[0] / 3)
            self._nodes.foundation.pos = pad[0], y_pos
        for i, foundation_node in enumerate(self._children.foundation):
            foundation_node.pos = i * (card_w + pad[0]), 0
        screen_height = screen_size[1] / screen_size[0]
        tableau_height = screen_height - y_pos - 4 * pad[1] - card_h
        tableau_height -= self._cfg.toolbar_size[1]
        self._v_offset = (
            min(
                card_h / 3,
                card_h * ((tableau_height / card_h - 1) / 18)
            ),
            card_h / 3
        )
        self._nodes.tableau.pos = pad[0], y_pos + card_h + pad[1]
        for i, tableau_node in enumerate(self._children.tableau):
            tableau_node.x = i * (card_w + pad[0])
        self._nodes.toolbar.pos = (
            (1 - self._cfg.toolbar_size[0]) / 2,
            screen_height - self._cfg.toolbar_size[1] - pad[1]
        )

    def _setup_landscape(
            self,
            screen_size: Tuple[int, int],
            left_handed: bool
        ) -> None:
        """
        Setup node positions for landscape layout.

        Args:
            screen_size: ``Tuple[int, int]`` width and height of the screen.
            left_handed: ``bool`` whether to place stack/waste on the left.
        """
        card_w, card_h = self._cfg.card_size
        pad = self._cfg.padding
        width = screen_size[0] / screen_size[1]
        self._nodes.status.pos = (width - self._cfg.status_size[0]) / 2, pad[0]
        y_pos = 2 * pad[0] + self._cfg.status_size[1]
        y_stack = 0.5 + pad[1] / 2
        y_waste = 0.5 - (card_h + pad[1] / 2)
        self._nodes.foundation.y = 0.5 - (2 * card_h + pad[1] * 1.5)
        if left_handed:
            self._nodes.stack.pos = pad[0], y_stack
            self._nodes.waste.pos = pad[0], y_waste
            for i, waste_node in enumerate(self._children.waste):
                waste_node.x = i * (card_w / 3 + pad[0] / 3)
            self._nodes.foundation.x = width - pad[0] - card_w
            self._nodes.tableau.pos = pad[0] + 3 * (card_w + pad[0]), y_pos
        else:
            self._nodes.stack.pos = width - pad[0] - card_w, y_stack
            self._nodes.waste.pos = width - pad[0] - card_w, y_waste
            for i, waste_node in enumerate(self._children.waste):
                waste_node.x = -i * (card_w / 3 + pad[0] / 3)
            self._nodes.foundation.x = pad[0]
            self._nodes.tableau.pos = 2 * pad[0] + card_w, y_pos
        for i, foundation_node in enumerate(self._children.foundation):
            foundation_node.pos = 0, i * (card_h + pad[1])
        tableau_height = 1 - self._cfg.toolbar_size[1] - y_pos - 2 * pad[1]
        self._v_offset = (
            min(
                card_h / 3,
                card_h * ((tableau_height / card_h - 1) / 18)
            ),
            card_h / 3
        )
        for i, tableau_node in enumerate(self._children.tableau):
            tableau_node.x = i * (card_w + pad[0])
        self._nodes.toolbar.pos = (
            (width - self._cfg.toolbar_size[0]) / 2,
            1 - self._cfg.toolbar_size[1] - pad[1]
        )

    def refresh_all(self):
        """Force refresh all card nodes."""
        table = self._table.table
        for i, t_card in enumerate(table.stack):
            self._cards[t_card.index[0]].location = common.TableLocation(
                common.TableArea.STACK,
                False,
                card_id=i
            )
        w_len = len(table.waste)
        for i, t_card in enumerate(table.waste):
            pile_id = min(3, w_len - i - 1)
            self._cards[t_card.index[0]].location = common.TableLocation(
                common.TableArea.WASTE,
                True,
                pile_id=pile_id,
                card_id=i
            )
        for i, pile in enumerate(table.foundation):
            for j, t_card in enumerate(pile):
                self._cards[t_card.index[0]].location = common.TableLocation(
                    common.TableArea.FOUNDATION,
                    True,
                    pile_id=i,
                    card_id=j
                )
        for i, pile in enumerate(table.tableau):
            for j, t_card in enumerate(pile):
                self._cards[t_card.index[0]].location = common.TableLocation(
                    common.TableArea.TABLEAU,
                    t_card.index[1] == 0,
                    pile_id=i,
                    card_id=j
                )

        meths = {
            common.TableArea.STACK: self._callback_stack,
            common.TableArea.WASTE: self._callback_waste,
            common.TableArea.FOUNDATION: self._callback_foundation,
            common.TableArea.TABLEAU: self._callback_tableau,
            common.TableArea.NONE: None
        }
        c_loc = common.TableLocation(common.TableArea.NONE)
        for k in self._cards:
            card_node = self._cards[k]
            if meths[card_node.location.area] is None:
                continue
            meths[card_node.location.area](c_loc, card_node.location, card_node)

    def _callback(
            self,
            t_card: card.Card,
            loc: common.TableLocation
        ) -> None:
        """
        Callback method to handle placement and depth of cards.
        """
        card_node = self._cards[t_card.index[0]]
        c_loc = card_node.location

        queue = False
        if loc.area == common.TableArea.STACK:
            queue = self._callback_stack(c_loc, loc, card_node)
        elif loc.area == common.TableArea.WASTE:
            queue = self._callback_waste(c_loc, loc, card_node)
        elif loc.area == common.TableArea.FOUNDATION:
            queue = self._callback_foundation(c_loc, loc, card_node)
        elif loc.area == common.TableArea.TABLEAU:
            queue = self._callback_tableau(c_loc, loc, card_node)
        elif card_node.node.depth != loc.card_id:
            queue = True

        if loc.visible:  # To force foolysh to render the next frame!
            card_node.node.index = 1
            card_node.node.index = 0
        else:
            card_node.node.index = 0
            card_node.node.index = 1

        card_node.location = loc
        if queue:
            self._depth_queue.append(
                DepthQueueItem(
                    card_node,
                    self._depth_queue.time + 0.3,
                    loc.card_id
                )
            )

    def _callback_stack(
            self,
            c_loc: common.TableLocation,
            loc: common.TableLocation,
            card_node: CardNode
        ) -> bool:
        """Place card on Stack."""
        t_pos = self._relative_positions.stack
        if c_loc.area != loc.area or c_loc.pile_id != loc.pile_id or \
                c_loc.card_id != loc.card_id or card_node.node.pos != t_pos:
            PosInterval(
                card_node.node,
                0.2,
                t_pos,
                blend=BlendType.EASE_OUT
            ).play()
            card_node.node.index = 1
            card_node.node.depth = 200 + loc.card_id
            return True
        return False

    def _callback_waste(
            self,
            c_loc: common.TableLocation,
            loc: common.TableLocation,
            card_node: CardNode
        ) -> bool:
        """Place card on Waste."""
        t_pos = self._relative_positions.waste[loc.pile_id]
        if c_loc.area != loc.area or c_loc.pile_id != loc.pile_id or \
              c_loc.card_id != loc.card_id or card_node.node.pos != t_pos:
            PosInterval(
                card_node.node,
                0.2,
                t_pos,
                blend=BlendType.EASE_OUT
            ).play()
            card_node.node.index = 0
            card_node.node.depth = 200 + loc.card_id
            return True
        return False

    def _callback_foundation(
            self,
            c_loc: common.TableLocation,
            loc: common.TableLocation,
            card_node: CardNode
        ) -> bool:
        """Place card on Foundation."""
        t_pos = self._relative_positions.foundation[loc.pile_id]
        if c_loc.area != loc.area or c_loc.pile_id != loc.pile_id or \
              c_loc.card_id != loc.card_id or card_node.node.pos != t_pos:
            PosInterval(
                card_node.node,
                0.2,
                t_pos,
                blend=BlendType.EASE_OUT
            ).play()
            card_node.node.index = 0
            card_node.node.depth = 260 + loc.card_id
            return True
        return False

    def _callback_tableau(
            self,
            c_loc: common.TableLocation,
            loc: common.TableLocation,
            card_node: CardNode,
        ) -> bool:
        """Place card on Tableau."""
        if c_loc.visible is False and loc.visible is True and \
              c_loc.pile_id == loc.pile_id and c_loc.card_id == loc.card_id:
            RotationInterval(
                card_node.node,
                0.2,
                360,
                blend=BlendType.EASE_IN_OUT
            ).play()
            card_node.node.index = 0
            return True

        pile_size = len(self._table.table.tableau[loc.pile_id])
        offset = vec2.Vec2(0, self.v_offset(pile_size) * loc.card_id)
        t_pos = self._relative_positions.tableau[loc.pile_id] + offset
        if c_loc.area != loc.area or c_loc.pile_id != loc.pile_id or \
              c_loc.card_id != loc.card_id or card_node.node.pos != t_pos:
            PosInterval(
                card_node.node,
                0.2,
                t_pos,
                blend=BlendType.EASE_OUT
            ).play()
            card_node.node.index = 0 if loc.visible else 1
            card_node.node.depth = 200 + loc.card_id
            return True
        card_node.node.index = 0 if loc.visible else 1
        return False
