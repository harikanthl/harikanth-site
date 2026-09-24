"""
Pattern 15 — DP.

The film follows the card's own argument: hook -> the staircase recurrence -> the exponential
recursion tree -> the memo -> the table -> the state and its transition on House Robber ->
take-or-skip -> the shapes (LIS, two-sequence, interval) -> the forward-loop trap -> the empty
prefix -> complexity -> the recall card.

The visual spine is ONE state table filling in: `DPGrid` cells are computed from earlier
cells, an arrow runs from the dependency to the cell being written, and the fill order is the
whole moral of the card — look-back-two goes left to right, a knapsack row goes backwards, an
interval table goes by increasing length, and a pair state goes row by row.
"""

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    FadeIn,
    FadeOut,
    Indicate,
    Line,
    Restore,
    Text,
    VGroup,
    Write,
)

from house import (
    ACCENT,
    BODY_FS,
    GOOD,
    GONE,
    INK,
    MONO,
    MUTED,
    PANEL,
    PRIMARY,
    SMALL_FS,
    STROKE,
    WINDOW,
    bg,
    card,
    caption,
    headline,
    rule,
    stage_center,
    swap_rails,
)
from prebaked_voice import PrebakedVoiceMovingCameraScene
from shots import chip

PATTERN_SLUG = "dp"
TITLE = "Dynamic Programming"
SUMMARY = "Name the state, write the transition, fill in dependency order."
SCENE_CLASS = "DynamicProgramming"
POSTER_AT = 30.0

# The running example: the staircase from the card's own ELI5.
STAIRS = [1, 2, 3, 4, 5]
WAYS = [1, 2, 3, 5, 8]
NONE = "\u2009"  # a hair space: an empty cell still needs ink for the layout QA to see it

BEATS = [
    # 0 hook
    "Dynamic programming is recursion that remembers. The answer is not cleverer, it is "
    "computed once.",
    # 1 the job and the recurrence
    "How many ways can you climb these stairs, one step or two? The last hop was a one or "
    "a two, so ways to reach five equals ways to reach four plus three.",
    # 2 the exponential tree
    "As plain recursion that spawns a tree. The same question is asked again and again, "
    "thousands of times.",
    # 3 the memo
    "The first fix writes the answer down: a memo, checked before any work. Same "
    "recursion, no repeat questions.",
    # 4 the table
    "Then flip it. Fill the table bottom-up, smallest subproblem first. That fill order is "
    "just the reverse of the call order.",
    # 5 the state
    "So here is the whole skill: say the state in words. F of i is the most I can rob from "
    "houses zero to i.",
    # 6 the transition and base cases
    "The transition: skip house i, or rob it and add F of i minus two. Base case, no houses, "
    "answer zero.",
    # 7 order and space
    "Each cell reads the one before it and the one two back, so you can fill left to right "
    "and throw the rest away. Two variables, constant space.",
    # 8 take or skip: knapsack
    "Take it or skip it is the same shape with an item and a capacity. Row i reads only row "
    "i minus one, so one row is enough.",
    # 9 knapsack loop direction
    "But that row has to be filled backwards. Forwards, the cell you read already contains "
    "this item, so you take it twice.",
    # 10 two sequences
    "Two sequences means a state made of a pair, i and j. Each cell reads three neighbours, "
    "and row zero is the empty prefix.",
    # 11 interval DP
    "A range state, l to r, filled by increasing interval length, because every smaller "
    "interval inside it has to be ready first.",
    # 12 state too small
    "If the state cannot tell you what you need to decide the next step, it is too small. "
    "A wrong answer on a small case is a missing dimension.",
    # 13 empty prefix
    "And index zero usually means the empty thing, not the first thing. Mixing those up "
    "looks right on the example and fails the first hidden test.",
    # 14 complexity
    "Linear DP is n, and rolls to constant space. Knapsack is n times capacity. Two "
    "sequences is m times n. Interval is m cubed. All of it beats exponential.",
    # 15 recall
    "Name the state, write the transition, fill in dependency order.",
]

CHAPTERS = {
    0: "The hook",
    1: "The recurrence",
    2: "The exponential tree",
    3: "The memo",
    4: "The table",
    5: "Say the state",
    6: "The transition",
    7: "Fill order and space",
    8: "Take it or skip it",
    9: "Why backwards",
    10: "Two sequences",
    11: "Interval DP",
    12: "What goes wrong",
    14: "Complexity",
    15: "Recall",
}


