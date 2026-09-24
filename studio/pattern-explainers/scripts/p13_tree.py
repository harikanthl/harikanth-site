"""
Pattern 13 — Tree.

The card's argument, in order: hook -> the one design question -> a tree is a family ->
the three lines (ask left, ask right, combine) -> DFS vs BFS -> the three traversal orders
as a moving cursor over one tree -> the BST tell -> iterative inorder -> level order's one
trick -> bottom-up (one return value, one recorded answer) -> the -1 sentinel -> validate a
BST with bounds -> the two things that go wrong -> complexity -> recognition -> recall.

Two heroes carry the film: one seven-node tree whose values are relabelled (plain tree ->
BST) while a cursor walks it, and the seven-line dfs body where only the visit line moves.
Every traversal is driven by a ValueTracker, so the walk is computed state, not a stack of
hand-timed keyframes.
"""

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Circle,
    FadeIn,
    FadeOut,
    Indicate,
    Line,
    MathTex,
    ReplacementTransform,
    Restore,
    RoundedRectangle,
    ShowPassingFlash,
    Text,
    VGroup,
    ValueTracker,
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
from shots import TreeViz, chip

PATTERN_SLUG = "tree"
TITLE = "Tree"
SUMMARY = "Every tree problem is one recursive function: ask left, ask right, combine."
SCENE_CLASS = "TreePattern"
POSTER_AT = 32.0

BEATS = [
    # 0 hook
    "Every tree problem is one recursive function, asking its children the very same question.",
    # 1 the design question
    "The design question is what a node needs from its children, and what it hands back.",
    # 2 a tree is a family
    "A tree is a family: one ancestor on top, and everyone else has exactly one parent.",
    # 3 ask the top person
    "You don't interview everyone yourself. You ask the top person, who asks their own children.",
    # 4 the base case
    "The people with no children are the base case, and they answer immediately.",
    # 5 the three lines
    "Everyone else runs exactly the same three lines: ask left, ask right, and combine.",
    # 6 DFS
    "Two ways to walk it. Depth first dives as deep as it can, using recursion or an "
    "explicit stack.",
    # 7 BFS
    "Breadth first visits the tree one generation at a time, using a queue.",
    # 8 the tell
    "Level, nearest, minimum depth means breadth first. Everything else is depth first.",
    # 9 the three orders
    "One function gives three orders, and only the line that does the work moves.",
    # 10 preorder
    "Visit before the calls: root, left, right. Preorder, the order for copying a tree.",
    # 11 inorder
    "Visit between the two calls: left, root, right. That is inorder.",
    # 12 the BST tell
    "On a binary search tree, an inorder walk comes out sorted. That is the BST tell.",
    # 13 postorder
    "Visit after both calls: left, right, root. Children come first, the order for sizes and deletes.",
    # 14 iterative inorder
    "Interviewers ask for iterative inorder: dive left pushing a stack, pop, visit, then go right.",
    # 15 level order
    "Breadth first's whole trick is reading the queue's length just once, before appending any children.",
    # 16 bottom-up
    "Bottom-up returns one value to the parent, and records a separate answer taken from both children.",
    # 17 diameter
    "Diameter returns the taller arm up, but records the sum of both arms.",
    # 18 the sentinel
    "Balanced carries the height and the verdict in one number: minus one means already broken.",
    # 19 validate a BST
    "To validate a binary search tree, carry low and high bounds. The parent alone is not enough.",
    # 20 the null checks
    "In two-tree recursion, order the null checks: both empty first, then either empty.",
    # 21 complexity
    "One depth-first or breadth-first pass is linear, and the sentinel keeps balanced linear too.",
    # 22 recognise
    "Reach for it on level, mirror, ancestor, or path sum: any node with a left and a right child.",
    # 23 recall
    "Ask left, ask right, combine. Then know exactly what value comes back up.",
]

CHAPTERS = {
    0: "The hook",
    1: "The one design question",
    2: "A tree is a family",
    5: "The three lines",
    6: "DFS or BFS",
    9: "The three orders",
    12: "The BST tell",
    14: "Iterative inorder",
    15: "Level order",
    16: "Bottom-up",
    18: "The sentinel",
    19: "Validate a BST",
    20: "What goes wrong",
    21: "Complexity",
    22: "How to recognise it",
    23: "Recall",
}

PLAIN = ["1", "2", "3", "4", "5", "6", "7"]
BST = ["4", "2", "6", "1", "3", "5", "7"]

# node indices in visit order (index i of the perfect tree, level by level)
PRE_ORDER = [0, 1, 3, 4, 2, 5, 6]
IN_ORDER = [3, 1, 4, 0, 5, 2, 6]
POST_ORDER = [4, 3, 1, 6, 5, 2, 0]
LEVEL_ORDER = [0, 1, 2, 3, 4, 5, 6]

V_GAP = 0.95
RADIUS = 0.30
TREE_SCALE = 0.85
TREE_CENTER = [-1.0, -0.05, 0]
ROW_Y = -2.32
CODE_X = 4.45

