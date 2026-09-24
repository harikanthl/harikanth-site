"""
The shot library: reusable, animated diagram primitives the 15 pattern films compose from.

Every shot returns a plain manim mobject (or a small holder with named parts) so scene code
reads like a shot list rather than geometry. Each is drawn to the house palette and stays
inside the safe box; callers place the result, they don't rebuild it.

Design rules kept here so scenes can't get them wrong:
  * bars share a baseline (GrowFromEdge(DOWN)), never FadeIn;
  * labels sit BESIDE a shape (next_to + buff), never move_to(shape.get_center());
  * highlight in place (`Indicate` / `.animate.set_color`), never a duplicate overlay;
  * text inside a box is fit to the box before it's centred.
"""

from manim import (
    DOWN,
    LEFT,
    ORIGIN,
    RIGHT,
    UP,
    Arrow,
    Circle,
    DashedLine,
    Dot,
    GrowArrow,
    GrowFromEdge,
    Line,
    RoundedRectangle,
    Text,
    VGroup,
    VMobject,
)

from house import (
    ACCENT,
    BODY_FS,
    GONE,
    GOOD,
    INK,
    MONO,
    MONO_FS,
    MUTED,
    PANEL,
    PRIMARY,
    SMALL_FS,
    STROKE,
    WINDOW,
    card,
)

CELL = 0.62
CELL_BUFF = 0.07


def _txt(value, color=INK, fs=MONO_FS, mono=True) -> Text:
    return Text(str(value), font=MONO if mono else "Helvetica Neue", font_size=fs, color=color)


def _fit_inside(t: Text, box, pad: float = 0.12) -> Text:
    """Downscale-only fit of text into a box, then centre it (guide rule)."""
    if t.width > box.width - pad:
        t.scale_to_fit_width(box.width - pad)
    if t.height > box.height - pad:
        t.scale_to_fit_height(box.height - pad)
    t.move_to(box.get_center())
    return t


# --------------------------------------------------------------------------------------
# ArrayRow — the workhorse: a row of cells + an index rail + pointer/window/mark helpers.
# --------------------------------------------------------------------------------------
class ArrayRow:
    """A row of value cells with an index rail.

    `values` may contain None for a deliberately empty slot. Cells are addressable by index
    so a scene can animate one cell without rebuilding the row.
    """

    def __init__(
        self,
        values,
        *,
        cell: float = CELL,
        buff: float = CELL_BUFF,
        color=STROKE,
        fill=PANEL,
        fs: int = MONO_FS,
        show_index: bool = True,
        index_fs: int = SMALL_FS,
        max_width: float = 11.6,
    ):
        self.values = list(values)
        self.cell_size = cell
        self.cells = VGroup()
        self.boxes = []
        self.texts = []
        for v in self.values:
            box = card(cell, cell, color=color, fill=fill)
            self.boxes.append(box)
            if v is None:
                self.cells.add(VGroup(box))
                self.texts.append(None)
            else:
                t = _txt(v, fs=fs)
                _fit_inside(t, box)
                self.texts.append(t)
                self.cells.add(VGroup(box, t))
        self.cells.arrange(RIGHT, buff=buff)
        if self.cells.width > max_width:
            self.cells.scale_to_fit_width(max_width)
            self.cell_size = cell * (max_width / (cell * len(values) + buff * (len(values) - 1)))

        self.idx = VGroup()
        if show_index:
            for i in range(len(self.values)):
                lb = Text(str(i), font=MONO, font_size=index_fs, color=MUTED)
                lb.next_to(self.cells[i], DOWN, buff=0.14)
                self.idx.add(lb)
        self.group = VGroup(self.cells, self.idx)

    # -- geometry ------------------------------------------------------------------
    def cell(self, i: int):
        return self.cells[i]

    def box(self, i: int) -> VMobject:
        return self.boxes[i]

    def center_of(self, i: int):
        return self.cells[i].get_center()

    def top_of(self, i: int):
        return self.cells[i].get_top()

    def bottom_of(self, i: int):
        return self.cells[i].get_bottom()

    def set_value(self, i: int, value, color=INK):
        """Replace cell i's text in place — used when values change during a beat.

        Note: manim's `Mobject.replace(mobject, dim_to_match)` takes the thing to copy
        geometry FROM, so swapping a child by calling `cell.replace(old, new)` passes the new
        Text as `dim_to_match` and raises TypeError. Remove-then-add is the correct swap, and
        it also keeps the cell's draw order stable.
        """
        box = self.boxes[i]
        new = _txt(value, color=color)
        _fit_inside(new, box)
        old = self.texts[i]
        self.texts[i] = new
        if old is not None:
            self.cells[i].remove(old)
        new.move_to(box.get_center())
        self.cells[i].add(new)
        return new

    def index_labels(self, i: int) -> Text:
        return self.idx[i]

    # -- emphasis (in place, never a duplicate overlay) -----------------------------
    def focus(self, i: int, color=ACCENT, fill_opacity: float = 0.30):
        return [
            self.boxes[i].animate.set_stroke(color=color, width=2.6).set_fill(
                color, opacity=fill_opacity
            )
        ]

    def mark_gone(self, i: int, opacity: float = 0.16):
        """Eliminated candidate: dimmed, red-stroked, still legible."""
        anims = [
            self.boxes[i].animate.set_stroke(color=GONE, width=1.8).set_fill(
                GONE, opacity=opacity
            )
        ]
        if self.texts[i] is not None:
            anims.append(self.texts[i].animate.set_color(MUTED))
        return anims

    def mark_good(self, i: int, opacity: float = 0.32):
        return [
            self.boxes[i].animate.set_stroke(color=GOOD, width=2.6).set_fill(
                GOOD, opacity=opacity
            )
        ]

    def reset(self, i: int, color=STROKE, fill=PANEL):
        anims = [self.boxes[i].animate.set_stroke(color=color, width=1.6).set_fill(fill, opacity=1.0)]
        if self.texts[i] is not None:
            anims.append(self.texts[i].animate.set_color(INK))
        return anims

    def reset_all(self, color=STROKE, fill=PANEL):
        anims = []
        for i in range(len(self.values)):
            anims += self.reset(i, color=color, fill=fill)
        return anims