# ---------------------------------------------------------------------------------------
# Local primitives
# ---------------------------------------------------------------------------------------
class _Table:
    """A state table that fills in cell by cell.

    Built here rather than from `shots.DPGrid`: that class never arranges the cells inside a
    row, so every column lands on the same point and the table renders as a single stack.
    The API used by the film (`set_value`, `focus`, `cell_at`) is kept the same.
    """

    ROWS = 0
    COLS = 0

    def __init__(self, values, *, cell: float = 0.56, buff: float = 0.06,
                 center=(0.0, -0.2)):
        self.values = [list(row) for row in values]
        self.rows = len(self.values)
        self.cols = len(self.values[0])
        self.cell = cell
        self.buff = buff
        self.center = center
        self.texts = {}
        self.cell_boxes = {}
        self.cells = VGroup()
        for row in self.values:
            row_group = VGroup()
            for _ in row:
                box = card(cell, cell, color=STROKE, fill=PANEL)
                row_group.add(VGroup(box))
            row_group.arrange(RIGHT, buff=buff)
            self.cells.add(row_group)
        self.cells.arrange(DOWN, buff=buff)
        self.cells.move_to([center[0], center[1], 0])

    # -- API ---------------------------------------------------------------------------
    def box(self, r: int, c: int):
        return self.cells[r][c][0]

    def cell_at(self, r: int, c: int):
        return self.cells[r][c]

    def set_value(self, r: int, c: int, value, color=INK, fs: int = SMALL_FS):
        box = self.box(r, c)
        t = Text(str(value), font=MONO, font_size=fs, color=color)
        if t.width > box.width - 0.08:
            t.scale_to_fit_width(box.width - 0.08)
        if t.height > box.height - 0.08:
            t.scale_to_fit_height(box.height - 0.08)
        t.move_to(box.get_center())
        self.cells[r][c].add(t)
        self.texts[(r, c)] = t
        self.cell_boxes[(r, c)] = box
        return t

    def build(self, color=INK):
        """Create every value in place, hidden, so the fill order can reveal them."""
        out = VGroup()
        for r in range(self.rows):
            for c in range(self.cols):
                out.add(self.set_value(r, c, self.values[r][c], color=color))
        for t in out:
            t.set_opacity(0.0)
        return out

    def show(self, r: int, c: int, *, color=None):
        t = self.texts[(r, c)]
        if color is not None:
            t.set_color(color)
        return t.animate.set_opacity(1.0)

    def focus(self, r: int, c: int, color=ACCENT, opacity: float = 0.3):
        return self.box(r, c).animate.set_stroke(color, width=2.4).set_fill(color,
                                                                            opacity=opacity)

    def dim(self, *cells, opacity: float = 0.3):
        return [self.texts[(r, c)].animate.set_opacity(opacity) for (r, c) in cells]

    def group(self):
        return self.cells


def _dep_arrow(table: _Table, src, dst, *, color=ACCENT, arc: float = 0.0,
               stroke: float = 3.0):
    """An arrow from the cell being read to the cell being written — the transition, drawn."""
    a = table.cell_at(*src)
    b = table.cell_at(*dst)
    kwargs = dict(buff=0.1, color=color, stroke_width=stroke,
                  max_tip_length_to_length_ratio=0.35)
    if arc:
        kwargs["path_arc"] = arc
    return Arrow(a.get_center(), b.get_center(), **kwargs)


def _dep_line(table: _Table, src, dst, *, color=ACCENT, arc: float = 0.0,
              stroke: float = 2.4):
    """A no-tip highlight for a dependency that is not the one being spoken about."""
    a = table.cell_at(*src)
    b = table.cell_at(*dst)
    kwargs = dict(color=color, stroke_width=stroke)
    if arc:
        kwargs["path_arc"] = arc
    return Line(a.get_center(), b.get_center(), **kwargs)


def _stack_chip(text: str, color=GOOD, fs: int = SMALL_FS):
    return chip(text, color=color, fs=fs)


