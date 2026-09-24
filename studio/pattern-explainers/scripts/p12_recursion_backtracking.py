"""
Pattern 12 — Recursion and Backtracking.

The film walks the card's own argument: hook -> the one-sentence version -> the maze
(choose / explore / unchoose) -> plain recursion with one corridor -> base case + the leap
of faith -> the call stack and its unwinding -> why naive fib is 2^n -> the backtracking
template -> the paren tree and its pruning -> prune before you descend -> the four flavours
-> the two things that go wrong -> complexity -> recognition -> the recall card.

One hero object carries the film: a decision tree that is first a maze, then a single
corridor, then Fibonacci, then the parentheses search. Narration lives in BEATS and every
animation is sized against `tracker.duration`, so picture and voice cannot drift.
"""

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Circle,
    Circumscribe,
    DashedLine,
    FadeIn,
    FadeOut,
    Indicate,
    Line,
    MathTex,
    ReplacementTransform,
    Restore,
    ShowPassingFlash,
    Text,
    VGroup,
    Write,
)

from house import (
    ACCENT,
    BODY_FS,
    GONE,
    GOOD,
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
from shots import ArrayRow, TreeViz, chip

PATTERN_SLUG = "recursion-backtracking"
TITLE = "Recursion and Backtracking"
SUMMARY = "A function that trusts a smaller call of itself, and a search that undoes every choice."
SCENE_CLASS = "RecursionBacktracking"
POSTER_AT = 28.0

BEATS = [
    # 0 hook
    "Backtracking is a maze, walked with one piece of chalk.",
    # 1 the one-sentence version
    "Recursion is a function that trusts a smaller call of itself, and then adds one step.",
    # 2 backtracking defined
    "Backtracking adds a choice: make it, recurse, then undo it.",
    # 3 the maze
    "Picture a hedge maze. At every fork you pick a corridor and draw a chalk line into it.",
    # 4 dead end
    "Dead end? Walk back to the fork, rub the line out, try the next corridor.",
    # 5 the trail is the answer
    "The trail behind you is the path, and that one piece of chalk explores the whole maze.",
    # 6 plain recursion
    "Plain recursion is that maze with only one corridor per fork, so nothing ever needs undoing.",
    # 7 base case + smaller call
    "Before writing anything, answer two questions: what is the smallest input, and how "
    "does a smaller answer combine?",
    # 8 the leap of faith
    "Don't trace the smaller call in your head. Trust it, and check only your one step.",
    # 9 the stack
    "Every waiting call becomes a stack frame, so a recursion n deep costs n space.",
    # 10 fibonacci
    "Fibonacci makes two smaller calls per node, and that is exactly why the naive version "
    "is two to the n.",
    # 11 three verbs
    "Backtracking's template is three verbs: choose, explore, unchoose.",
    # 12 append / recurse / pop
    "Append the choice, recurse, then pop it. The append and pop bracket the call.",
    # 13 generate parentheses
    "Generate parentheses, with n equal to two. Every level appends one character to the path.",
    # 14 the pruning condition
    "A close bracket is legal only while an open bracket is still waiting.",
    # 15 the payoff
    "The branches that do not exist are the pruning: Catalan time instead of four to the n.",
    # 16 prune early
    "Prune before you descend. Checking validity at the leaf still visits every dead branch.",
    # 17 the four flavours
    "Four flavours: build by position, permutations, combinations, and partitioning a string.",
    # 18 used vs start
    "Order matters, so track what is used. Order does not, so pass a start index.",
    # 19 copy trap
    "Store a copy of the path. Append the live list, and every result ends up empty.",
    # 20 undo trap
    "If you changed two things before the call, restore both of them after it.",
    # 21 complexity
    "The cost is the number of leaves, times the cost of copying one path. Space is the depth.",
    # 22 recognise / counter-tell
    "Reach for it on all ways, or on every valid way. A count, or an optimum, means dynamic "
    "programming.",
    # 23 recall
    "Choose. Explore. Unchoose. Make the call, then undo it.",
]

CHAPTERS = {
    0: "The hook",
    1: "The one-sentence version",
    3: "The maze",
    6: "Plain recursion",
    7: "Base case and leap of faith",
    9: "The call stack",
    10: "Why Fibonacci explodes",
    11: "The template",
    13: "Pruning the tree",
    16: "Prune before you descend",
    17: "The four flavours",
    19: "What goes wrong",
    21: "Complexity",
    22: "How to recognise it",
    23: "Recall",
}

MAZE = ["s", "L", "M", "LL", "LR", "ML", "MR"]
FIB = ["f4", "f3", "f2", "f2", "f1", "f1", "f0"]
PARENS = ['""', "(", ")", "((", "()", ")(", "))"]

RADIUS = 0.30
V_GAP = 0.95
Y_SHIFT = 0.62


def node_index(level: int, i: int) -> int:
    """Index of node i on a perfect tree's level (levels are laid out in order)."""
    return 2 ** level - 1 + i


def edge_index(level: int, i: int, off: int) -> int:
    """Index of the edge from node i on `level` to its child (off = 0 left, 1 right)."""
    return 2 ** level - 1 + 2 * i + off


def fit_into(t: Text, box, pad: float = 0.06) -> Text:
    if t.width > box.width - pad:
        t.scale_to_fit_width(box.width - pad)
    if t.height > box.height - pad:
        t.scale_to_fit_height(box.height - pad)
    return t


def labelled_tree(labels, *, levels=3, radius=RADIUS, v_gap=V_GAP, y_shift=Y_SHIFT,
                  fs=15):
    """TreeViz's bare circles plus a value drawn inside every node."""
    viz = TreeViz(levels, radius=radius, v_gap=v_gap)
    viz.group.shift(UP * y_shift)
    texts = VGroup()
    for c, lab in zip(viz.nodes, labels):
        t = Text(lab, font=MONO, font_size=fs, color=INK)
        fit_into(t, c, pad=0.05)
        t.move_to(c.get_center())
        texts.add(t)
    return viz, texts


def relabel(texts, labels, *, fs=15):
    """Swap the values inside an existing tree, node for node."""
    new = VGroup()
    anims = []
    for old, lab in zip(texts, labels):
        t = Text(lab, font=MONO, font_size=fs, color=old.color)
        fit_into(t, Circle(radius=RADIUS), pad=0.05)
        t.move_to(old.get_center())
        new.add(t)
        anims.append(ReplacementTransform(old, t))
    return new, anims


class Trail:
    """The `path` list as a row of slots: choose fills one, unchoose empties it."""

    def __init__(self, slots=4, *, cell=0.58, buff=0.1, fs=18, y=-2.42, x=0.5):
        self.boxes = []
        self.items = []
        cells = VGroup()
        for _ in range(slots):
            b = card(cell, cell, color=STROKE, fill=PANEL)
            self.boxes.append(b)
            self.items.append(None)
            cells.add(b)
        cells.arrange(RIGHT, buff=buff).move_to([x, y, 0])
        self.cells = cells
        self.live = VGroup()  # the values currently sitting in the slots
        self.fs = fs

    def put(self, i: int, text: str, color=ACCENT):
        t = Text(text, font=MONO, font_size=self.fs, color=color)
        fit_into(t, self.boxes[i], pad=0.05)
        t.move_to(self.boxes[i].get_center())
        self.items[i] = t
        self.live.add(t)
        return [
            FadeIn(t, scale=0.7),
            self.boxes[i].animate.set_stroke(color, width=2.6).set_fill(color, opacity=0.22),
        ]

    def drop(self, i: int):
        t = self.items[i]
        self.items[i] = None
        if t is None:
            return []
        self.live.remove(t)
        return [
            FadeOut(t, scale=0.7),
            self.boxes[i].animate.set_stroke(STROKE, width=1.6).set_fill(PANEL, opacity=1.0),
        ]

    def mobs(self):
        """Everything the trail owns, for a clean fade-out."""
        return VGroup(self.cells, self.live)

    def tint(self, i: int, color=GOOD):
        return [
            self.boxes[i].animate.set_stroke(color, width=2.6).set_fill(color, opacity=0.22)
        ]


class StackColumn:
    """Recursion frames as a column that grows upward; push and pop are real motion."""

    def __init__(self, *, w=3.0, h=0.52, buff=0.14, x=-3.0, base_y=-1.95, fs=18):
        self.w, self.h, self.buff, self.x, self.base_y, self.fs = w, h, buff, x, base_y, fs
        self.frames = []

    def y_of(self, n: int) -> float:
        return self.base_y + n * (self.h + self.buff)

    def frame(self, n: int, text: str, color=PRIMARY):
        box = card(self.w, self.h, color=color, fill=PANEL)
        t = Text(text, font=MONO, font_size=self.fs, color=INK)
        fit_into(t, box, pad=0.18)
        t.move_to(box.get_center())
        v = VGroup(box, t).move_to([self.x, self.y_of(n), 0])
        self.frames.append(v)
        return v


class RecursionBacktracking(PrebakedVoiceMovingCameraScene):
    # ---------------------------------------------------------------------------- setup
    def construct(self):
        bg(self)
        for i in range(len(BEATS)):
            getattr(self, f"_beat{i}")()

    # ------------------------------------------------------------------------- utilities
    def _tree(self, labels, **kw):
        viz, texts = labelled_tree(labels, **kw)
        return VGroup(viz.group, texts), viz, texts

    def _mark(self, viz, idxs, color=ACCENT, width=3.0):
        return [viz.nodes[k].animate.set_stroke(color=color, width=width) for k in idxs]

    def _mark_edge(self, viz, idxs, color=ACCENT, width=3.0):
        return [viz.edges[k].animate.set_color(color).set_stroke(width=width) for k in idxs]

    def _chips_row(self, items, *, buff=0.55, y=0.0):
        return VGroup(*items).arrange(RIGHT, buff=buff).move_to([0, y, 0])

    def _code(self, lines, *, fs=17):
        return VGroup(*[Text(t, font=MONO, font_size=fs, color=c) for t, c in lines]).arrange(
            DOWN, aligned_edge=LEFT, buff=0.16
        )

    def _note_at(self, code, line_i, text, color, *, x_off=0.45, fs=SMALL_FS):
        """A note pinned clear of the code block's whole bounding box."""
        t = Text(text, font=MONO, font_size=fs, color=color)
        t.move_to([code.get_right()[0] + x_off + t.width / 2,
                   code[line_i].get_center()[1], 0])
        return t

    # ---------------------------------------------------------------------------- beats
    def _beat0(self):
        """Hook: the trade, as two objects. Nothing else on stage."""
        with self.voiceover(text=BEATS[0]) as tr:
            swap_rails(self, headline("One piece of chalk, one trail."),
                       caption("recursion + backtracking"))
            self.play(FadeIn(rule()), run_time=0.3)
            bad = chip("every branch, copied", color=GONE, fs=BODY_FS)
            good = chip("one path, reused", color=GOOD, fs=BODY_FS)
            row = VGroup(bad, good).arrange(DOWN, buff=0.6).move_to(stage_center(0.15))
            self.play(FadeIn(bad, shift=UP * 0.2), run_time=0.5)
            self.wait(0.25)
            self.play(FadeIn(good, shift=UP * 0.2), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._hook = row

    def _beat1(self):
        """The one-sentence version: f(n) hands off to f(n-1) and adds one step."""
        with self.voiceover(text=BEATS[1]) as tr:
            swap_rails(self, headline("Recursion trusts a smaller call."),
                       caption("then adds one step of work"))
            self.play(FadeOut(self._hook, run_time=0.3))
            big = chip("f(n)", color=PRIMARY, fs=30)
            small = chip("f(n-1)", color=PRIMARY, fs=30)
            pair = VGroup(big, small).arrange(RIGHT, buff=1.5).move_to([0, 0.75, 0])
            arrow = Text("→", font=MONO, font_size=40, color=MUTED)
            arrow.move_to((big.get_right() + small.get_left()) / 2)
            trust = Text("trust it", font=MONO, font_size=SMALL_FS, color=ACCENT)
            trust.next_to(small, DOWN, buff=0.22)
            step = chip("+ one step of work", color=ACCENT, fs=BODY_FS)
            step.next_to(big, DOWN, buff=0.9)
            self.play(FadeIn(big, shift=UP * 0.2), run_time=0.45)
            self.play(FadeIn(arrow), run_time=0.3)
            self.play(FadeIn(small, shift=UP * 0.2), run_time=0.45)
            self.play(FadeIn(trust), FadeIn(step), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._onesentence = VGroup(pair, arrow, trust, step)

    def _beat2(self):
        """Backtracking defined: three beats of a loop."""
        with self.voiceover(text=BEATS[2]) as tr:
            swap_rails(self, headline("Choose, recurse, undo."),
                       caption("the backtracking rhythm"))
            self.play(FadeOut(self._onesentence, run_time=0.3))
            verbs = [
                chip("choose", color=ACCENT, fs=BODY_FS),
                chip("explore", color=WINDOW, fs=BODY_FS),
                chip("unchoose", color=MUTED, fs=BODY_FS),
            ]
            row = VGroup(*verbs).arrange(RIGHT, buff=0.85).move_to(stage_center(0.15))
            arrows = VGroup(
                Text("→", font=MONO, font_size=34, color=MUTED).move_to(
                    (verbs[0].get_right() + verbs[1].get_left()) / 2),
                Text("→", font=MONO, font_size=34, color=MUTED).move_to(
                    (verbs[1].get_right() + verbs[2].get_left()) / 2),
            )
            self.play(
                FadeIn(verbs[0], shift=UP * 0.2),
                run_time=0.4,
            )
            self.play(FadeIn(arrows[0]), run_time=0.25)
            self.play(FadeIn(verbs[1], shift=UP * 0.2), run_time=0.4)
            self.play(FadeIn(arrows[1]), run_time=0.25)
            self.play(FadeIn(verbs[2], shift=UP * 0.2), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._verbs = VGroup(row, arrows)

    def _beat3(self):
        """The maze: the hero tree arrives, with the first chalk line drawn into it."""
        with self.voiceover(text=BEATS[3]) as tr:
            swap_rails(self, headline("Draw a line into one corridor."),
                       caption("the trail is the path"))
            self.play(FadeOut(self._verbs, run_time=0.3))
            self.tree, self.viz, self.tree_labels = self._tree(MAZE)
            self.trail = Trail(slots=4, x=0.5)
            plabel = Text("path", font=MONO, font_size=SMALL_FS, color=MUTED)
            plabel.next_to(self.trail.cells, LEFT, buff=0.3)
            self.play(FadeIn(self.tree), FadeIn(self.trail.cells), FadeIn(plabel),
                      run_time=min(1.4, max(0.7, tr.duration * 0.3)))
            self.play(*self._mark(self.viz, [0]),
                      run_time=min(0.7, max(0.4, tr.duration * 0.15)))
            self.play(*self._mark(self.viz, [1]), *self._mark_edge(self.viz, [0]),
                      *self.trail.put(0, "s"), *self.trail.put(1, "L"),
                      run_time=min(1.2, max(0.6, tr.duration * 0.25)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._path_label = plabel

    def _beat4(self):
        """Dead end, then the rub-out: the corridor is unwound, the trail stays."""
        with self.voiceover(text=BEATS[4]) as tr:
            swap_rails(self, headline("Dead end: rub the line out."),
                       caption("walk back, try the next"))
            self.play(*self._mark(self.viz, [3]), *self._mark_edge(self.viz, [1]),
                      *self.trail.put(2, "LL", color=GONE),
                      run_time=min(0.9, max(0.5, tr.duration * 0.2)))
            dead = chip("dead end", color=GONE, fs=SMALL_FS)
            dead.next_to(self.viz.nodes[3], DOWN, buff=0.18)
            self.play(FadeIn(dead, shift=UP * 0.15), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.6)))
            # rub it out — the chalk line goes, the trail up to the fork stays
            self.play(*self.trail.drop(2), *self._mark(self.viz, [3], color=PRIMARY, width=2.0),
                      *self._mark_edge(self.viz, [1], color=STROKE, width=2.0),
                      FadeOut(dead), run_time=min(1.0, max(0.5, tr.duration * 0.2)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._dead = dead

    def _beat5(self):
        """The exit: the trail is the answer, and it is copied out."""
        with self.voiceover(text=BEATS[5]) as tr:
            swap_rails(self, headline("The next corridor is the exit."),
                       caption("the trail is the answer"))
            self.play(*self._mark(self.viz, [4], color=GOOD), *self._mark_edge(self.viz, [2], color=GOOD),
                      *self.trail.put(2, "LR", color=GOOD),
                      run_time=min(1.0, max(0.5, tr.duration * 0.25)))
            self.play(Circumscribe(self.viz.nodes[4], color=GOOD), run_time=0.6)
            copied = chip("copy the trail → results", color=GOOD, fs=SMALL_FS)
            copied.move_to([0, -1.95, 0])
            self.play(FadeIn(copied, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._copied = copied

    def _beat6(self):
        """Plain recursion: every fork has one corridor, so there is nothing to undo."""
        with self.voiceover(text=BEATS[6]) as tr:
            swap_rails(self, headline("Plain recursion has no forks."),
                       caption("one corridor, nothing to undo"))
            self.play(FadeOut(self._copied, run_time=0.25))
            others = [2, 3, 5, 6]
            self.play(*[self.viz.nodes[k].animate.set_stroke(color=STROKE, width=1.6)
                        for k in others],
                      *[self.viz.edges[k].animate.set_color(STROKE).set_stroke(width=1.2)
                        for k in (3, 4, 5)],
                      *[self.tree_labels[k].animate.set_color(MUTED) for k in others],
                      *self._mark(self.viz, [0, 1, 4], color=PRIMARY, width=2.4),
                      *self._mark_edge(self.viz, [0, 2], color=PRIMARY, width=2.4),
                      run_time=min(1.4, max(0.7, tr.duration * 0.35)))
            self.play(Indicate(self.viz.nodes[4], color=GOOD, scale_factor=1.15),
                      run_time=0.6)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self.play(FadeOut(VGroup(self.tree, self.trail.mobs(), self._path_label)),
                      run_time=0.4)

    def _beat7(self):
        """Base case and smaller call, named on the code the viewer will write."""
        with self.voiceover(text=BEATS[7]) as tr:
            swap_rails(self, headline("Answer two questions first."),
                       caption("base case, then smaller call"))
            code = self._code([
                ("def f(n):", INK),
                ("    if n < 10: return n", INK),
                ("    return n % 10 + f(n // 10)", INK),
            ])
            code.move_to([-1.6, 0.35, 0])
            base = self._note_at(code, 1, "← base case: answer it by looking", GOOD)
            small = self._note_at(code, 2, "← smaller call: trust it", ACCENT)
            self.play(Write(code), run_time=min(1.3, max(0.6, tr.duration * 0.3)))
            self.play(FadeIn(base, shift=LEFT * 0.15), run_time=0.45)
            self.play(FadeIn(small, shift=LEFT * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._code7 = code
            self._base = base
            self._small = small

    def _beat8(self):
        """The leap of faith, made explicit: stop tracing, check your own step."""
        with self.voiceover(text=BEATS[8]) as tr:
            swap_rails(self, headline("Trust the smaller call."),
                       caption("check only your one step"))
            self.play(Indicate(self._small, color=ACCENT, scale_factor=1.05), run_time=0.7)
            faith = chip("assume it is already correct", color=ACCENT, fs=BODY_FS)
            faith.move_to([0, -1.5, 0])
            self.play(FadeIn(faith, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self.play(FadeOut(VGroup(self._code7, self._base, self._small, faith)),
                      run_time=0.4)

    def _beat9(self):
        """The stack: frames push down the recursion, then unwind with real values."""
        with self.voiceover(text=BEATS[9]) as tr:
            swap_rails(self, headline("Every call is a stack frame."),
                       caption("depth n costs n space"))
            st = StackColumn()
            self.play(FadeIn(st.frame(0, "sum(345)", color=ACCENT)),
                      run_time=min(0.5, max(0.3, tr.duration * 0.1)))
            self.play(FadeIn(st.frame(1, "sum(34)"), shift=UP * 0.2),
                      run_time=min(0.5, max(0.3, tr.duration * 0.1)))
            self.play(FadeIn(st.frame(2, "sum(3)"), shift=UP * 0.2),
                      run_time=min(0.5, max(0.3, tr.duration * 0.1)))
            base = Text("base case: return 3", font=MONO, font_size=SMALL_FS, color=GOOD)
            base.move_to([3.1, 0.65, 0])
            trace = VGroup(
                Text("= 5 + sum(34)", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("= 5 + (4 + sum(3))", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("= 5 + (4 + 3)", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("= 12", font=MONO, font_size=SMALL_FS, color=GOOD),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.26).move_to([3.1, -0.5, 0])
            self.camera.frame.save_state()  # bare: stores only
            self.play(
                self.camera.auto_zoom([st.frames[2], st.frames[0]], margin=1.1),
                run_time=min(0.8, max(0.45, tr.duration * 0.16)),
            )
            self.play(FadeOut(st.frames[2], shift=UP * 0.25), run_time=0.3)
            self.play(Restore(self.camera.frame), run_time=0.45)
            self.play(FadeIn(base, shift=UP * 0.15), FadeIn(trace[0], shift=UP * 0.1),
                      run_time=0.35)
            self.play(FadeOut(st.frames[1], shift=UP * 0.25), FadeIn(trace[1]), run_time=0.35)
            self.play(FadeOut(st.frames[0], shift=UP * 0.25), run_time=0.25)
            self.play(FadeIn(trace[2]), FadeIn(trace[3]), run_time=0.4)
            cost = chip("O(depth) space", color=GOOD, fs=SMALL_FS)
            cost.move_to([3.1, -2.05, 0])
            self.play(FadeIn(cost, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._stack9 = VGroup(base, trace, cost)
            self._st = st

    def _beat10(self):
        """Fibonacci: two calls per node, so the level count doubles."""
        with self.voiceover(text=BEATS[10]) as tr:
            swap_rails(self, headline("Two calls per node is 2^n."),
                       caption("why naive Fibonacci explodes"))
            self.play(FadeOut(self._stack9, run_time=0.3))
            fib, viz, labels = self._tree(FIB, fs=15)
            counts = VGroup(
                Text("1 call", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("2 calls", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("4 calls", font=MONO, font_size=SMALL_FS, color=MUTED),
            )
            for t, k in zip(counts, (0, 1, 3)):
                t.next_to(viz.nodes[k], LEFT, buff=0.55)
            self.play(FadeIn(fib), run_time=min(0.9, max(0.5, tr.duration * 0.2)))
            for i, t in enumerate(counts):
                self.play(FadeIn(t, shift=RIGHT * 0.15),
                          run_time=min(0.5, max(0.28, tr.duration * 0.1)))
                if i == 0:
                    self.play(Indicate(viz.nodes[0], color=ACCENT, scale_factor=1.12),
                              run_time=0.4)
                elif i == 1:
                    self.play(*self._mark(viz, [1, 2], color=ACCENT),
                              run_time=0.4)
                else:
                    self.play(*self._mark(viz, [3, 4, 5, 6], color=ACCENT),
                              run_time=0.4)
            blow = chip("doubles every level → 2^n", color=GONE, fs=BODY_FS)
            blow.move_to([3.2, -2.15, 0])
            self.play(FadeIn(blow, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self.play(FadeOut(VGroup(fib, counts, blow)), run_time=0.4)
            del viz, labels

    def _beat11(self):
        """The template: the three verbs, now as a loop over a real path."""
        with self.voiceover(text=BEATS[11]) as tr:
            swap_rails(self, headline("Choose, explore, unchoose."),
                       caption("the template, in three verbs"))
            verbs = VGroup(
                chip("choose", color=ACCENT, fs=BODY_FS),
                chip("explore", color=WINDOW, fs=BODY_FS),
                chip("unchoose", color=MUTED, fs=BODY_FS),
            ).arrange(RIGHT, buff=0.7).move_to([0, 1.15, 0])
            trail = Trail(slots=3, x=0.35, y=-0.35)
            plabel = Text("path", font=MONO, font_size=SMALL_FS, color=MUTED)
            plabel.next_to(trail.cells, LEFT, buff=0.3)
            self.play(FadeIn(verbs), FadeIn(trail.cells), FadeIn(plabel),
                      run_time=min(1.1, max(0.6, tr.duration * 0.25)))
            self.play(Indicate(verbs[0], color=ACCENT, scale_factor=1.06),
                      *trail.put(0, "A"), run_time=0.6)
            self.play(Indicate(verbs[1], color=WINDOW, scale_factor=1.06), run_time=0.5)
            self.play(Indicate(verbs[2], color=MUTED, scale_factor=1.06),
                      *trail.drop(0), run_time=0.6)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._verbs2 = verbs
            self.trail11 = trail
            self._plabel11 = plabel

    def _beat12(self):
        """Append / recurse / pop, with the brackets drawn around the call."""
        with self.voiceover(text=BEATS[12]) as tr:
            swap_rails(self, headline("Append, recurse, pop."),
                       caption("the pair brackets the call"))
            self.play(FadeOut(self._verbs2, run_time=0.25))
            code = self._code([
                ("path.append(choice)    # choose", GOOD),
                ("backtrack(state)       # explore", WINDOW),
                ("path.pop()             # unchoose", MUTED),
            ])
            code.move_to([0, 1.05, 0])
            left = Text("(", font=MONO, font_size=40, color=ACCENT)
            right = Text(")", font=MONO, font_size=40, color=ACCENT)
            left.next_to(code[1], LEFT, buff=0.22)
            right.next_to(code[1], RIGHT, buff=0.22)
            self.play(Write(code), run_time=min(1.1, max(0.6, tr.duration * 0.25)))
            self.play(FadeIn(left, shift=RIGHT * 0.2), FadeIn(right, shift=LEFT * 0.2),
                      *self.trail11.put(0, "A"),
                      run_time=0.6)
            self.play(Indicate(code[1], color=WINDOW, scale_factor=1.03), run_time=0.6)
            self.play(*self.trail11.drop(0), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._code12 = VGroup(code, left, right)

    def _beat13(self):
        """Generate parentheses: the same tree, relabelled with partial strings."""
        with self.voiceover(text=BEATS[13]) as tr:
            swap_rails(self, headline("Each level adds one character."),
                       caption("generate parentheses, n = 2"))
            self.play(FadeOut(self._code12, run_time=0.3))
            tree, viz, labels = self._tree(PARENS, fs=15)
            self.ptree, self.pviz, self.plabels = tree, viz, labels
            self.play(FadeIn(tree), run_time=min(1.0, max(0.5, tr.duration * 0.22)))
            self.play(*self._mark(viz, [0], color=ACCENT),
                      run_time=min(0.6, max(0.35, tr.duration * 0.12)))
            self.play(*self._mark(viz, [1], color=ACCENT), *self._mark_edge(viz, [0], color=ACCENT),
                      *self.trail11.put(0, "("),
                      run_time=min(1.0, max(0.5, tr.duration * 0.22)))
            self.play(*self._mark(viz, [3], color=ACCENT), *self._mark_edge(viz, [1], color=ACCENT),
                      *self.trail11.put(1, "(("),
                      run_time=min(1.0, max(0.5, tr.duration * 0.22)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat14(self):
        """The prune conditions, marked where the corridor would start."""
        with self.voiceover(text=BEATS[14]) as tr:
            swap_rails(self, headline("A close bracket needs an open one."),
                       caption("prune where the branch starts"))
            self.play(*self._mark(self.pviz, [2], color=GONE),
                      *self._mark_edge(self.pviz, [2], color=GONE, width=2.4),
                      run_time=min(0.9, max(0.5, tr.duration * 0.2)))
            near = chip("close > open", color=GONE, fs=SMALL_FS)
            near.next_to(self.pviz.nodes[2], RIGHT, buff=0.4)
            self.play(FadeIn(near, shift=LEFT * 0.15), run_time=0.4)
            ghost = Circle(radius=0.24, stroke_color=GONE, stroke_width=2, fill_color=PANEL,
                           fill_opacity=1.0).move_to(self.pviz.nodes[3].get_center() + DOWN * V_GAP)
            cross = Text("✗", font=MONO, font_size=SMALL_FS, color=GONE).move_to(ghost.get_center())
            edge = DashedLine(self.pviz.nodes[3].get_center(), ghost.get_center(),
                              color=GONE, stroke_width=1.6)
            far = chip("open > n", color=GONE, fs=SMALL_FS)
            far.next_to(ghost, RIGHT, buff=0.3)
            self.play(FadeIn(VGroup(edge, ghost, cross)),
                      run_time=min(0.8, max(0.45, tr.duration * 0.18)))
            self.play(FadeIn(far, shift=LEFT * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._prune14 = VGroup(near, far, edge, ghost, cross)

    def _beat15(self):
        """The payoff: two answers survive, and the count is Catalan, not 4^n."""
        with self.voiceover(text=BEATS[15]) as tr:
            swap_rails(self, headline("Pruning makes it Catalan."),
                       caption("not four to the n"))
            self.play(FadeOut(self._prune14), run_time=0.3)
            self.play(*self._mark(self.pviz, [5, 6], color=GONE),
                      *self._mark_edge(self.pviz, [3, 4, 5], color=GONE, width=2.0),
                      *[self.plabels[k].animate.set_color(MUTED) for k in (2, 5, 6)],
                      run_time=min(1.1, max(0.6, tr.duration * 0.25)))
            answers = VGroup(
                chip("(())", color=GOOD, fs=SMALL_FS),
                chip("()()", color=GOOD, fs=SMALL_FS),
            )
            answers[0].move_to(self.pviz.nodes[3].get_center() + DOWN * 0.95)
            answers[1].move_to(self.pviz.nodes[4].get_center() + DOWN * 0.95)
            self.play(FadeIn(answers, shift=UP * 0.15), run_time=0.5)
            payoff = chip("4^n branches  →  Catalan", color=GOOD, fs=SMALL_FS)
            payoff.move_to([3.4, -2.2, 0])
            self.play(FadeIn(payoff, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._answers = VGroup(answers, payoff)
            self.play(FadeOut(VGroup(self.ptree, self.trail11.mobs(), self._plabel11,
                                     self._answers)),
                      run_time=0.4)

    def _beat16(self):
        """Prune before you descend: the leaf check pays for every dead branch."""
        with self.voiceover(text=BEATS[16]) as tr:
            swap_rails(self, headline("Prune before you descend."),
                       caption("leaf checks walk every dead branch"))
            def chain(x, y_top, n, color, r=0.2, gap=0.62):
                nodes = VGroup()
                for i in range(n):
                    c = Circle(radius=r, stroke_color=color, stroke_width=2,
                               fill_color=PANEL, fill_opacity=1.0)
                    c.move_to([x, y_top - i * gap, 0])
                    nodes.add(c)
                edges = VGroup()
                for i in range(n - 1):
                    edges.add(Line(nodes[i].get_center(), nodes[i + 1].get_center(),
                                   color=STROKE, stroke_width=1.6))
                return VGroup(edges, nodes)

            bad = chain(-5.2, 0.95, 4, GONE)
            badx = Text("✗", font=MONO, font_size=BODY_FS, color=GONE)
            badx.next_to(bad, DOWN, buff=0.18)
            badlab = Text("check at the leaf: 4 frames", font=MONO, font_size=SMALL_FS, color=GONE)
            badlab.move_to([-2.35, 0.1, 0])
            self.play(FadeIn(bad), run_time=min(0.9, max(0.5, tr.duration * 0.2)))
            self.play(ShowPassingFlash(
                Line(bad.get_top(), bad.get_bottom(), color=GONE, stroke_width=4),
                time_width=0.7), run_time=min(0.9, max(0.5, tr.duration * 0.2)))
            self.play(FadeIn(badx), FadeIn(badlab), run_time=0.4)
            good = Circle(radius=0.24, stroke_color=GOOD, stroke_width=2.4, fill_color=PANEL,
                          fill_opacity=1.0).move_to([1.7, 0.95, 0])
            gx = Text("✗", font=MONO, font_size=SMALL_FS, color=GOOD).move_to(good.get_center())
            glab = Text("check first: no frames wasted", font=MONO, font_size=SMALL_FS, color=GOOD)
            glab.move_to([4.1, 0.1, 0])
            self.play(FadeIn(good), FadeIn(gx), run_time=0.45)
            self.play(FadeIn(glab, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._prune16 = VGroup(bad, badx, badlab, good, gx, glab)

    def _beat17(self):
        """The four flavours of the one template."""
        with self.voiceover(text=BEATS[17]) as tr:
            swap_rails(self, headline("Four flavours, one template."),
                       caption("position, permutation, combo, cut"))
            self.play(FadeOut(self._prune16, run_time=0.3))
            rows = VGroup(
                Text("build by position  →  keypad[i]", font=MONO, font_size=BODY_FS, color=INK),
                Text("permutations  →  a used set", font=MONO, font_size=BODY_FS, color=INK),
                Text("combinations  →  a start index", font=MONO, font_size=BODY_FS, color=INK),
                Text("partitioning  →  a cut point", font=MONO, font_size=BODY_FS, color=INK),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.34)
            box = card(rows.width + 1.1, rows.height + 0.9, color=WINDOW, fill=PANEL)
            box.move_to(stage_center(0.0))
            rows.move_to(box.get_center())
            self.play(FadeIn(box), run_time=0.35)
            self.play(*[FadeIn(t, shift=RIGHT * 0.2) for t in rows], lag_ratio=0.3,
                      run_time=min(1.5, max(0.8, tr.duration * 0.35)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._flavours = VGroup(box, rows)

    def _beat18(self):
        """Used set vs start index — the one choice that decides the shape."""
        with self.voiceover(text=BEATS[18]) as tr:
            swap_rails(self, headline("Used set, or a start index."),
                       caption("order matters, or it doesn't"))
            self.play(FadeOut(self._flavours, run_time=0.3))
            left = ArrayRow([1, 2, 3], cell=0.62, fs=22, show_index=False)
            right = ArrayRow([1, 2, 3], cell=0.62, fs=22, show_index=False)
            left.group.move_to([-3.5, 0.5, 0])
            right.group.move_to([3.3, 0.5, 0])
            ltag = Text("order matters → used", font=MONO, font_size=SMALL_FS, color=ACCENT)
            ltag.next_to(left.group, UP, buff=0.35)
            rtag = Text("order doesn't → start", font=MONO, font_size=SMALL_FS, color=WINDOW)
            rtag.next_to(right.group, UP, buff=0.35)
            used = Text("used", font=MONO, font_size=SMALL_FS, color=ACCENT)
            used.next_to(left.cell(1), DOWN, buff=0.2)
            start = Text("start", font=MONO, font_size=SMALL_FS, color=WINDOW)
            start.next_to(right.cell(1), DOWN, buff=0.2)
            self.play(FadeIn(left.group), FadeIn(right.group), FadeIn(ltag), FadeIn(rtag),
                      run_time=min(1.1, max(0.6, tr.duration * 0.25)))
            self.play(FadeIn(used, shift=UP * 0.15), *left.focus(1, color=ACCENT),
                      run_time=0.5)
            self.play(FadeIn(start, shift=UP * 0.15), *right.mark_gone(0),
                      run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._usedstart = VGroup(left.group, right.group, ltag, rtag, used, start)

    def _beat19(self):
        """Trap one: the live path list aliases every result."""
        with self.voiceover(text=BEATS[19]) as tr:
            swap_rails(self, headline("Store a copy of the path."),
                       caption("path[:], never path"))
            self.play(FadeOut(self._usedstart, run_time=0.3))
            live = VGroup(
                Text("path = ['(', '(', ')']", font=MONO, font_size=BODY_FS, color=ACCENT),
            ).move_to([0, 1.35, 0])
            bad = Text("results = [[], [], [], []]", font=MONO, font_size=BODY_FS, color=GONE)
            bad.move_to([0, 0.15, 0])
            good = Text("results.append(path[:])", font=MONO, font_size=BODY_FS, color=GOOD)
            good.move_to([0, -1.0, 0])
            note = chip("append(path) aliases", color=GONE, fs=SMALL_FS)
            note.next_to(bad, RIGHT, buff=0.45)
            self.play(FadeIn(live, shift=UP * 0.15), run_time=0.45)
            self.play(FadeIn(bad, shift=UP * 0.15), run_time=0.45)
            self.play(Indicate(bad, color=GONE, scale_factor=1.05), run_time=0.6)
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.play(FadeIn(good, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._copy19 = VGroup(live, bad, good, note)

    def _beat20(self):
        """Trap two: undoing half the state poisons the sibling branches."""
        with self.voiceover(text=BEATS[20]) as tr:
            swap_rails(self, headline("Changed two things? Undo two."),
                       caption("or siblings see a polluted world"))
            self.play(FadeOut(self._copy19, run_time=0.3))
            code = self._code([
                ("used.add(x); path.append(x)", INK),
                ("permute(path, used)", WINDOW),
                ("path.pop(); used.discard(x)", GOOD),
            ])
            code.move_to([0, 0.75, 0])
            tags = VGroup(
                self._note_at(code, 0, "two things change", ACCENT),
                self._note_at(code, 1, "recurse", WINDOW),
                self._note_at(code, 2, "two things restored", GOOD),
            )
            self.play(Write(code), run_time=min(1.1, max(0.6, tr.duration * 0.25)))
            self.play(*[FadeIn(t, shift=LEFT * 0.15) for t in tags], lag_ratio=0.3,
                      run_time=min(1.1, max(0.6, tr.duration * 0.25)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._undo20 = VGroup(code, tags)

    def _beat21(self):
        """Complexity, stated cold."""
        with self.voiceover(text=BEATS[21]) as tr:
            swap_rails(self, headline("Leaves times copy cost."),
                       caption("space is depth, excluding output"))
            self.play(FadeOut(self._undo20, run_time=0.3))

            def mchip(tex, color):
                m = MathTex(tex, color=color).scale(0.85)
                b = card(m.width + 0.7, m.height + 0.45, color=color, fill=PANEL)
                m.move_to(b.get_center())
                return VGroup(b, m)

            row = VGroup(
                mchip(r"O(2^n)", GONE),
                mchip(r"O(n \cdot n!)", GONE),
                mchip(r"O(4^n / \sqrt{n})", MUTED),
            ).arrange(RIGHT, buff=0.7).move_to([0, 0.75, 0])
            caps = VGroup(
                Text("fibonacci", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("permutations", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("parens, unpruned", font=MONO, font_size=SMALL_FS, color=MUTED),
            )
            for c, box in zip(caps, row):
                c.next_to(box, DOWN, buff=0.2)
            space = Text("space = O(depth), excluding the output",
                         font=MONO, font_size=BODY_FS, color=GOOD)
            space.move_to([0, -1.35, 0])
            self.play(*[FadeIn(m, shift=UP * 0.2) for m in row], lag_ratio=0.25,
                      run_time=min(1.3, max(0.7, tr.duration * 0.3)))
            self.play(FadeIn(caps), run_time=0.4)
            self.play(FadeIn(space, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._complex = VGroup(row, caps, space)

    def _beat22(self):
        """Recognition, and the counter-tell that sends you to DP."""
        with self.voiceover(text=BEATS[22]) as tr:
            swap_rails(self, headline("Reach for it on 'all ways'."),
                       caption("a count or an optimum is DP"))
            self.play(FadeOut(self._complex, run_time=0.3))
            yes = VGroup(
                Text("✓  all combinations / permutations", font=MONO, font_size=BODY_FS, color=GOOD),
                Text("✓  every valid way", font=MONO, font_size=BODY_FS, color=GOOD),
                Text("✓  choices per step, small n", font=MONO, font_size=BODY_FS, color=GOOD),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            yes.move_to([0, 1.0, 0])
            no = Text("✗  how many ways, or the best way  →  DP",
                      font=MONO, font_size=BODY_FS, color=GONE)
            no.move_to([0, -1.15, 0])
            self.play(*[FadeIn(t, shift=RIGHT * 0.2) for t in yes], lag_ratio=0.3,
                      run_time=min(1.4, max(0.8, tr.duration * 0.35)))
            self.play(FadeIn(no, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._recognise = VGroup(yes, no)

    def _beat23(self):
        """Recall card: the three verbs, one line to leave with."""
        with self.voiceover(text=BEATS[23]) as tr:
            swap_rails(self, headline("Choose. Explore. Unchoose."),
                       caption("make the call, then undo it"))
            self.play(FadeOut(self._recognise, run_time=0.3))
            box = card(9.2, 1.9, color=ACCENT, fill=PANEL)
            box.move_to(stage_center(-0.1))
            top = Text("Choose · Explore · Unchoose", font=MONO, font_size=30, color=ACCENT)
            mid = Text("prune before you descend", font=MONO, font_size=SMALL_FS, color=MUTED)
            sub = Text("space = O(depth)  ·  excluding the output",
                       font=MONO, font_size=SMALL_FS, color=MUTED)
            VGroup(top, mid, sub).arrange(DOWN, buff=0.2).move_to(box.get_center())
            self.play(FadeIn(box, scale=0.96), run_time=0.45)
            self.play(Write(top), run_time=0.5)
            self.play(FadeIn(mid), FadeIn(sub), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