def pointer(row: ArrayRow, i: int, text: str, *, color=ACCENT, above: bool = True,
            fs: int = BODY_FS) -> VGroup:
    """A labelled pointer chevron aimed at cell i — the thing the narration just named."""
    cell = row.cell(i)
    if above:
        tip = cell.get_top()
        arrow = Arrow(
            tip + UP * 0.62, tip + UP * 0.1, buff=0, color=color, stroke_width=3.4,
            max_tip_length_to_length_ratio=0.28,
        )
        lb = Text(text, font=MONO, font_size=fs, color=color)
        lb.next_to(arrow, UP, buff=0.1)
    else:
        tip = cell.get_bottom()
        arrow = Arrow(
            tip + DOWN * 0.62, tip + DOWN * 0.1, buff=0, color=color, stroke_width=3.4,
            max_tip_length_to_length_ratio=0.28,
        )
        lb = Text(text, font=MONO, font_size=fs, color=color)
        lb.next_to(arrow, DOWN, buff=0.1)
    return VGroup(arrow, lb)


def window_over(row: ArrayRow, lo: int, hi: int, *, color=WINDOW, opacity: float = 0.22,
                label: str | None = None) -> VGroup:
    """A translucent span covering cells lo..hi (inclusive) — the active window/subarray."""
    left = row.cell(lo).get_left()[0] - 0.05
    right = row.cell(hi).get_right()[0] + 0.05
    top = max(row.cell(lo).get_top()[1], row.cell(hi).get_top()[1]) + 0.09
    bottom = min(row.cell(lo).get_bottom()[1], row.cell(hi).get_bottom()[1]) - 0.09
    rect = RoundedRectangle(
        corner_radius=0.13,
        width=right - left,
        height=top - bottom,
        stroke_color=color,
        stroke_width=2.2,
        fill_color=color,
        fill_opacity=opacity,
    )
    rect.move_to([(left + right) / 2, (top + bottom) / 2, 0])
    parts = VGroup(rect)
    if label:
        lb = Text(label, font=MONO, font_size=SMALL_FS, color=color)
        lb.next_to(rect, UP, buff=0.14)
        parts.add(lb)
    return parts


def target_band(value_text, *, color=INK, fs: int = 30, y: float = 2.55) -> VGroup:
    """The 'we want this' readout that sits under the headline for the whole film."""
    t = Text(value_text, font=MONO, font_size=fs, color=color)
    t.move_to([0, y, 0])
    return VGroup(t)