DFS_CODE = [
    ("def dfs(node):", INK),
    ("    if not node: return", MUTED),
    ("    visit(node)     # PRE", ACCENT),
    ("    dfs(node.left)", INK),
    ("    visit(node)     # IN", ACCENT),
    ("    dfs(node.right)", INK),
    ("    visit(node)     # POST", ACCENT),
]
VISIT_LINE = {10: 2, 11: 4, 12: 4, 13: 6}


def fit_into(t: Text, box, pad: float = 0.06) -> Text:
    if t.width > box.width - pad:
        t.scale_to_fit_width(box.width - pad)
    if t.height > box.height - pad:
        t.scale_to_fit_height(box.height - pad)
    return t


def make_tree(labels, *, levels=3, fs=16):
    """TreeViz's layout, scaled into the safe box, with a value inside every node."""
    viz = TreeViz(levels, radius=RADIUS, v_gap=V_GAP)
    viz.group.shift(UP * 0.62).scale(TREE_SCALE).move_to(TREE_CENTER)
    texts = VGroup()
    for c, lab in zip(viz.nodes, labels):
        t = Text(lab, font=MONO, font_size=fs, color=INK)
        fit_into(t, c, pad=0.05)
        t.move_to(c.get_center())
        texts.add(t)
    return viz, texts


def relabel(texts, labels, *, fs=16):
    """Swap the values inside the existing tree — one node at a time."""
    new = VGroup()
    anims = []
    for old, lab in zip(texts, labels):
        t = Text(lab, font=MONO, font_size=fs, color=old.color)
        fit_into(t, Circle(radius=RADIUS * TREE_SCALE), pad=0.05)
        t.move_to(old.get_center())
        new.add(t)
        anims.append(ReplacementTransform(old, t))
    return new, anims


class Walker:
    """A ring that walks a visit order and a readout that fills as it goes.

    Both are driven by one ValueTracker, so the traversal is computed state: the ring is
    wherever `t` says the current node is, and slot i of the readout is visible exactly
    when i < t. Nothing here is a hand-tuned keyframe.
    """

    def __init__(self, viz, order, values, *, color=ACCENT, x=-1.0, y=ROW_Y, fs=24,
                 buff=0.52, ring_r=0.33):
        self.viz = viz
        self.order = order
        self.t = ValueTracker(0)
        self.ring = Circle(radius=ring_r, color=color, stroke_width=3.2)
        self.texts = VGroup(
            *[Text(str(v), font=MONO, font_size=fs, color=color) for v in values]
        ).arrange(RIGHT, buff=buff)
        self.texts.move_to([x, y, 0])
        self.texts.set_opacity(0)
        self.cursor_updater = self._ring_update
        self.row_updater = self._row_update
        self.ring.add_updater(self.cursor_updater)
        self.texts.add_updater(self.row_updater)
        self.ring_update()

    # -- state -> pixels ------------------------------------------------------------
    def _index(self) -> int:
        return min(int(self.t.get_value()), len(self.order) - 1)

    def ring_update(self):
        self._ring_update(self.ring)

    def _ring_update(self, m):
        i = self._index()
        m.move_to(self.viz.nodes[self.order[i]].get_center())
        m.set_stroke(opacity=0.0 if self.t.get_value() >= len(self.order) else 1.0)

    def _row_update(self, m):
        k = self.t.get_value()
        for i, t in enumerate(m):
            t.set_opacity(1.0 if i < k else 0.0)
        for j, node_i in enumerate(self.order):
            done = j < k
            self.viz.nodes[node_i].set_stroke(
                color=ACCENT if done else PRIMARY, width=3.0 if done else 2.0
            )

    # -- lifecycle ------------------------------------------------------------------
    def arrive(self, scene, *, run_time=0.45):
        scene.add(self.t, self.texts)
        scene.play(FadeIn(self.ring), run_time=run_time)

    def go(self, scene, *, run_time: float):
        scene.play(
            self.t.animate.set_value(len(self.order)),
            run_time=run_time,
            rate_func=lambda a: a,
        )

    def detach(self):
        self.ring.clear_updaters()
        self.texts.clear_updaters()


class TreeFig:
    """A small hand-placed tree for the shapes TreeViz's perfect layout can't express."""

    def __init__(self, coords, edges, *, radius=0.30, fs=16, color=PRIMARY):
        self.nodes = {}
        self.texts = {}
        group = VGroup()
        for name, (x, y) in coords.items():
            c = Circle(radius=radius, stroke_color=color, stroke_width=2.0,
                       fill_color=PANEL, fill_opacity=1.0).move_to([x, y, 0])
            t = Text(name, font=MONO, font_size=fs, color=INK)
            fit_into(t, c, pad=0.05)
            t.move_to(c.get_center())
            self.nodes[name] = c
            self.texts[name] = t
            group.add(VGroup(c, t))
        lines = VGroup()
        for a, b in edges:
            lines.add(Line(self.nodes[a].get_center(), self.nodes[b].get_center(),
                           color=STROKE, stroke_width=2.0))
        self.edges = lines
        self.group = VGroup(lines, group)