class DynamicProgramming(PrebakedVoiceMovingCameraScene):
    # ---------------------------------------------------------------------------- setup
    def construct(self):
        bg(self)
        self._tables = []
        for i in range(len(BEATS)):
            self._sweep()
            getattr(self, f"_beat{i}")()

    # -------------------------------------------------------------------- stage lifecycle
    def _set_rails(self, head, cap):
        """`swap_rails`, then genuinely remove the outgoing rails (see `_vanish`)."""
        old = list(getattr(self, "_rails", []))
        swap_rails(self, head, cap)
        for m in old:
            if m in self.mobjects:
                self.remove(m)

    def _live(self, m):
        """The instance of `m` the scene is actually holding (introducers stage a copy)."""
        try:
            if m in self.mobjects:
                return m
            cx, cy = float(m.get_center()[0]), float(m.get_center()[1])
            w, h = float(m.width), float(m.height)
            want = getattr(m, "text", None)
            for cand in self.mobjects:
                if want is not None and getattr(cand, "text", None) != want:
                    continue
                if (abs(float(cand.get_center()[0]) - cx) < 0.2
                        and abs(float(cand.get_center()[1]) - cy) < 0.2
                        and abs(float(cand.width) - w) < 0.25
                        and abs(float(cand.height) - h) < 0.25):
                    return cand
        except Exception:
            pass
        return m

    def _sweep(self):
        """Drop anything left on the stage with no visible ink (the QA ignores opacity)."""
        rails = {id(m) for m in getattr(self, "_rails", [])}
        dead = []
        for m in list(self.mobjects):
            if id(m) in rails:
                continue
            try:
                if (float(m.get_fill_opacity()) <= 0.001
                        and float(m.get_stroke_opacity()) <= 0.001):
                    dead.append(m)
            except Exception:
                continue
        if dead:
            self.remove(*dead)

    def _remove_family(self, mobs):
        every = []
        for m in mobs:
            every += list(m.get_family())
        self.remove(*mobs, *every)

    def _vanish(self, *mobs, run_time: float = 0.35):
        """Fade the given mobjects out, then genuinely remove them and their families."""
        self.play(*[FadeOut(self._live(m)) for m in mobs], run_time=run_time)
        self._remove_family([self._live(m) for m in mobs])
        self._sweep()

    # ------------------------------------------------------------------------- utilities
    # ---------------------------------------------------------------------------- beats
    def _beat0(self):
        """Hook: the trade, named plainly, then the two costs as objects."""
        with self.voiceover(text=BEATS[0]) as tr:
            self._set_rails(headline("Recursion that remembers."),
                            caption("answer each subproblem once"))
            self.play(FadeIn(rule()), run_time=0.3)
            slow = chip("same question, again and again", color=GONE, fs=BODY_FS)
            fast = chip("computed once, looked up after", color=GOOD, fs=BODY_FS)
            VGroup(slow, fast).arrange(DOWN, buff=0.7).move_to(stage_center(0.0))
            self.play(FadeIn(slow, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(fast, shift=UP * 0.2), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._hook = VGroup(slow, fast)

    def _beat1(self):
        """The job and the recurrence, on the card's own staircase."""
        with self.voiceover(text=BEATS[1]) as tr:
            self._set_rails(headline("Ways to reach a step."),
                            caption("one step or two, at a time"))
            self._vanish(self._hook, run_time=0.3)
            steps = VGroup()
            for i, v in enumerate(STAIRS):
                box = card(0.62, 0.62, color=PRIMARY, fill=PANEL)
                lb = Text(str(v), font=MONO, font_size=BODY_FS, color=INK)
                lb.move_to(box.get_center())
                g = VGroup(box, lb)
                g.move_to([-3.4 + i * 1.0, 0.85, 0])
                steps.add(g)
            dots = Text("…", font=MONO, font_size=BODY_FS, color=MUTED)
            dots.next_to(steps[-1], RIGHT, buff=0.3)
            self.play(*[FadeIn(s, shift=UP * 0.15) for s in steps], lag_ratio=0.2,
                      run_time=min(1.4, max(0.7, tr.duration * 0.3)))
            self.play(FadeIn(dots), run_time=0.3)
            rec = Text("ways(5) = ways(4) + ways(3)", font=MONO, font_size=BODY_FS,
                       color=ACCENT)
            rec.move_to([0, -1.35, 0])
            seen = Text("a 1-step hop, or a 2-step hop", font=MONO, font_size=SMALL_FS,
                        color=MUTED)
            seen.next_to(rec, DOWN, buff=0.3)
            self.play(Write(rec), run_time=0.6)
            self.play(FadeIn(seen, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._stairs = VGroup(steps, dots, rec, seen)

    def _beat2(self):
        """Why the naive recursion is exponential: the tree asks the same question twice."""
        with self.voiceover(text=BEATS[2]) as tr:
            self._set_rails(headline("Plain recursion repeats itself."),
                            caption("the same subproblem, again and again"))
            self._vanish(self._stairs, run_time=0.3)
            pos = [
                (0, 0.0, 1.9), (1, -1.7, 1.05), (1, 1.7, 1.05),
                (2, -2.6, 0.2), (2, -0.9, 0.2), (2, 0.9, 0.2), (2, 2.6, 0.2),
            ]
            nodes = VGroup()
            for level, x, y in pos:
                circ = card(0.66, 0.5, color=PRIMARY, fill=PANEL)
                lb = Text(f"ways({5 - level})", font=MONO, font_size=15, color=INK)
                lb.move_to(circ.get_center())
                g = VGroup(circ, lb)
                g.move_to([x, y, 0])
                nodes.add(g)
            links = VGroup()
            for i, j in ((0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)):
                links.add(Line(nodes[i].get_center(), nodes[j].get_center(),
                               color=STROKE, stroke_width=2))
            self.play(FadeIn(links), run_time=0.4)
            self.play(*[FadeIn(n, shift=DOWN * 0.12) for n in nodes], lag_ratio=0.22,
                      run_time=min(1.6, max(0.8, tr.duration * 0.34)))
            dup = Text("ways(3) computed twice", font=MONO, font_size=SMALL_FS, color=GONE)
            dup.move_to([0, -2.6, 0])
            self.play(FadeIn(dup, shift=UP * 0.12), run_time=0.4)
            self.play(Indicate(nodes[3], color=GONE, scale_factor=1.12), run_time=0.5)
            self.play(Indicate(nodes[4], color=GONE, scale_factor=1.12), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._tree = VGroup(links, nodes, dup)

    def _beat3(self):
        """The memo: write the answer down the first time, read it after that."""
        with self.voiceover(text=BEATS[3]) as tr:
            self._set_rails(headline("Write the answer down."),
                            caption("a memo, checked before any work"))
            self._vanish(self._tree, run_time=0.3)
            self.tab = _Table([
                [NONE, "1", "2", "3", "4", "5"],
                [NONE, "1", "2", "3", "5", "8"],
            ], center=(0.0, -0.3))
            self.tab.build()
            grid = self.tab.group()
            self.play(FadeIn(grid), run_time=0.5)
            heads = VGroup()
            for c, lb in ((1, "ways(1)"), (2, "ways(2)")):
                t = Text(lb, font=MONO, font_size=SMALL_FS, color=MUTED)
                t.next_to(self.tab.cell_at(0, c), UP, buff=0.42)
                heads.add(t)
            self.play(FadeIn(heads, shift=DOWN * 0.1), run_time=0.4)
            # the two base cases land, then the tree's repeats read instead of recomputing
            self.play(self.tab.show(0, 1, color=GOOD), self.tab.show(1, 1, color=GOOD),
                      run_time=0.4)
            self.play(self.tab.show(0, 2, color=GOOD), self.tab.show(1, 2, color=GOOD),
                      run_time=0.4)
            memo = Text("memo:  ways(1) = 1,  ways(2) = 2", font=MONO, font_size=SMALL_FS,
                        color=GOOD)
            memo.move_to([0, -1.6, 0])
            self.play(FadeIn(memo, shift=UP * 0.12), run_time=0.4)
            hit = Text("ways(3):  hit, no work", font=MONO, font_size=SMALL_FS, color=WINDOW)
            hit.next_to(memo, DOWN, buff=0.22)
            self.play(FadeIn(hit), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._memo = VGroup(heads, memo, hit)

    def _beat4(self):
        """Tabulation: the same answers, filled smallest-first."""
        with self.voiceover(text=BEATS[4]) as tr:
            self._set_rails(headline("Flip it: fill the table bottom-up."),
                            caption("smallest subproblem first"))
            self._vanish(self._memo, run_time=0.3)
            self.play(self.tab.show(0, 3, color=WINDOW), self.tab.show(1, 3, color=WINDOW),
                      run_time=0.35)
            self.play(self.tab.show(0, 4, color=WINDOW), self.tab.show(1, 4, color=WINDOW),
                      run_time=0.35)
            self.play(self.tab.show(0, 5, color=GOOD), self.tab.show(1, 5, color=GOOD),
                      run_time=0.4)
            self.play(Indicate(self.tab.box(1, 5), color=GOOD, scale_factor=1.1),
                      run_time=0.5)
            order = Text("fill order = reverse of the call order", font=MONO,
                         font_size=SMALL_FS, color=MUTED)
            order.move_to([0, -1.6, 0])
            self.play(FadeIn(order, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._tabbed = order

    def _beat5(self):
        """The state, in words — House Robber, the card's worked example."""
        with self.voiceover(text=BEATS[5]) as tr:
            self._set_rails(headline("Say the state in words."),
                            caption("F(i) = best from houses 0..i"))
            self._vanish(self.tab.group(), self._tabbed, run_time=0.3)
            self.rob = _Table([
                [NONE, "2", "7", "9", "3", "1"],
                [NONE, NONE, NONE, NONE, NONE, NONE],
                ["0", NONE, NONE, NONE, NONE, NONE],
            ], center=(0.0, 0.55))
            self.rob.build()
            self.play(FadeIn(self.rob.group()), run_time=0.5)
            hlab = Text("houses", font=MONO, font_size=SMALL_FS, color=MUTED)
            hlab.next_to(self.rob.cell_at(0, 0), LEFT, buff=0.2)
            dlab = Text("F(i)", font=MONO, font_size=SMALL_FS, color=WINDOW)
            dlab.next_to(self.rob.cell_at(2, 0), LEFT, buff=0.2)
            self.play(FadeIn(hlab), FadeIn(dlab), run_time=0.4)
            self.play(*[self.rob.show(0, c, color=PRIMARY) for c in range(1, 6)],
                      run_time=0.4)
            self.play(self.rob.show(2, 0, color=GOOD), run_time=0.3)
            self.camera.frame.save_state()  # bare: stores, doesn't animate
            self.play(
                self.camera.auto_zoom([self.rob.group()], margin=1.15),
                run_time=min(0.9, max(0.5, tr.duration * 0.22)),
            )
            self.play(Restore(self.camera.frame), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._state = VGroup(hlab, dlab)

    def _beat6(self):
        """The transition and the base case, drawn between the table's own cells."""
        with self.voiceover(text=BEATS[6]) as tr:
            self._set_rails(headline("Two choices: skip it or rob it."),
                            caption("max(F(i-1), F(i-2) + nums[i])"))
            for c, col in ((1, GOOD), (2, WINDOW), (3, WINDOW)):
                self.play(self.rob.show(2, c, color=col), run_time=0.3)
            self.play(Indicate(self.rob.box(2, 3), color=ACCENT, scale_factor=1.1),
                      run_time=0.45)
            skip = _dep_arrow(self.rob, (2, 2), (2, 3), color=ACCENT, arc=0.3)
            take = _dep_line(self.rob, (2, 1), (2, 3), color=WINDOW, arc=-0.3)
            self.play(FadeIn(skip), run_time=0.35)
            self.play(FadeIn(take), run_time=0.35)
            note = VGroup(
                Text("skip it  →  F(2) = 2", font=MONO, font_size=SMALL_FS, color=ACCENT),
                Text("rob it   →  F(1) + 9 = 11", font=MONO, font_size=SMALL_FS, color=WINDOW),
                Text("base case: F(0) = 0, no houses", font=MONO, font_size=SMALL_FS,
                     color=GOOD),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([0, -2.2, 0])
            self.play(*[FadeIn(n, shift=RIGHT * 0.12) for n in note], lag_ratio=0.3,
                      run_time=min(1.4, max(0.7, tr.duration * 0.3)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._trans = VGroup(skip, take, note)

    def _beat7(self):
        """Look-back-two means rolling variables: the table shrinks to two cells."""
        with self.voiceover(text=BEATS[7]) as tr:
            self._set_rails(headline("Look back two, roll to two variables."),
                            caption("fill left to right, O(1) space"))
            self._vanish(self._trans, run_time=0.3)
            dim = [(0, c) for c in range(6)] + [(2, c) for c in (1, 2)]
            self.play(*self.rob.dim(*dim, opacity=0.16), run_time=0.5)
            self.play(self.rob.focus(2, 2, color=WINDOW), self.rob.focus(2, 3, color=ACCENT),
                      run_time=0.4)
            chips = VGroup(
                _stack_chip("prev2", color=WINDOW),
                _stack_chip("prev1", color=ACCENT),
            )
            chips[0].next_to(self.rob.cell_at(2, 2), UP, buff=0.3)
            chips[1].next_to(self.rob.cell_at(2, 3), UP, buff=0.3)
            self.play(FadeIn(chips, shift=DOWN * 0.12), run_time=0.45)
            cut = Text("the rest of the table is never read again", font=MONO,
                       font_size=SMALL_FS, color=GONE)
            cut.move_to([-2.6, -2.6, 0])
            self.play(FadeIn(cut, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._roll = VGroup(chips, cut)

    def _beat8(self):
        """Take-or-skip with an item and a capacity: the 0/1 knapsack grid."""
        with self.voiceover(text=BEATS[8]) as tr:
            self._set_rails(headline("Add an item and a capacity."),
                            caption("take it, or skip it"))
            self._vanish(self.rob.group(), self._state, self._roll, run_time=0.35)
            knap = [
                [NONE, "w1 v1", "w1 v1", "w3 v4", "w3 v4", "w4 v5"],
                [NONE, "0", "0", "0", "0", "0"],
                [NONE, "1", "1", "1", "1", "1"],
                [NONE, "1", "1", "4", "4", "4"],
                [NONE, "1", "1", "4", "5", "5"],
            ]
            self.knap = _Table(knap, cell=0.6, center=(0.0, -0.3))
            self.knap.build()
            self.play(FadeIn(self.knap.group()), run_time=0.5)
            self.play(self.knap.show(0, 1, color=GOOD), self.knap.show(0, 2, color=GOOD),
                      self.knap.show(0, 3, color=GOOD), self.knap.show(0, 4, color=GOOD),
                      self.knap.show(0, 5, color=GOOD), run_time=0.5)
            note = Text("capacity  →", font=MONO, font_size=SMALL_FS, color=MUTED)
            note.next_to(self.knap.group(), RIGHT, buff=0.3)
            self.play(FadeIn(note), run_time=0.3)
            for row in (1, 2, 3, 4):
                self.play(*[self.knap.show(row, c, color=WINDOW if row < 4 else GOOD)
                            for c in range(1, 6)], run_time=0.3)
            skip = Text("row i reads only row i - 1", font=MONO, font_size=SMALL_FS,
                        color=ACCENT)
            skip.move_to([-3.6, -2.65, 0])
            self.play(FadeIn(skip, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._knap = VGroup(note, skip)

    def _beat9(self):
        """The trap: a forward inner loop takes the same item twice."""
        with self.voiceover(text=BEATS[9]) as tr:
            self._set_rails(headline("Fill that row backwards."),
                            caption("forwards = the item is used twice"))
            self._vanish(self.knap.group(), self._knap, run_time=0.3)
            bad = Text("for c in range(w, W+1):     ✗", font=MONO, font_size=BODY_FS,
                       color=GONE)
            good = Text("for c in range(W, w-1, -1):  ✓", font=MONO, font_size=BODY_FS,
                        color=GOOD)
            VGroup(bad, good).arrange(DOWN, buff=0.8).move_to([0, 1.1, 0])
            why = Text("forwards, dp[c-w] already holds THIS item", font=MONO,
                       font_size=SMALL_FS, color=MUTED)
            why.move_to([0, -1.9, 0])
            self.play(Write(bad), run_time=0.55)
            self.play(Indicate(bad, color=GONE, scale_factor=1.06), run_time=0.5)
            self.play(Write(good), run_time=0.55)
            self.play(FadeIn(why, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._back = VGroup(bad, good, why)

    def _beat10(self):
        """Two sequences: the state is a pair, and each cell reads three neighbours."""
        with self.voiceover(text=BEATS[10]) as tr:
            self._set_rails(headline("Two sequences: the state is a pair."),
                            caption("dp[i][j], three neighbours"))
            self._vanish(self._back, run_time=0.35)
            values = [
                [NONE, NONE, "a", "b", "c"],
                [NONE, "0", "0", "0", "0"],
                ["x", "0", "1", "1", "1"],
                ["y", "0", "1", "1", "1"],
                ["z", "0", "1", "2", "2"],
            ]
            self.lcs = _Table(values, cell=0.62, center=(0.0, -0.15))
            self.lcs.build()
            self.play(FadeIn(self.lcs.group()), run_time=0.5)
            for r in range(5):
                self.play(self.lcs.show(r, 0, color=GOOD), run_time=0.16)
            for c in range(5):
                self.play(self.lcs.show(0, c, color=GOOD), run_time=0.16)
            self.play(self.lcs.focus(3, 3, color=ACCENT), run_time=0.35)
            deps = VGroup(
                _dep_line(self.lcs, (2, 3), (3, 3), color=WINDOW),
                _dep_line(self.lcs, (3, 2), (3, 3), color=WINDOW),
                _dep_arrow(self.lcs, (2, 2), (3, 3), color=ACCENT),
            )
            self.play(FadeIn(deps), run_time=0.5)
            pre = Text("row 0 and col 0 are the EMPTY prefix", font=MONO, font_size=SMALL_FS,
                       color=GOOD)
            pre.move_to([0, -2.6, 0])
            self.play(FadeIn(pre, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._lcs = VGroup(deps, pre)

    def _beat11(self):
        """Interval DP: a range state, filled by increasing length."""
        with self.voiceover(text=BEATS[11]) as tr:
            self._set_rails(headline("A range state fills by length."),
                            caption("every smaller interval first"))
            self._vanish(self.lcs.group(), self._lcs, run_time=0.35)
            values = [
                ["cuts", "0", "2", "4", "7"],
                ["0", NONE, "2", "4", "7"],
                ["2", NONE, NONE, "2", "5"],
                ["4", NONE, NONE, NONE, "3"],
                ["7", NONE, NONE, NONE, NONE],
            ]
            self.tab2 = _Table(values, cell=0.56, center=(-0.6, -0.15))
            self.tab2.build()
            self.play(FadeIn(self.tab2.group()), run_time=0.5)
            for r in range(4):
                self.play(self.tab2.show(r, 0, color=GOOD), run_time=0.2)
            for c in range(4):
                self.play(self.tab2.show(c, c + 1, color=WINDOW), run_time=0.22)
            for r in range(2):
                self.play(self.tab2.show(r, r + 2, color=WINDOW), run_time=0.22)
            self.play(self.tab2.show(0, 3, color=ACCENT), run_time=0.25)
            self.play(self.tab2.show(0, 4, color=GOOD), run_time=0.25)
            length = Text("length 1  →  2  →  3  →  4", font=MONO, font_size=SMALL_FS,
                          color=MUTED)
            length.move_to([3.2, -2.3, 0])
            self.play(FadeIn(length, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._interval = length

    def _beat12(self):
        """What goes wrong #1: a state too small to decide the next step."""
        with self.voiceover(text=BEATS[12]) as tr:
            self._set_rails(headline("A state that can't decide is too small."),
                            caption("small case wrong = missing dimension"))
            self._vanish(self.tab2.group(), self._interval, run_time=0.35)
            wrong = VGroup(
                Text("F(i) = best so far, ignoring i - 1", font=MONO, font_size=BODY_FS,
                     color=GONE),
                Text("two houses in a row get robbed", font=MONO, font_size=SMALL_FS,
                     color=MUTED),
            ).arrange(DOWN, buff=0.22)
            right = VGroup(
                Text("the state must reach back to i - 2", font=MONO, font_size=BODY_FS,
                     color=GOOD),
                Text("skip, or rob and add F(i - 2)", font=MONO, font_size=SMALL_FS,
                     color=INK),
            ).arrange(DOWN, buff=0.22)
            VGroup(wrong, right).arrange(DOWN, buff=1.0).move_to(stage_center(-0.1))
            self.play(FadeIn(wrong[0], shift=UP * 0.14), run_time=0.45)
            self.play(FadeIn(wrong[1]), run_time=0.35)
            self.play(FadeIn(right[0], shift=UP * 0.14), run_time=0.45)
            self.play(FadeIn(right[1]), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._too_small = VGroup(wrong, right)

    def _beat13(self):
        """What goes wrong #2: index zero is the empty thing, not the first thing."""
        with self.voiceover(text=BEATS[13]) as tr:
            self._set_rails(headline("Index zero means the empty thing."),
                            caption("dp[i][j] describes a[:i], b[:j]"))
            self._vanish(self._too_small, run_time=0.35)
            values = [
                [NONE, NONE, "a", "b"],
                [NONE, "0", "0", "0"],
                ["x", "0", NONE, NONE],
                ["y", "0", NONE, NONE],
            ]
            self.pre = _Table(values, cell=0.56, center=(-2.4, -0.15))
            self.pre.build()
            grid = self.pre.group()
            self.play(FadeIn(grid), run_time=0.5)
            self.play(*[self.pre.show(r, c, color=GOOD) for r, c in
                        ((1, 1), (1, 2), (1, 3), (2, 1), (3, 1))], run_time=0.6)
            self.play(self.pre.focus(1, 1, color=GOOD), run_time=0.3)
            empty = Text("dp[1][1] = LCS of \"\" and \"\"", font=MONO, font_size=SMALL_FS,
                         color=GOOD)
            empty.next_to(grid, UP, buff=0.25)
            trap = VGroup(
                Text("the character compared is a[i-1], not a[i]", font=MONO,
                     font_size=SMALL_FS, color=GONE),
                Text("right on the example, wrong on the first hidden test", font=MONO,
                     font_size=SMALL_FS, color=MUTED),
            ).arrange(DOWN, buff=0.26).move_to([3.0, -0.2, 0])
            self.play(FadeIn(empty), run_time=0.35)
            self.play(FadeIn(trap[0], shift=RIGHT * 0.15), run_time=0.4)
            self.play(FadeIn(trap[1]), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._prefix = VGroup(empty, trap)

    def _beat14(self):
        """Complexity, stated cold, row by row."""
        with self.voiceover(text=BEATS[14]) as tr:
            self._set_rails(headline("Know the cost of each shape."),
                            caption("all of it beats exponential"))
            self._vanish(self.pre.group(), self._prefix, run_time=0.35)
            rows = [
                ("stairs, house robber", "O(n)", "O(1) rolling", GOOD),
                ("0/1 knapsack, subset sum", "O(n·W)", "O(W) one row", GOOD),
                ("LIS", "O(n²)  ·  O(n log n)", "O(n)", WINDOW),
                ("LCS, unique paths", "O(m·n)", "O(n) one row", WINDOW),
                ("cut a stick, burst balloons", "O(m³)", "O(m²)", WINDOW),
            ]
            table = VGroup()
            for name, tm, sp, col in rows:
                table.add(VGroup(
                    Text(name, font=MONO, font_size=SMALL_FS, color=INK),
                    Text(tm, font=MONO, font_size=SMALL_FS, color=col),
                    Text(sp, font=MONO, font_size=SMALL_FS, color=MUTED),
                ).arrange(RIGHT, buff=0.5))
            table.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            if table.width > 12.4:
                table.scale_to_fit_width(12.4)
            table.move_to(stage_center(-0.1))
            self.play(*[FadeIn(r, shift=RIGHT * 0.15) for r in table], lag_ratio=0.26,
                      run_time=min(1.7, max(0.9, tr.duration * 0.4)))
            brute = Text("brute force was O(2ⁿ)", font=MONO, font_size=SMALL_FS, color=GONE)
            brute.move_to([0, -2.6, 0])
            self.play(FadeIn(brute, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._complex = VGroup(table, brute)

    def _beat15(self):
        """Recall card: the four steps, in one line the viewer leaves with."""
        with self.voiceover(text=BEATS[15]) as tr:
            self._set_rails(headline("Name it. Write it. Fill it."),
                            caption("state · transition · order"))
            self._vanish(self._complex, run_time=0.3)
            box = card(10.4, 2.1, color=ACCENT, fill=PANEL)
            box.move_to(stage_center(-0.05))
            top = Text("Dynamic Programming", font=MONO, font_size=30, color=ACCENT)
            mid = Text("1 say the state   2 write the recurrence   3 memo   4 table, then roll",
                       font=MONO, font_size=SMALL_FS, color=INK)
            sub = Text("index 0 is the empty thing  ·  fill in dependency order",
                       font=MONO, font_size=SMALL_FS, color=MUTED)
            VGroup(top, mid, sub).arrange(DOWN, buff=0.28).move_to(box.get_center())
            self.play(FadeIn(box, scale=0.96), run_time=0.45)
            self.play(Write(top), run_time=0.5)
            self.play(FadeIn(mid), run_time=0.4)
            self.play(FadeIn(sub), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