# --------------------------------------------------------------------------------------
# Bars — bars share a baseline; label BELOW after arranging so the baseline stays true.
# --------------------------------------------------------------------------------------
class BarSet:
    def __init__(self, values, *, bar_w: float = 0.52, buff: float = 0.16,
                 height: float = 2.6, color=PRIMARY, label_fs: int = SMALL_FS,
                 show_index: bool = True, max_width: float = 11.4):
        self.values = list(values)
        peak = max(self.values) if any(self.values) else 1
        self.bars = VGroup()
        self.bar_w = bar_w
        for v in self.values:
            h = max(0.06, height * (v / peak if peak else 0))
            bar = RoundedRectangle(
                corner_radius=0.05, width=bar_w, height=h,
                stroke_color=color, stroke_width=1.4,
                fill_color=color, fill_opacity=0.55,
            )
            bar._target_h = h
            self.bars.add(bar)
        self.bars.arrange(RIGHT, buff=buff, aligned_edge=DOWN)
        if self.bars.width > max_width:
            self.bars.scale_to_fit_width(max_width)
        self.baseline = Line(
            self.bars.get_left() + LEFT * 0.12,
            self.bars.get_right() + RIGHT * 0.12,
            color=STROKE, stroke_width=2,
        ).align_to(self.bars, DOWN)
        self.labels = VGroup()
        if show_index:
            for i, bar in enumerate(self.bars):
                lb = Text(str(i), font=MONO, font_size=label_fs, color=MUTED)
                lb.next_to(bar, DOWN, buff=0.14)
                lb.align_to(bar, DOWN)
                self.labels.add(lb)
        self.group = VGroup(self.baseline, self.bars, self.labels)

    def grow(self):
        return [GrowFromEdge(b, DOWN) for b in self.bars]

    def bar(self, i: int):
        return self.bars[i]


# --------------------------------------------------------------------------------------
# LinkedList — nodes chained by arrows; `break_at` shows a reversal in progress.
# --------------------------------------------------------------------------------------
def node_chain(labels, *, node: float = 0.72, buff: float = 0.62, color=PRIMARY,
               fs: int = MONO_FS) -> VGroup:
    nodes = VGroup()
    for lb in labels:
        c = Circle(radius=node / 2, stroke_color=color, stroke_width=2, fill_color=PANEL,
                   fill_opacity=1.0)
        t = _txt(lb, fs=fs)
        _fit_inside(t, c)
        nodes.add(VGroup(c, t))
    nodes.arrange(RIGHT, buff=buff)
    arrows = VGroup()
    for i in range(len(labels) - 1):
        a = Arrow(
            nodes[i].get_right() + RIGHT * 0.04,
            nodes[i + 1].get_left() + LEFT * 0.04,
            buff=0, color=MUTED, stroke_width=2.6, max_tip_length_to_length_ratio=0.3,
        )
        arrows.add(a)
    return VGroup(nodes, arrows)


def arrow_between(a, b, *, color=ACCENT, curved: float = 0.0, stroke: float = 3.0) -> Arrow:
    kwargs = dict(buff=0.06, color=color, stroke_width=stroke,
                  max_tip_length_to_length_ratio=0.3)
    if curved:
        kwargs["path_arc"] = curved
    return Arrow(a.get_center(), b.get_center(), **kwargs)


# --------------------------------------------------------------------------------------
# Hash buckets — key → bucket list, for hash-map pattern.
# --------------------------------------------------------------------------------------
def hash_buckets(keys, *, bucket_w: float = 1.5, row_h: float = 0.52,
                 buff: float = 0.16) -> VGroup:
    rows = VGroup()
    for k in keys:
        box = card(bucket_w, row_h, color=STROKE, fill=PANEL)
        t = _txt(k, fs=SMALL_FS)
        _fit_inside(t, box, pad=0.1)
        rows.add(VGroup(box, t))
    rows.arrange(DOWN, buff=buff, aligned_edge=LEFT)
    return rows


# --------------------------------------------------------------------------------------
# Tree — a perfect binary tree layout with straight edges; returns holder with node list.
# --------------------------------------------------------------------------------------
class TreeViz:
    def __init__(self, levels: int, *, radius: float = 0.30, v_gap: float = 1.15,
                 label_fs: int = SMALL_FS):
        self.positions = []
        self.nodes = VGroup()
        self.edges = VGroup()
        n = 2 ** levels - 1
        # x positions: level L has 2^L nodes spread evenly
        for L in range(levels):
            count = 2 ** L
            span = 8.4
            row = []
            for i in range(count):
                x = -span / 2 + span * (i + 0.5) / count
                y = -(L * v_gap)
                row.append([x, y, 0])
            self.positions.append(row)
        for L, row in enumerate(self.positions):
            for x, y, _ in row:
                c = Circle(radius=radius, stroke_color=PRIMARY, stroke_width=2,
                           fill_color=PANEL, fill_opacity=1.0)
                c.move_to([x, y, 0])
                self.nodes.add(c)
        idx = 0
        starts = []
        for L in range(levels):
            starts.append(idx)
            idx += 2 ** L
        for L in range(levels - 1):
            for i in range(2 ** L):
                parent = self.nodes[starts[L] + i]
                for child_off in (0, 1):
                    child = self.nodes[starts[L + 1] + 2 * i + child_off]
                    self.edges.add(
                        Line(parent.get_center(), child.get_center(), color=STROKE,
                             stroke_width=2.0)
                    )
        self.group = VGroup(self.edges, self.nodes)