class StackColumn:
    """Frames of the explicit stack, growing upward beside the tree."""

    def __init__(self, *, w=2.4, h=0.5, buff=0.14, x=-5.5, base_y=-1.6, fs=18):
        self.w, self.h, self.buff, self.x, self.base_y, self.fs = w, h, buff, x, base_y, fs
        self.frames = []

    def y_of(self, n: int) -> float:
        return self.base_y + n * (self.h + self.buff)

    def frame(self, n: int, text: str, color=PRIMARY):
        box = card(self.w, self.h, color=color, fill=PANEL)
        t = Text(text, font=MONO, font_size=self.fs, color=INK)
        fit_into(t, box, pad=0.2)
        t.move_to(box.get_center())
        v = VGroup(box, t).move_to([self.x, self.y_of(n), 0])
        self.frames.append(v)
        return v


class TreePattern(PrebakedVoiceMovingCameraScene):
    # ---------------------------------------------------------------------------- setup
    def construct(self):
        bg(self)
        for i in range(len(BEATS)):
            getattr(self, f"_beat{i}")()

    # ------------------------------------------------------------------------- utilities
    def _code(self, spec, *, fs=15, x=CODE_X):
        group = VGroup(*[Text(t, font=MONO, font_size=fs, color=c) for t, c in spec])
        group.arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to([x, 0.0, 0])
        return group

    def _reset_nodes(self, color=PRIMARY, width=2.0):
        return [self.viz.nodes[k].animate.set_stroke(color=color, width=width)
                for k in range(7)]

    def _walk(self, order, values, tr, *, line=None, run_time=None, lead=0.5):
        """Bring in a fresh walker for `order`, run it, and return it (un-detached)."""
        walker = Walker(self.viz, order, values)
        walker.arrive(self, run_time=0.4)
        if line is not None:
            self.play(Indicate(self.code[line], color=ACCENT, scale_factor=1.03),
                      run_time=0.55)
        if run_time is None:
            run_time = min(2.6, max(1.4, tr.duration * 0.42))
        walker.go(self, run_time=run_time)
        return walker

    def _drop_walker(self, walker, *, extra=None):
        walker.detach()
        self.remove(walker.t)
        mobs = [walker.ring, walker.texts]
        if extra is not None:
            mobs.append(extra)
        self.play(FadeOut(VGroup(*mobs)), run_time=0.3)

    # ---------------------------------------------------------------------------- beats
    def _beat0(self):
        """Hook: the same three lines, asked of every node."""
        with self.voiceover(text=BEATS[0]) as tr:
            swap_rails(self, headline("One function, asked of every node."),
                       caption("ask left · ask right · combine"))
            self.play(FadeIn(rule()), run_time=0.3)
            lines = VGroup(
                chip("ask left", color=PRIMARY, fs=BODY_FS),
                chip("ask right", color=PRIMARY, fs=BODY_FS),
                chip("combine", color=ACCENT, fs=BODY_FS),
            ).arrange(RIGHT, buff=0.75).move_to(stage_center(0.1))
            self.play(FadeIn(lines, shift=UP * 0.2), lag_ratio=0.35,
                      run_time=min(1.3, max(0.7, tr.duration * 0.3)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._hook = lines

    def _beat1(self):
        """The one design question: up to the parent, down from the children."""
        with self.voiceover(text=BEATS[1]) as tr:
            swap_rails(self, headline("What goes down, what comes back?"),
                       caption("the only design question"))
            self.play(self._hook.animate.shift(UP * 0.55), run_time=0.4)
            up = Text("↑ what it hands back to its parent", font=MONO, font_size=BODY_FS,
                      color=GOOD)
            down = Text("↓ what it needs from its children", font=MONO, font_size=BODY_FS,
                        color=WINDOW)
            VGroup(up, down).arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to([0, -0.9, 0])
            self.play(FadeIn(down, shift=UP * 0.15), run_time=0.45)
            self.play(FadeIn(up, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._question = VGroup(up, down)

    def _beat2(self):
        """A tree is a family: the hero tree arrives and the root is named."""
        with self.voiceover(text=BEATS[2]) as tr:
            swap_rails(self, headline("A tree is a family."),
                       caption("one parent each, one ancestor"))
            self.play(FadeOut(VGroup(self._hook, self._question)), run_time=0.3)
            self.viz, self.labels = make_tree(PLAIN)
            self.tree = VGroup(self.viz.group, self.labels)
            self.play(FadeIn(self.tree), run_time=min(1.2, max(0.6, tr.duration * 0.28)))
            self.play(Indicate(self.viz.nodes[0], color=ACCENT, scale_factor=1.2),
                      run_time=0.6)
            root = Text("root", font=MONO, font_size=SMALL_FS, color=ACCENT)
            root.next_to(self.viz.nodes[0], UP, buff=0.2)
            self.play(FadeIn(root, shift=DOWN * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._root = root

    def _beat3(self):
        """Ask the top person: the question travels down the edges."""
        with self.voiceover(text=BEATS[3]) as tr:
            swap_rails(self, headline("Ask the top person."),
                       caption("they ask their own children"))
            self.play(*[self.viz.edges[k].animate.set_color(WINDOW).set_stroke(width=2.8)
                        for k in (0, 1)],
                      *[self.viz.nodes[k].animate.set_stroke(WINDOW, width=2.6)
                        for k in (1, 2)],
                      run_time=min(0.9, max(0.5, tr.duration * 0.2)))
            ask = Text("ask left, ask right", font=MONO, font_size=SMALL_FS, color=WINDOW)
            ask.next_to(self.viz.nodes[1], LEFT, buff=0.35)
            self.play(FadeIn(ask, shift=RIGHT * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._ask = ask

    def _beat4(self):
        """The base case: the nodes with no children answer immediately."""
        with self.voiceover(text=BEATS[4]) as tr:
            swap_rails(self, headline("No children means base case."),
                       caption("leaves answer immediately"))
            self.play(FadeOut(self._ask, run_time=0.25))
            self.play(*[self.viz.nodes[k].animate.set_stroke(GOOD, width=2.8)
                        for k in (3, 4, 5, 6)],
                      run_time=min(1.0, max(0.55, tr.duration * 0.22)))
            chip_lb = Text("base case", font=MONO, font_size=SMALL_FS, color=GOOD)
            chip_lb.next_to(self.viz.nodes[5], DOWN, buff=0.25)
            self.play(FadeIn(chip_lb, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._base = chip_lb

    def _beat5(self):
        """The three lines, on the code body that never changes again."""
        with self.voiceover(text=BEATS[5]) as tr:
            swap_rails(self, headline("Everyone else asks and combines."),
                       caption("ask left · ask right · combine"))
            self.play(FadeOut(VGroup(self._root, self._base)), run_time=0.25)
            self.play(*self._reset_nodes(color=PRIMARY), run_time=0.5)
            self.code = self._code(DFS_CODE)
            self.play(Write(self.code), run_time=min(1.4, max(0.7, tr.duration * 0.32)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat6(self):
        """DFS: dive as deep as you can before turning back."""
        with self.voiceover(text=BEATS[6]) as tr:
            swap_rails(self, headline("Depth first dives deep."),
                       caption("recursion, or an explicit stack"))
            dive = [0, 1, 3]
            self.play(*[self.viz.nodes[k].animate.set_stroke(ACCENT, width=3.0) for k in dive],
                      *[self.viz.edges[k].animate.set_color(ACCENT).set_stroke(width=2.8)
                        for k in (0,)],
                      run_time=min(1.0, max(0.55, tr.duration * 0.22)))
            path = Line(self.viz.nodes[0].get_center(), self.viz.nodes[3].get_center(),
                        color=ACCENT, stroke_width=3.0)
            self.play(ShowPassingFlash(path, time_width=0.6),
                      run_time=min(1.0, max(0.55, tr.duration * 0.22)))
            deep = chip("deepest first, then turn back", color=ACCENT, fs=SMALL_FS)
            deep.move_to([-1.0, -2.3, 0])
            self.play(FadeIn(deep, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._dfs = deep

    def _beat7(self):
        """BFS: one generation at a time, with the queue that makes it work."""
        with self.voiceover(text=BEATS[7]) as tr:
            swap_rails(self, headline("Breadth first takes one level."),
                       caption("one generation at a time"))
            self.play(FadeOut(self._dfs, run_time=0.25))
            self.play(*self._reset_nodes(color=PRIMARY),
                      *[e.animate.set_color(STROKE).set_stroke(width=2.0)
                        for e in self.viz.edges],
                      run_time=0.5)
            bands = VGroup()
            for level in range(3):
                ys = [self.viz.nodes[k].get_center()[1] for k in range(7)]
                xs = [self.viz.nodes[k].get_center()[0] for k in
                      range(2 ** level - 1, 2 ** (level + 1) - 1)]
                y = ys[2 ** level - 1]
                band = RoundedRectangle(
                    corner_radius=0.12,
                    width=max(xs) - min(xs) + 0.75,
                    height=0.72,
                    stroke_color=WINDOW,
                    stroke_width=2.0,
                    fill_color=WINDOW,
                    fill_opacity=0.15,
                ).move_to([(max(xs) + min(xs)) / 2, y, 0])
                bands.add(band)
            queue = chip("queue: 1  →  2 3  →  4 5 6 7", color=WINDOW, fs=SMALL_FS)
            queue.move_to([-1.0, 1.85, 0])
            self.play(FadeIn(bands[0]), run_time=0.35)
            self.play(FadeIn(bands[1]), FadeIn(queue), run_time=0.45)
            self.play(FadeIn(bands[2]), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._bands = VGroup(bands, queue)

    def _beat8(self):
        """The tell that decides DFS vs BFS before you write anything."""
        with self.voiceover(text=BEATS[8]) as tr:
            swap_rails(self, headline("Level or nearest means BFS."),
                       caption("everything else is DFS"))
            self.play(FadeOut(self._bands, run_time=0.3))
            bfs = chip("level · nearest · minimum depth", color=WINDOW, fs=BODY_FS)
            dfs = chip("path · depth · is this tree…", color=PRIMARY, fs=BODY_FS)
            pair = VGroup(bfs, dfs).arrange(DOWN, buff=0.5).move_to([-1.0, -0.15, 0])
            self.play(FadeIn(bfs, shift=UP * 0.2), run_time=0.45)
            self.play(FadeIn(dfs, shift=UP * 0.2), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._tell = pair

    def _beat9(self):
        """One function, three orders: only the visit line moves."""
        with self.voiceover(text=BEATS[9]) as tr:
            swap_rails(self, headline("One function, three orders."),
                       caption("only the visit line moves"))
            self.play(FadeOut(self._tell, run_time=0.3))
            for idx in (2, 4, 6):
                self.play(Indicate(self.code[idx], color=ACCENT, scale_factor=1.04),
                          run_time=min(0.6, max(0.35, tr.duration * 0.12)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat10(self):
        """Preorder: visit before the calls — root, left, right."""
        with self.voiceover(text=BEATS[10]) as tr:
            swap_rails(self, headline("Visit before the calls."),
                       caption("preorder: root, left, right"))
            self.walker = self._walk(PRE_ORDER, [1, 2, 4, 5, 3, 6, 7], tr,
                                     line=VISIT_LINE[10])
            order_note = Text("preorder", font=MONO, font_size=SMALL_FS, color=ACCENT)
            order_note.next_to(self.walker.texts, LEFT, buff=0.45)
            self.play(FadeIn(order_note), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._order_note = order_note

    def _beat11(self):
        """Inorder: visit between the calls — left, root, right."""
        with self.voiceover(text=BEATS[11]) as tr:
            swap_rails(self, headline("Visit between the calls."),
                       caption("inorder: left, root, right"))
            self.play(FadeOut(self._order_note, run_time=0.2))
            self._drop_walker(self.walker)
            self.play(*self._reset_nodes(color=PRIMARY), run_time=0.3)
            self.walker = self._walk(IN_ORDER, [4, 2, 5, 1, 6, 3, 7], tr,
                                     line=VISIT_LINE[11])
            note = Text("inorder", font=MONO, font_size=SMALL_FS, color=ACCENT)
            note.next_to(self.walker.texts, LEFT, buff=0.45)
            self.play(FadeIn(note), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._order_note = note

    def _beat12(self):
        """The BST tell: relabel the tree, walk inorder again, and it comes out sorted."""
        with self.voiceover(text=BEATS[12]) as tr:
            swap_rails(self, headline("Inorder on a BST is sorted."),
                       caption("that is the BST tell"))
            self.play(FadeOut(self._order_note, run_time=0.2))
            self._drop_walker(self.walker)
            self.play(*self._reset_nodes(color=PRIMARY), run_time=0.3)
            tag = chip("make it a BST", color=WINDOW, fs=SMALL_FS)
            tag.move_to([-1.0, 1.75, 0])
            self.labels, anims = relabel(self.labels, BST)
            self.play(FadeIn(tag), *anims, run_time=min(1.0, max(0.55, tr.duration * 0.22)))
            self.walker = self._walk(IN_ORDER, [1, 2, 3, 4, 5, 6, 7], tr,
                                     line=VISIT_LINE[12])
            sorted_chip = chip("sorted ✓  →  a valid BST", color=GOOD, fs=SMALL_FS)
            sorted_chip.move_to([-1.0, 1.75, 0])
            self.play(FadeOut(tag), FadeIn(sorted_chip, shift=UP * 0.15), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._sorted = sorted_chip

    def _beat13(self):
        """Postorder: visit after both calls — children first."""
        with self.voiceover(text=BEATS[13]) as tr:
            swap_rails(self, headline("Visit after both calls."),
                       caption("postorder: children first"))
            self.play(FadeOut(self._sorted, run_time=0.2))
            self._drop_walker(self.walker)
            self.play(*self._reset_nodes(color=PRIMARY), run_time=0.3)
            self.labels, anims = relabel(self.labels, PLAIN)
            self.play(*anims, run_time=min(0.9, max(0.5, tr.duration * 0.2)))
            self.walker = self._walk(POST_ORDER, [4, 5, 2, 6, 7, 3, 1], tr,
                                     line=VISIT_LINE[13])
            note = Text("postorder", font=MONO, font_size=SMALL_FS, color=ACCENT)
            note.next_to(self.walker.texts, LEFT, buff=0.45)
            self.play(FadeIn(note), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._order_note = note

    def _beat14(self):
        """The recursive-vs-iterative trade: the same inorder, with your own stack."""
        with self.voiceover(text=BEATS[14]) as tr:
            swap_rails(self, headline("Or dive left with a stack."),
                       caption("iterative inorder: pop, visit, go right"))
            self.play(FadeOut(self._order_note, run_time=0.2))
            self._drop_walker(self.walker)
            self.play(*self._reset_nodes(color=PRIMARY),
                      FadeOut(self.code), run_time=0.4)
            self.play(self.tree.animate.set_opacity(0.22), run_time=0.4)
            st = StackColumn()
            it_code = self._code([
                ("stack, node = [], root", INK),
                ("while stack or node:", INK),
                ("    while node:", MUTED),
                ("        stack.append(node)", MUTED),
                ("        node = node.left", MUTED),
                ("    node = stack.pop()   # visit", ACCENT),
                ("    node = node.right", GOOD),
            ], fs=14, x=3.6)
            self.play(Write(it_code), run_time=min(0.95, max(0.55, tr.duration * 0.2)))
            for i, v in enumerate(("1", "2", "4")):
                self.play(FadeIn(st.frame(i, v), shift=UP * 0.2),
                          run_time=min(0.4, max(0.24, tr.duration * 0.07)))
            seen = Text("visit 4", font=MONO, font_size=SMALL_FS, color=GOOD)
            seen.next_to(st.frames[2], DOWN, buff=0.9)
            self.play(FadeOut(st.frames[2], shift=UP * 0.25), FadeIn(seen),
                      run_time=min(0.5, max(0.3, tr.duration * 0.11)))
            self.play(FadeIn(st.frame(3, "5"), shift=UP * 0.2),
                      run_time=min(0.45, max(0.28, tr.duration * 0.09)))
            seen5 = Text("visit 5", font=MONO, font_size=SMALL_FS, color=GOOD)
            seen5.next_to(seen, DOWN, buff=0.3)
            self.play(FadeOut(st.frames[3], shift=UP * 0.25), FadeIn(seen5),
                      run_time=min(0.5, max(0.3, tr.duration * 0.11)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._iter = VGroup(it_code, seen, seen5, st.frames[0], st.frames[1])

    def _beat15(self):
        """Level order's whole trick: read the queue length once."""
        with self.voiceover(text=BEATS[15]) as tr:
            swap_rails(self, headline("Read the queue length once."),
                       caption("that loop is one whole level"))
            self.play(FadeOut(self._iter, run_time=0.3))
            self.play(self.tree.animate.set_opacity(1.0), run_time=0.4)
            bands = VGroup()
            for level in range(3):
                xs = [self.viz.nodes[k].get_center()[0] for k in
                      range(2 ** level - 1, 2 ** (level + 1) - 1)]
                y = self.viz.nodes[2 ** level - 1].get_center()[1]
                bands.add(RoundedRectangle(
                    corner_radius=0.12,
                    width=max(xs) - min(xs) + 0.75,
                    height=0.72,
                    stroke_color=WINDOW,
                    stroke_width=2.0,
                    fill_color=WINDOW,
                    fill_opacity=0.16,
                ).move_to([(max(xs) + min(xs)) / 2, y, 0]))
            code = self._code([
                ("while queue:", INK),
                ("    for _ in range(len(queue)):", ACCENT),
                ("        node = queue.popleft()", MUTED),
                ("        level.append(node.val)", MUTED),
            ], fs=15, x=3.9)
            self.play(FadeIn(bands), Write(code), run_time=min(0.95, max(0.55, tr.duration * 0.2)))
            self.walker = self._walk(LEVEL_ORDER, [1, 2, 3, 4, 5, 6, 7], tr)
            note = Text("level order", font=MONO, font_size=SMALL_FS, color=WINDOW)
            note.next_to(self.walker.texts, LEFT, buff=0.45)
            self.play(FadeIn(note), run_time=0.3)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._level = VGroup(bands, code, note)

    def _beat16(self):
        """Bottom-up: children return a value, the parent combines it."""
        with self.voiceover(text=BEATS[16]) as tr:
            swap_rails(self, headline("Return one value, record another."),
                       caption("the answer comes from both arms"))
            self.play(FadeOut(self._level, run_time=0.3))
            self._drop_walker(self.walker)
            self.play(*self._reset_nodes(color=PRIMARY), run_time=0.3)
            heights = VGroup()
            for k, (dx, dy) in {3: (0.3, 0.0), 4: (0.3, 0.0), 5: (0.3, 0.0),
                                6: (0.3, 0.0)}.items():
                t = Text("h=1", font=MONO, font_size=SMALL_FS, color=GOOD)
                t.next_to(self.viz.nodes[k], RIGHT, buff=dx)
                heights.add(t)
            self.play(*[FadeIn(t, shift=UP * 0.12) for t in heights], lag_ratio=0.25,
                      run_time=min(1.0, max(0.55, tr.duration * 0.22)))
            mid = Text("h=2", font=MONO, font_size=SMALL_FS, color=ACCENT)
            mid.next_to(self.viz.nodes[1], RIGHT, buff=0.35)
            top = Text("h=3", font=MONO, font_size=SMALL_FS, color=ACCENT)
            top.next_to(self.viz.nodes[0], RIGHT, buff=0.3)
            self.play(FadeIn(mid), run_time=0.4)
            self.play(FadeIn(top), run_time=0.4)
            rule_chip = chip("return 1 + max(L, R)", color=ACCENT, fs=SMALL_FS)
            rule_chip.move_to([1.6, -2.3, 0])
            self.play(FadeIn(rule_chip, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._bottomup = VGroup(heights, mid, top, rule_chip)

    def _beat17(self):
        """Diameter: the return value is one arm, the answer uses both."""
        with self.voiceover(text=BEATS[17]) as tr:
            swap_rails(self, headline("Diameter: one arm up, two arms kept."),
                       caption("returns max(L, R), records L + R"))
            self.play(FadeOut(self._bottomup, run_time=0.3))
            left_arm = [0, 1, 3]
            right_arm = [2]
            self.play(*[self.viz.nodes[k].animate.set_stroke(ACCENT, width=3.0)
                        for k in left_arm],
                      *[self.viz.edges[k].animate.set_color(ACCENT).set_stroke(width=2.8)
                        for k in (0,)],
                      run_time=0.5)
            self.play(*[self.viz.nodes[k].animate.set_stroke(WINDOW, width=3.0)
                        for k in right_arm],
                      *[self.viz.edges[k].animate.set_color(WINDOW).set_stroke(width=2.8)
                        for k in (1,)],
                      run_time=0.5)
            a = Text("L", font=MONO, font_size=BODY_FS, color=ACCENT)
            a.next_to(self.viz.nodes[1], LEFT, buff=0.3)
            b = Text("R", font=MONO, font_size=BODY_FS, color=WINDOW)
            b.next_to(self.viz.nodes[2], RIGHT, buff=0.3)
            self.play(FadeIn(a), FadeIn(b), run_time=0.4)
            note = Text("returns max(L, R)  ·  records L + R", font=MONO,
                        font_size=SMALL_FS, color=GOOD)
            note.move_to([0, -2.3, 0])
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._diameter = VGroup(a, b, note)

    def _beat18(self):
        """The sentinel: height and verdict travel up together."""
        with self.voiceover(text=BEATS[18]) as tr:
            swap_rails(self, headline("One number carries the verdict."),
                       caption("minus one means already broken"))
            self.play(FadeOut(self._diameter, run_time=0.3))
            self.play(*self._reset_nodes(color=PRIMARY),
                      *[e.animate.set_color(STROKE).set_stroke(width=2.0)
                        for e in self.viz.edges], run_time=0.4)
            sentinel = VGroup()
            for k in (3, 1, 0):
                t = Text("-1", font=MONO, font_size=BODY_FS, color=GONE)
                t.next_to(self.viz.nodes[k], RIGHT, buff=0.3)
                sentinel.add(t)
            self.play(FadeIn(sentinel[0], shift=UP * 0.15), run_time=0.4)
            self.play(FadeIn(sentinel[1], shift=UP * 0.15), run_time=0.4)
            self.play(FadeIn(sentinel[2], shift=UP * 0.15), run_time=0.4)
            cost = Text("height and verdict, one pass: O(n)", font=MONO,
                        font_size=SMALL_FS, color=GOOD)
            cost.move_to([0, -2.3, 0])
            self.play(FadeIn(cost, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._sentinel = VGroup(sentinel, cost)

    def _beat19(self):
        """Validate a BST: carry (lo, hi) bounds — the parent alone is not enough."""
        with self.voiceover(text=BEATS[19]) as tr:
            swap_rails(self, headline("Carry low and high bounds."),
                       caption("the parent alone is not enough"))
            self.play(FadeOut(VGroup(self.tree, self._sentinel)), run_time=0.35)
            fig = TreeFig({"5": (0.4, 1.05), "1": (-1.9, 0.1), "6": (2.2, 0.1),
                           "4": (1.2, -0.95), "7": (3.3, -0.95)},
                          [("5", "1"), ("5", "6"), ("6", "4"), ("6", "7")])
            bounds = VGroup(
                Text("(-inf, inf)", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("(-inf, 5)", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("(5, inf)", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("(5, 6)", font=MONO, font_size=SMALL_FS, color=GONE),
                Text("(6, inf)", font=MONO, font_size=SMALL_FS, color=MUTED),
            )
            for t, name, side in zip(bounds, ("5", "1", "6", "4", "7"),
                                     ("UP", "LEFT", "UP", "RIGHT", "RIGHT")):
                if side == "UP":
                    t.next_to(fig.nodes[name], UP, buff=0.22)
                elif side == "LEFT":
                    t.next_to(fig.nodes[name], LEFT, buff=0.25)
                else:
                    t.next_to(fig.nodes[name], RIGHT, buff=0.25)
            self.play(FadeIn(fig.group), run_time=min(0.75, max(0.45, tr.duration * 0.16)))
            self.play(*[FadeIn(t, shift=UP * 0.12) for t in bounds[:3]], lag_ratio=0.25,
                      run_time=min(1.0, max(0.55, tr.duration * 0.22)))
            self.camera.frame.save_state()  # bare: stores only
            self.play(
                self.camera.auto_zoom([fig.group, bounds], margin=1.0),
                run_time=min(0.85, max(0.45, tr.duration * 0.17)),
            )
            self.play(FadeIn(bounds[3], shift=UP * 0.12), FadeIn(bounds[4], shift=UP * 0.12),
                      run_time=0.5)
            self.play(Indicate(fig.nodes["4"], color=GONE, scale_factor=1.2),
                      Indicate(bounds[3], color=GONE, scale_factor=1.1),
                      run_time=0.8)
            self.play(Restore(self.camera.frame), run_time=0.5)
            verdict = Text("4 is left of 6, but right of 5  →  not a BST", font=MONO,
                           font_size=SMALL_FS, color=GONE)
            verdict.move_to([0.4, -2.25, 0])
            self.play(FadeIn(verdict, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._bst = VGroup(fig.group, bounds, verdict)

    def _beat20(self):
        """The two null checks, in the order they must appear."""
        with self.voiceover(text=BEATS[20]) as tr:
            swap_rails(self, headline("Two null checks, in order."),
                       caption("both empty, then either empty"))
            self.play(FadeOut(self._bst, run_time=0.3))
            code = VGroup(
                Text("if not a and not b: return True", font=MONO, font_size=BODY_FS,
                     color=GOOD),
                Text("if not a or  not b: return False", font=MONO, font_size=BODY_FS,
                     color=GONE),
                Text("return a.val == b.val and same(a.left, b.left)", font=MONO,
                     font_size=SMALL_FS, color=INK),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.34).move_to([-0.4, 0.35, 0])
            tags = VGroup(
                Text("# both empty", font=MONO, font_size=SMALL_FS, color=GOOD),
                Text("# exactly one empty", font=MONO, font_size=SMALL_FS, color=GONE),
            )
            for tag, line in zip(tags, code):
                tag.move_to([code.get_right()[0] + 0.4 + tag.width / 2,
                             line.get_center()[1], 0])
            self.play(Write(code), run_time=min(1.2, max(0.6, tr.duration * 0.27)))
            self.play(FadeIn(tags, shift=LEFT * 0.12), lag_ratio=0.3,
                      run_time=min(0.9, max(0.5, tr.duration * 0.2)))
            self.play(Indicate(code[1], color=GONE, scale_factor=1.03), run_time=0.6)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._nulls = VGroup(code, tags)

    def _beat21(self):
        """Complexity, stated cold."""
        with self.voiceover(text=BEATS[21]) as tr:
            swap_rails(self, headline("One pass is linear."),
                       caption("the sentinel keeps it linear"))
            self.play(FadeOut(self._nulls, run_time=0.3))
            row = VGroup(
                self._mchip(r"O(n)", GOOD),
                self._mchip(r"O(h)", PRIMARY),
                self._mchip(r"O(w)", WINDOW),
            ).arrange(RIGHT, buff=0.85).move_to([0, 0.7, 0])
            caps = VGroup(
                Text("any single DFS / BFS", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("recursion depth", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("queue width", font=MONO, font_size=SMALL_FS, color=MUTED),
            )
            for c, box in zip(caps, row):
                c.next_to(box, DOWN, buff=0.22)
            note = Text("balanced with the sentinel: O(n), not O(n²)", font=MONO,
                        font_size=BODY_FS, color=GOOD)
            note.move_to([0, -1.35, 0])
            self.play(*[FadeIn(m, shift=UP * 0.2) for m in row], lag_ratio=0.25,
                      run_time=min(1.2, max(0.6, tr.duration * 0.28)))
            self.play(FadeIn(caps), run_time=0.4)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._complex = VGroup(row, caps, note)

    def _mchip(self, tex, color):
        m = MathTex(tex, color=color).scale(0.85)
        b = card(m.width + 0.7, m.height + 0.45, color=color, fill=PANEL)
        m.move_to(b.get_center())
        return VGroup(b, m)

    def _beat22(self):
        """Recognition: the signals, and the structure that is always there."""
        with self.voiceover(text=BEATS[22]) as tr:
            swap_rails(self, headline("When to reach for it."),
                       caption("level · mirror · ancestor · path"))
            self.play(FadeOut(self._complex, run_time=0.3))
            yes = VGroup(
                Text("✓  a node with .left and .right", font=MONO, font_size=BODY_FS,
                     color=GOOD),
                Text("✓  level, zigzag, each level", font=MONO, font_size=BODY_FS,
                     color=GOOD),
                Text("✓  mirror, same, symmetric, flip", font=MONO, font_size=BODY_FS,
                     color=GOOD),
                Text("✓  ancestor, path sum, depth", font=MONO, font_size=BODY_FS,
                     color=GOOD),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.28).move_to([0, 0.35, 0])
            self.play(*[FadeIn(t, shift=RIGHT * 0.2) for t in yes], lag_ratio=0.28,
                      run_time=min(1.5, max(0.8, tr.duration * 0.35)))
            no = Text("✗  a count or a best value → DP", font=MONO, font_size=BODY_FS,
                      color=GONE)
            no.move_to([0, -1.75, 0])
            self.play(FadeIn(no, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._recognise = VGroup(yes, no)

    def _beat23(self):
        """Recall card: the three lines, one idea to leave with."""
        with self.voiceover(text=BEATS[23]) as tr:
            swap_rails(self, headline("Ask left, ask right, combine."),
                       caption("know what comes back up"))
            self.play(FadeOut(self._recognise, run_time=0.3))
            box = card(9.4, 1.9, color=ACCENT, fill=PANEL)
            box.move_to(stage_center(-0.1))
            top = Text("Ask left · Ask right · Combine", font=MONO, font_size=30, color=ACCENT)
            mid = Text("DFS by default  ·  BFS on 'level'", font=MONO, font_size=SMALL_FS,
                       color=MUTED)
            sub = Text("O(n) time  ·  O(h) space  ·  BST inorder is sorted",
                       font=MONO, font_size=SMALL_FS, color=MUTED)
            VGroup(top, mid, sub).arrange(DOWN, buff=0.2).move_to(box.get_center())
            self.play(FadeIn(box, scale=0.96), run_time=0.45)
            self.play(Write(top), run_time=0.5)
            self.play(FadeIn(mid), FadeIn(sub), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