# --------------------------------------------------------------------------------------
# Graph — nodes at explicit coords with optional directed edges.
# --------------------------------------------------------------------------------------
def graph_viz(coords: dict, edges, *, radius: float = 0.32, color=PRIMARY,
              directed: bool = False) -> VGroup:
    nodes = {}
    node_mobs = VGroup()
    for name, (x, y) in coords.items():
        c = Circle(radius=radius, stroke_color=color, stroke_width=2.2, fill_color=PANEL,
                   fill_opacity=1.0)
        c.move_to([x, y, 0])
        t = _txt(name, fs=SMALL_FS)
        _fit_inside(t, c, pad=0.06)
        nodes[name] = VGroup(c, t)
        node_mobs.add(nodes[name])
    edge_mobs = VGroup()
    for a, b in edges:
        A, B = nodes[a], nodes[b]
        if directed:
            edge_mobs.add(arrow_between(A, B, color=MUTED, stroke=2.2))
        else:
            edge_mobs.add(Line(A.get_center(), B.get_center(), color=STROKE, stroke_width=2.2))
    return VGroup(edge_mobs, node_mobs)


# --------------------------------------------------------------------------------------
# DP grid — a table that fills in; cells addressed by (r, c).
# --------------------------------------------------------------------------------------
class DPGrid:
    def __init__(self, rows: int, cols: int, *, cell: float = 0.58, buff: float = 0.05,
                 fill=PANEL):
        self.rows, self.cols = rows, cols
        self.cells = VGroup()
        self.boxes = []
        self.texts = []
        for r in range(rows):
            row = VGroup()
            for c in range(cols):
                box = card(cell, cell, color=STROKE, fill=fill)
                self.boxes.append(box)
                self.texts.append(None)
                row.add(VGroup(box))
            # Each row must be laid out RIGHT before the rows are stacked DOWN — without this
            # every cell in a row sits on the same point and the table renders as one column.
            row.arrange(RIGHT, buff=buff)
            self.cells.add(row)
        self.cells.arrange(DOWN, buff=buff)
        self.group = self.cells

    def box(self, r: int, c: int):
        return self.cells[r][c][0]

    def set_value(self, r: int, c: int, value, color=INK, fs: int = SMALL_FS):
        box = self.box(r, c)
        t = _txt(value, fs=fs, color=color)
        _fit_inside(t, box, pad=0.08)
        self.cells[r][c].add(t)
        self.texts[r * self.cols + c] = t
        return t

    def focus(self, r: int, c: int, color=ACCENT, opacity: float = 0.3):
        return self.box(r, c).animate.set_stroke(color, width=2.4).set_fill(color, opacity=opacity)


# --------------------------------------------------------------------------------------
# Interval track — intervals as bars on a shared number line (merge-intervals pattern).
# --------------------------------------------------------------------------------------
def interval_track(intervals, *, length: float = 10.0, height: float = 0.42,
                   buff: float = 0.24, lo: float | None = None, hi: float | None = None,
                   color=PRIMARY) -> VGroup:
    lo = min(s for s, _ in intervals) if lo is None else lo
    hi = max(e for _, e in intervals) if hi is None else hi
    span = max(hi - lo, 1)
    scale = length / span
    bars = VGroup()
    for (s, e) in intervals:
        w = max(0.14, (e - s) * scale)
        bar = RoundedRectangle(corner_radius=0.07, width=w, height=height,
                               stroke_color=color, stroke_width=1.6,
                               fill_color=color, fill_opacity=0.5)
        bars.add(bar)
    bars.arrange(DOWN, buff=buff, aligned_edge=LEFT)
    # position each bar horizontally by its start value
    for bar, (s, _e) in zip(bars, intervals):
        bar.shift(RIGHT * ((s - lo) * scale))
    axis = Line(LEFT * 0.1, RIGHT * (length + 0.1), color=STROKE, stroke_width=2)
    axis.next_to(bars, DOWN, buff=0.3).align_to(bars, LEFT)
    return VGroup(bars, axis)


def chip(text: str, *, color=PRIMARY, fs: int = BODY_FS, pad_w: float = 0.34):
    """A small rounded label — used for complexity readouts and recall cards."""
    t = Text(text, font=MONO, font_size=fs, color=color)
    box = card(t.width + 2 * pad_w, t.height + 0.3, color=color, fill=PANEL)
    t.move_to(box.get_center())
    return VGroup(box, t)
