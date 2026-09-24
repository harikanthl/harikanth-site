"""
Pattern 14 — Graphs.

The film follows the card's own argument: hook -> nodes and edges -> the one loop -> the
container that picks the algorithm -> the same neighbours in opposite orders -> BFS as a
flood filling one ring per round -> DFS diving then backtracking -> why first arrival is
the fewest edges -> counting components -> Kahn's ordering -> Dijkstra when edges carry
weights -> Dijkstra's one-line variants -> what goes wrong -> recognition -> complexity ->
the recall card.

The visual spine is one graph whose frontier is animated two ways: `graph_viz` with explicit
coordinates keeps the drawing stable for the whole film, `ShowPassingFlash` lights the edge
being walked, and the frontier itself is a computed ring (always_redraw + ValueTracker), so
"flood" is something you watch rather than something you are told.
"""

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Circumscribe,
    Circle,
    Dot,
    FadeIn,
    FadeOut,
    Indicate,
    Line,
    ReplacementTransform,
    Restore,
    ShowPassingFlash,
    Text,
    VGroup,
    ValueTracker,
    Write,
    always_redraw,
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
from shots import chip, graph_viz

PATTERN_SLUG = "graphs"
TITLE = "Graphs"
SUMMARY = "BFS and DFS are the same loop; only the frontier container changes."
SCENE_CLASS = "Graphs"
POSTER_AT = 30.0

# ---------------------------------------------------------------------------------------
# Fixed coordinates, in one place, so every beat draws the SAME graph (charter rule 6).
# ---------------------------------------------------------------------------------------
COORDS = {
    "A": [0.0, 2.5],
    "B": [-2.6, 1.1],
    "C": [2.6, 1.1],
    "D": [-5.0, -0.3],
    "E": [0.0, -0.3],
    "F": [3.6, -0.4],
    "G": [5.0, -1.7],
    "H": [-3.4, -1.9],
    "I": [1.6, -2.2],
}
EDGE_LIST = [
    ("A", "B"), ("A", "C"), ("B", "D"), ("B", "E"), ("C", "E"), ("C", "F"),
    ("D", "H"), ("E", "H"), ("E", "I"), ("F", "G"), ("F", "I"), ("B", "H"),
]
NAMES = list(COORDS)
RADIUS = 0.28

BEATS = [
    # 0 hook
    "Two ways to flood a graph. Breadth first spreads in rings. Depth first dives deep, "
    "then retreats.",
    # 1 nodes and edges
    "A graph is nodes joined by edges. Start at one node; its edges name the next ones.",
    # 2 the loop
    "The whole pattern is one loop: walk along edges, and never revisit a node. Mark each "
    "node the moment you reach it.",
    # 3 the container
    "The only choice is what holds what you've found but not explored. A queue gives "
    "breadth first. A stack gives depth first.",
    # 4 same neighbours, different order
    "Starting from A, both find B and C. The queue takes the older one. The stack takes "
    "the newer one.",
    # 5 BFS
    "Breadth first expands one whole ring per round. Every node at distance two is found "
    "before any node at distance three.",
    # 6 DFS
    "Depth first pushes neighbours and dives. It runs down one branch to a dead end, then "
    "backtracks to the last fork.",
    # 7 shortest path
    "That ring order is why breadth first gives shortest paths: first touch, fewest edges.",
    # 8 components
    "One search explores one connected component. Count them by counting how many times "
    "you had to start over.",
    # 9 topo sort
    "For prerequisites, repeatedly remove nodes with no unmet dependency. If some remain, "
    "there is a cycle.",
    # 10 dijkstra
    "When edges have weights, a heap picks the cheapest node instead. That's Dijkstra, and "
    "step count is no longer cost.",
    # 11 dijkstra variants
    "Free the maximum edge instead of the sum, and Dijkstra becomes minimum effort. Key "
    "the heap on the edge itself, and it's Prim's.",
    # 12 marking visited
    "Mark nodes when you queue them, not when you pop them, or a node enters the queue "
    "several times.",
    # 13 cycle parents
    "For undirected cycles, remember where you came from, since every edge runs both ways. "
    "A directed graph needs more.",
    # 14 bellman ford
    "Bellman-Ford relaxes every edge once per round, so each round uses one more edge. "
    "Copy the distances first, or one path jumps ahead.",
    # 15 recognition
    "The word graph is rarely in the statement. Islands on a grid, fewest steps, and "
    "prerequisite orders are all graphs.",
    # 16 anti-signal
    "A tree needs no visited set. And if every edge costs the same, breadth first already "
    "gives the shortest path.",
    # 17 complexity
    "Time is V plus E: every node and edge once. Space is V for visited and the frontier.",
    # 18 recall
    "Same loop. Different container. Stack, queue, or heap. That picks your algorithm.",
]

CHAPTERS = {
    0: "The hook",
    1: "Nodes and edges",
    2: "The loop",
    3: "The container",
    4: "Same graph, two orders",
    5: "BFS: the flood",
    6: "DFS: dive and retreat",
    7: "Why BFS is shortest",
    8: "Counting components",
    9: "Topological sort",
    10: "Weighted edges",
    11: "Dijkstra's variants",
    12: "What goes wrong",
    15: "How to recognise it",
    17: "Complexity",
    18: "Recall",
}


# ---------------------------------------------------------------------------------------
# Local primitives — everything here is film-specific and lives in this file.
# ---------------------------------------------------------------------------------------
class _Frontier:
    """The frontier as a row of slots: queue fills right (FIFO), stack fills up (LIFO).

    Items are round tokens (the same shape as a graph node) because that keeps each item's
    footprint exactly its own: the layout QA treats a wide text bounding box as overlapping
    its neighbour long before the glyphs actually touch.
    """

    def __init__(self, slots: int, *, axis: str, color):
        self.axis = axis
        self.labels = [None] * slots
        self.tokens = []
        for _ in range(slots):
            ring = Circle(radius=0.19, stroke_color=color, stroke_width=1.8,
                          fill_color=PANEL, fill_opacity=1.0)
            self.tokens.append(ring)
        group = VGroup(*self.tokens)
        if axis == "h":
            group.arrange(RIGHT, buff=0.14)
        else:
            group.arrange(UP, buff=0.14)
        self.tokens_group = group

    def reveal(self, i: int, label: str, *, color=ACCENT):
        ring = self.tokens[i]
        # the stack packs its slots closer than the queue, so its glyphs run smaller, which
        # keeps each token's text box clear of its neighbour
        fs = 14 if self.axis == "v" else SMALL_FS
        t = Text(label, font=MONO, font_size=fs, color=INK)
        t.move_to(ring.get_center())
        self.labels[i] = t
        return [
            ring.animate.set_stroke(color=color, width=2.4).set_fill(color, opacity=0.26),
            FadeIn(t),
        ]

    def hide(self, i: int, *, color=PRIMARY, live=None):
        ring = self.tokens[i]
        anims = [ring.animate.set_stroke(color=color, width=1.8).set_fill(PANEL, opacity=1.0)]
        if self.labels[i] is not None:
            target = live(self.labels[i]) if live else self.labels[i]
            anims.append(FadeOut(target))
            self._pending_remove.append(target)
            self.labels[i] = None
        return anims

    def hide_all(self, live=None):
        anims = []
        for i in range(len(self.tokens)):
            anims += self.hide(i, live=live)
        return anims

    def take_removals(self):
        out, self._pending_remove = self._pending_remove, []
        return out

    _pending_remove: list = []


def _tokens(labels, *, axis: str, color=PRIMARY, fs: int = SMALL_FS) -> VGroup:
    """A row (queue) or column (stack) of round frontier tokens carrying the given labels."""
    rings = VGroup()
    for lb in labels:
        ring = Circle(radius=0.19, stroke_color=color, stroke_width=2.2,
                      fill_color=color, fill_opacity=0.24)
        t = Text(lb, font=MONO, font_size=fs, color=INK)
        t.move_to(ring.get_center())
        rings.add(VGroup(ring, t))
    if axis == "h":
        rings.arrange(RIGHT, buff=0.14)
    else:
        rings.arrange(UP, buff=0.14)
    return rings


class _Board:
    """The queue and the stack side by side: the same frontier in two containers."""

    SLOTS = 4

    def __init__(self, q_center, s_center, *, w: float = 1.7, h: float = 0.85):
        self.q = _Frontier(self.SLOTS, axis="h", color=WINDOW)
        self.s = _Frontier(self.SLOTS, axis="v", color=ACCENT)
        self.q_box = card(w, h, color=STROKE, fill=PANEL)
        self.s_box = card(w, h, color=STROKE, fill=PANEL)
        self.q_label = Text("queue", font=MONO, font_size=SMALL_FS, color=WINDOW)
        self.s_label = Text("stack", font=MONO, font_size=SMALL_FS, color=ACCENT)
        self.q_box.move_to(q_center)
        self.s_box.move_to(s_center)
        self.layout()

    def layout(self):
        self.q.tokens_group.move_to(self.q_box.get_center())
        self.s.tokens_group.arrange(UP, buff=0.14)
        self.s.tokens_group.move_to(self.s_box.get_center())
        self.q_label.next_to(self.q_box, DOWN, buff=0.6)
        self.s_label.next_to(self.s_box, DOWN, buff=0.6)

    def group(self):
        return VGroup(self.q_box, self.s_box, self.q.tokens_group, self.s.tokens_group,
                      self.q_label, self.s_label)


def _edge_flash(edge, color=ACCENT):
    """A travelling highlight along one edge — the edge the narration just named."""
    return ShowPassingFlash(
        edge.copy().set_stroke(color=color, width=6), time_width=0.55
    )


def _ring(circle: Circle, color=ACCENT, scale: float = 1.55, width: float = 2.6):
    r = Circle(radius=circle.radius * scale, stroke_color=color, stroke_width=width)
    r.move_to(circle.get_center())
    return r


class Graphs(PrebakedVoiceMovingCameraScene):
    # ---------------------------------------------------------------------------- setup
    def construct(self):
        bg(self)
        self.g = graph_viz(COORDS, EDGE_LIST, radius=RADIUS, color=PRIMARY)
        self.g.move_to([0, -0.15, 0])
        self.edges = self.g[0]
        self.nodes = self.g[1]
        self.node = {name: self.nodes[i] for i, name in enumerate(NAMES)}
        self._board = None
        for i in range(len(BEATS)):
            self._sweep()
            getattr(self, f"_beat{i}")()

    def _restage(self):
        """Adopt the graph instances the scene is actually holding.

        `FadeIn(node)` stages a COPY per node (see `_live`), so repainting or fading the
        originals would touch objects that are not on screen. After the entrance animation
        finishes, this re-points `self.g`, `self.node` and `self.graph_mobs` at what is
        really on the stage.
        """
        found = {}
        groups = []
        for name, (x, y) in COORDS.items():
            best, best_d = None, 0.5
            for m in self.mobjects:
                for sub in m.get_family():
                    if not sub.submobjects:
                        continue
                    d = ((float(sub.get_center()[0]) - x) ** 2
                         + (float(sub.get_center()[1]) - y) ** 2) ** 0.5
                    if d < best_d:
                        best, best_d = sub, d
            if best is not None:
                found[name] = best
                groups.append(best)
        if len(found) != len(COORDS):
            return
        self.node = found
        self.g = VGroup(*groups)
        # Top-level stage mobjects that are, or contain, one of the staged node groups, are
        # the graph's own furniture (its edges). Keep them so a teardown can remove all of it.
        self.graph_mobs = []
        for m in self.mobjects:
            fam = list(m.get_family())
            if m in groups or any(g in fam for g in groups) or m is self.edges:
                self.graph_mobs.append(m)

    def _set_rails(self, head, cap):
        """`swap_rails`, then genuinely remove the outgoing rails.

        swap_rails only fades them; a zero-opacity rail would still be measured by the
        layout QA and would sit on top of the incoming one's geometry.
        """
        old = list(getattr(self, "_rails", []))
        swap_rails(self, head, cap)
        for m in old:
            if m in self.mobjects:
                self.remove(m)

    def _live(self, m):
        """The instance of `m` the scene is actually holding.

        When a submobject is introduced by an animation, manim stages a *different* instance
        than the one the scene code holds: `FadeIn(v[0])` puts a copy on stage, and
        `FadeOut(v[0])` then fades the wrong object, leaving a visible ghost. Anything that
        has to fade or be removed resolves through here first.
        """
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

    def _forget_graphs(self):
        """Remove the graph drawing itself.

        The graph's nodes were staged by their entrance animations (`_live`), so identity
        matching is unreliable; its footprint on the stage is not. Every graph in this film
        is drawn in the upper band, clear of the rails, the containers and the annotation
        band, so clearing that band is exact.
        """
        dead = []
        for m in list(self.mobjects):
            for sub in m.get_family():
                cx, cy = float(sub.get_center()[0]), float(sub.get_center()[1])
                if (-6.0 <= cx <= 6.0) and (-2.75 <= cy <= 2.6):
                    dead.append(m)
                    break
        dead = [m for m in dead if m not in getattr(self, "_rails", [])]
        if dead:
            self.remove(*dead)

    def _clear_region(self, x0, x1, y0, y1):
        """Remove everything whose centre sits inside a rectangle (rails excepted)."""
        rails = {id(m) for m in getattr(self, "_rails", [])}
        dead = []
        for m in list(self.mobjects):
            if id(m) in rails:
                continue
            try:
                cx = float(m.get_center()[0])
                cy = float(m.get_center()[1])
            except Exception:
                continue
            if x0 <= cx <= x1 and y0 <= cy <= y1:
                dead.append(m)
        if dead:
            self._remove_family(dead)

    def _sweep(self):
        """Remove anything left on the stage that has no visible ink.

        FadeOut can leave a zero-opacity ghost in `scene.mobjects`, and the layout QA
        measures geometry regardless of opacity. One sweep per beat keeps the stage honest.
        """
        rails = {id(m) for m in getattr(self, "_rails", [])}
        dead = []
        for m in list(self.mobjects):
            if id(m) in rails:
                continue
            try:
                if float(m.get_fill_opacity()) <= 0.001 and float(m.get_stroke_opacity()) <= 0.001:
                    dead.append(m)
            except Exception:
                continue
        if dead:
            self.remove(*dead)

    def _remove_family(self, mobs):
        """Remove mobjects AND every family member from the stage."""
        every = []
        for m in mobs:
            every += list(m.get_family())
        self.remove(*mobs, *every)

    def _vanish(self, *mobs, run_time: float = 0.4):
        """Fade the given mobjects out, then genuinely remove them — and their families.

        `FadeOut` alone is not enough. It leaves a zero-opacity ghost on the stage, and a
        group's children were each added to the stage in their own right by the animation
        that introduced them, so removing the group alone is not enough either. The layout QA
        measures geometry regardless of opacity, so both have to go.
        """
        self.play(*[FadeOut(self._live(m)) for m in mobs], run_time=run_time)
        self._remove_family([self._live(m) for m in mobs])
        self._sweep()

    # ------------------------------------------------------------------- graph utilities
    def _edge(self, a: str, b: str):
        pair = (a, b) if (a, b) in EDGE_LIST else (b, a)
        return self.edges[EDGE_LIST.index(pair)]

    def _flash(self, a: str, b: str, color=ACCENT):
        return _edge_flash(self._edge(a, b), color)

    def _paint(self, name: str, color, *, opacity: float = 0.30, width: float = 2.6,
               fill: bool = True):
        box = self.node[name][0]
        if fill:
            return box.animate.set_stroke(color, width=width).set_fill(color, opacity=opacity)
        return box.animate.set_stroke(color, width=width)

    def _dist_chip(self, name: str, value):
        """The hop count, parked BESIDE the node so it never sits on the node's own label."""
        box = card(0.36, 0.34, color=WINDOW, fill=PANEL)
        t = Text(str(value), font=MONO, font_size=SMALL_FS, color=WINDOW)
        t.move_to(box.get_center())
        g = VGroup(box, t)
        node = self.node[name]
        side = LEFT if float(node.get_center()[0]) > 0 else RIGHT
        g.next_to(node, side, buff=0.3)
        return g

    def _frontier_rings(self, names, level: float, color=ACCENT):
        """Ring the nodes a fractional frontier sits between — computed, never keyframed."""
        i = min(int(level), len(names) - 1)
        j = min(i + 1, len(names) - 1)
        f = max(0.0, min(1.0, level - i))
        rings = VGroup()
        for k in (i, j):
            ring = Circle(
                radius=RADIUS * (1.45 + 0.55 * f),
                stroke_color=color,
                stroke_width=2.6,
                stroke_opacity=0.4 + 0.55 * f,
            )
            ring.move_to(self.node[names[k]][0].get_center())
            rings.add(ring)
        return rings


    def _vanish(self, *mobs, run_time: float = 0.4):
        """Fade the given mobjects out, then genuinely remove them — and their families.

        `FadeOut` alone is not enough here. It leaves a zero-opacity ghost on the stage
        (`add_mobjects_from_animations` re-adds every animated mobject after the removal
        pass), and a group's children were each added to the stage in their own right by the
        animation that introduced them, so removing the group is not enough either. The
        layout QA measures geometry regardless of opacity, so both have to go.
        """
        fades = [FadeOut(m) for m in mobs]
        self.play(*fades, run_time=run_time)
        every = []
        for m in mobs:
            every += list(m.get_family())
        self.remove(*mobs, *every)

    # ---------------------------------------------------------------------------- beats
    def _beat0(self):
        """Hook: name the trade, then draw the graph the whole film lives on."""
        with self.voiceover(text=BEATS[0]) as tr:
            self._set_rails(headline("Two ways to flood the same graph."),
                       caption("breadth first  ·  depth first"))
            self.play(FadeIn(rule()), run_time=0.3)
            self.play(
                FadeIn(self.edges, run_time=0.5),
                *[FadeIn(n, shift=UP * 0.18) for n in self.nodes],
                lag_ratio=0.16,
                run_time=min(1.8, max(0.9, tr.duration * 0.38)),
            )
            bfs = chip("BFS: rings", color=WINDOW, fs=BODY_FS)
            dfs = chip("DFS: dive", color=ACCENT, fs=BODY_FS)
            VGroup(bfs, dfs).arrange(RIGHT, buff=0.9).move_to([0, -2.55, 0])
            self.play(FadeIn(bfs, shift=UP * 0.2), run_time=0.45)
            self.play(FadeIn(dfs, shift=UP * 0.2), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._restage()
            self._hook = VGroup(bfs, dfs)

    def _beat1(self):
        """Nodes and edges: the vocabulary, in words, before any notation."""
        with self.voiceover(text=BEATS[1]) as tr:
            self._set_rails(headline("A graph is nodes joined by edges."),
                       caption("follow the edges to the next node"))
            self._vanish(self._hook, run_time=0.3)
            n_lab = Text("node", font=MONO, font_size=SMALL_FS, color=PRIMARY)
            n_lab.next_to(self.node["A"], DOWN, buff=0.2)
            e_lab = Text("edge", font=MONO, font_size=SMALL_FS, color=WINDOW)
            e_lab.next_to(self._edge("A", "B").get_center(), LEFT, buff=0.5)
            self.play(FadeIn(n_lab, shift=UP * 0.14), run_time=0.4)
            self.play(FadeIn(e_lab, shift=LEFT * 0.14), run_time=0.4)
            self.play(self._flash("A", "B"), run_time=0.5)
            self.play(self._paint("A", ACCENT), run_time=0.3)
            self.play(self._flash("A", "C", WINDOW), run_time=0.5)
            self.play(self._paint("C", WINDOW), run_time=0.3)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._vocab = VGroup(n_lab, e_lab)

    def _beat2(self):
        """The loop plus the visited mark. Camera zooms the exact node being marked."""
        with self.voiceover(text=BEATS[2]) as tr:
            self._set_rails(headline("Walk the edges, never revisit a node."),
                       caption("mark every node you reach"))
            self._vanish(self._vocab, run_time=0.3)
            self.play(self._paint("A", ACCENT), run_time=0.3)
            self.play(self._paint("B", ACCENT), self._paint("C", ACCENT), run_time=0.4)
            mark = Text("✓", font=MONO, font_size=BODY_FS, color=GOOD)
            mark.next_to(self.node["A"], UP, buff=0.04)
            note = chip("visited check: O(1)", color=GOOD, fs=SMALL_FS)
            note.move_to([0, -2.55, 0])
            self.camera.frame.save_state()  # bare: stores, doesn't animate
            self.play(
                self.camera.auto_zoom([self.node["A"]], margin=8.0),
                FadeIn(mark, scale=0.7),
                run_time=min(1.0, max(0.55, tr.duration * 0.24)),
            )
            self.play(FadeIn(note, shift=UP * 0.14), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.5)))
            self.play(Restore(self.camera.frame), run_time=0.5)
            self.play(*[self._paint(n, PRIMARY, opacity=0.0, width=2.2) for n in NAMES],
                      run_time=0.35)
            self.wait(max(0.05, tr.get_remaining_duration(buff=0.2)))
            self._loop = VGroup(mark, note)

    def _beat3(self):
        """The container choice, drawn as two real containers."""
        with self.voiceover(text=BEATS[3]) as tr:
            self._set_rails(headline("The container picks the algorithm."),
                       caption("queue → BFS   ·   stack → DFS"))
            self._vanish(self._loop, run_time=0.3)
            self.play(self.g.animate.scale(0.72).move_to([-3.3, 0.5, 0]), run_time=0.7)
            self._board = _Board((1.75, 0.6, 0), (5.7, 0.6, 0))
            self.play(FadeIn(self._board.group()), run_time=0.5)
            self.play(Indicate(self._board.q_box, color=WINDOW, scale_factor=1.06),
                      run_time=0.5)
            fill = Text("holds what you found, not what you've explored", font=MONO,
                        font_size=SMALL_FS, color=MUTED)
            fill.move_to([-2.2, -2.7, 0])
            self.play(FadeIn(fill, shift=UP * 0.12), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._board_note = fill

    def _beat4(self):
        """The one difference that matters: which of the two you take next."""
        with self.voiceover(text=BEATS[4]) as tr:
            self._set_rails(headline("Same neighbours, opposite order."),
                       caption("queue takes oldest  ·  stack newest"))
            self._vanish(self._board_note, run_time=0.25)
            self.play(self._flash("A", "B"), self._flash("A", "C", WINDOW), run_time=0.5)
            self.play(
                self._paint("B", WINDOW),
                self._paint("C", ACCENT),
                run_time=0.4,
            )
            self.play(
                *self._board.q.reveal(0, "B", color=WINDOW),
                *self._board.s.reveal(0, "C", color=ACCENT),
                run_time=0.5,
            )
            pop = Text("pop B  vs  pop C", font=MONO, font_size=BODY_FS, color=INK)
            pop.move_to([-2.2, -2.7, 0])
            self.play(FadeIn(pop, shift=UP * 0.12), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._pop = pop

    def _beat5(self):
        """BFS: one ring per round, with a computed frontier ring tracking the sweep."""
        with self.voiceover(text=BEATS[5]) as tr:
            self._set_rails(headline("Breadth first fills one ring at a time."),
                       caption("distance two before distance three"))
            self._vanish(self._pop, run_time=0.25)
            self._clear_region(0.4, 6.8, -2.0, 2.0)
            self.play(self.g.animate.shift(LEFT * 3.2).shift(DOWN * 0.7), run_time=0.7)
            q_box = card(1.7, 0.85, color=STROKE, fill=PANEL)
            q_box.move_to([4.15, 0.5, 0])
            self.play(FadeIn(q_box), run_time=0.35)
            self._q_box = q_box
            self._q_found = []
            self._q_row = None
            seq = ["A", "B", "C", "D", "E"]
            rounds = [
                ([("A", "B"), ("A", "C")], ["B", "C"]),
                ([("B", "D"), ("B", "E")], ["D", "E"]),
            ]
            tracker = ValueTracker(0.0)
            wave = always_redraw(
                lambda: self._frontier_rings(seq, tracker.get_value(), WINDOW)
            )
            self.add(wave)
            slot = 0
            for eps, targets in rounds:
                self.play(*[self._flash(a, b, WINDOW) for a, b in eps], run_time=0.5)
                for n in targets:
                    self.play(self._paint(n, WINDOW), run_time=0.28)
                    self._q_found.append(n)
                    row = _tokens(self._q_found, axis="h", color=WINDOW)
                    if len(self._q_found) > 4:
                        row = _tokens(self._q_found[-4:], axis="h", color=WINDOW)
                    row.move_to([4.15, 0.5, 0])
                    if getattr(self, "_q_row", None) is None:
                        self.play(FadeIn(row), run_time=0.3)
                    else:
                        self.play(ReplacementTransform(self._q_row, row), run_time=0.26)
                    self._q_row = row
                    slot += 1
                self.play(tracker.animate.set_value(float(slot - 1)), run_time=0.42)
            ring_note = Text("one ring per round", font=MONO, font_size=SMALL_FS, color=WINDOW)
            ring_note.move_to([4.15, -0.4, 0])
            self.play(FadeIn(ring_note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._bfs = VGroup(wave, ring_note)

    def _beat6(self):
        """DFS: push neighbours, dive, hit a dead end, backtrack."""
        with self.voiceover(text=BEATS[6]) as tr:
            self._set_rails(headline("Depth first dives, then backtracks."),
                       caption("push neighbours, pop the newest"))
            self._vanish(self._bfs, run_time=0.25)
            # The queue's stage copies cannot be matched after its move animation, so the
            # whole container lane is cleared by position, then the containers are re-placed.
            self.play(self.g.animate.shift(RIGHT * 3.2).shift(UP * 0.7), run_time=0.6)
            # both frontiers stay on stage: the queue BFS built, and the stack DFS is using
            self.play(self._q_box.animate.scale(0.85).move_to([3.7, -1.45, 0]),
                      self._q_row.animate.scale(0.85).move_to([3.7, -1.45, 0]), run_time=0.5)
            qlabel = Text("queue", font=MONO, font_size=SMALL_FS, color=WINDOW)
            qlabel.next_to(self._q_row, DOWN, buff=0.24)
            self.play(FadeIn(qlabel), run_time=0.45)
            self._queue_row = VGroup(self._q_box, self._q_row, qlabel)
            s_box = card(1.7, 2.3, color=STROKE, fill=PANEL)
            s_box.move_to([5.75, 0.5, 0])
            s_label = Text("stack", font=MONO, font_size=SMALL_FS, color=ACCENT)
            s_label.next_to(s_box, DOWN, buff=0.3)
            self.play(FadeIn(s_box), FadeIn(s_label), run_time=0.5)
            self._stack_box = VGroup(s_box, s_label)
            dive = [("A", "B"), ("B", "E"), ("E", "I"), ("C", "F"), ("F", "G")]
            # The stack is rebuilt in place at every step: pushing i, e, f, g pops a, b, e, i,
            # which is exactly what "dive then backtrack" looks like if you watch the stack.
            states = [
                ["A"],
                ["A", "B"],
                ["A", "B", "E"],
                ["A", "B", "E", "I"],
                ["B", "E", "I", "F"],
                ["E", "I", "F", "G"],
            ]
            stack = None
            for i, (a, b) in enumerate(dive):
                self.play(self._flash(a, b), run_time=0.3)
                self.play(self._paint(b, ACCENT), run_time=0.22)
                new = _tokens(states[i + 1], axis="v", color=ACCENT, fs=14)
                new.move_to(self._stack_box[0].get_center())
                if stack is None:
                    self.play(FadeIn(new), run_time=0.3)
                else:
                    self.play(ReplacementTransform(stack, new), run_time=0.34)
                stack = new
            self._stack_mob = stack
            back = Text("dead end  →  backtrack", font=MONO, font_size=SMALL_FS, color=GONE)
            back.move_to([-4.5, -2.45, 0])
            self.play(FadeIn(back, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._dfs = back

    def _beat7(self):
        """Why ring order means shortest paths — stated cold, rings still live."""
        with self.voiceover(text=BEATS[7]) as tr:
            self._set_rails(headline("First arrival is the fewest edges."),
                       caption("BFS gives the fewest steps"))
            self._vanish(self._dfs, run_time=0.35)
            self._clear_region(0.4, 6.8, -2.0, 2.4)
            dists = VGroup()
            for name, d in (("A", 0), ("B", 1), ("C", 1), ("D", 2), ("E", 2), ("F", 3)):
                dists.add(self._dist_chip(name, d))
            self.camera.frame.save_state()  # bare: stores, doesn't animate
            self.play(
                self.camera.auto_zoom([self.node["B"]], margin=8.0),
                *[FadeIn(d, shift=UP * 0.12) for d in dists],
                lag_ratio=0.22,
                run_time=min(1.6, max(0.8, tr.duration * 0.34)),
            )
            ok = Text("first touch = shortest", font=MONO, font_size=SMALL_FS, color=GOOD)
            ok.move_to([4.15, -1.5, 0])
            self.play(FadeIn(ok, scale=0.94), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self.play(Restore(self.camera.frame), run_time=0.5)
            self.wait(max(0.05, tr.get_remaining_duration(buff=0.2)))
            self._dist = VGroup(dists, ok)

    def _beat8(self):
        """Components: one search, one component — count the restarts."""
        with self.voiceover(text=BEATS[8]) as tr:
            self._set_rails(headline("One search explores one component."),
                       caption("count the restarts"))
            self._vanish(self._dist, self._board.q_box,
                         self._board.q.tokens_group, self._board.q_label, run_time=0.4)
            self._forget_graphs()
            coords = {"1": [-5.4, 0.9], "2": [-4.0, 0.9], "3": [-4.7, -0.3], "4": [-3.9, -1.4],
                      "5": [1.6, 0.4], "6": [3.2, 0.4]}
            comp = graph_viz(coords, [("1", "2"), ("1", "3"), ("2", "3"), ("3", "4")],
                             radius=0.34, color=PRIMARY)
            l1 = Text("component 1", font=MONO, font_size=SMALL_FS, color=WINDOW)
            l1.move_to([-4.65, 1.85, 0])
            l2 = Text("component 2", font=MONO, font_size=SMALL_FS, color=WINDOW)
            l2.move_to([2.4, 1.85, 0])
            note = Text("Number of Islands = the number of DFS calls", font=MONO,
                        font_size=SMALL_FS, color=MUTED)
            note.move_to([0, -2.5, 0])
            self.play(FadeIn(comp), run_time=0.5)
            for i in range(4):
                self.play(comp[1][i][0].animate.set_stroke(WINDOW, width=2.6)
                          .set_fill(WINDOW, opacity=0.3), run_time=0.22)
            self.play(FadeIn(l1, shift=UP * 0.12), run_time=0.35)
            for i in range(4, 6):
                self.play(comp[1][i][0].animate.set_stroke(GOOD, width=2.6)
                          .set_fill(GOOD, opacity=0.3), run_time=0.22)
            self.play(FadeIn(l2, shift=UP * 0.12), run_time=0.35)
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._comp = VGroup(comp, l1, l2, note)

    def _beat9(self):
        """Kahn's: repeatedly peel the nodes with no unmet prerequisite."""
        with self.voiceover(text=BEATS[9]) as tr:
            self._set_rails(headline("Peel whatever has no dependency left."),
                       caption("a short order means a cycle"))
            self._vanish(self._comp, run_time=0.35)
            self._forget_graphs()
            coords = {"A": [-5.0, 1.4], "B": [-2.0, 0.7], "C": [1.0, 1.4], "D": [2.6, -0.7],
                      "E": [0.0, -1.9]}
            order_names = ["A", "B", "C", "D", "E"]
            dag = graph_viz(coords, [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"),
                                     ("D", "E")],
                            radius=0.34, color=PRIMARY, directed=True)
            indeg = {"A": 0, "B": 1, "C": 1, "D": 2, "E": 1}
            self.play(FadeIn(dag), run_time=0.5)
            marks = VGroup()
            for name in order_names:
                box = card(0.46, 0.42, color=WINDOW, fill=PANEL)
                t = Text(str(indeg[name]), font=MONO, font_size=SMALL_FS, color=WINDOW)
                t.move_to(box.get_center())
                g = VGroup(box, t)
                g.next_to(dag[1][order_names.index(name)], UP, buff=0.12)
                marks.add(g)
            lab = Text("in-degree", font=MONO, font_size=SMALL_FS, color=MUTED)
            lab.next_to(marks[0], LEFT, buff=0.16)
            self.play(*[FadeIn(m, shift=UP * 0.1) for m in marks], FadeIn(lab),
                      lag_ratio=0.28, run_time=min(1.5, max(0.7, tr.duration * 0.3)))
            for i, name in enumerate(order_names):
                self.play(marks[i].animate.set_opacity(0.16),
                          dag[1][i][0].animate.set_stroke(GOOD, width=2.6)
                          .set_fill(GOOD, opacity=0.3),
                          run_time=0.3)
            order = Text("order:  A · B · C · D · E", font=MONO, font_size=SMALL_FS,
                         color=GOOD)
            order.move_to([-3.0, -2.6, 0])
            self.play(FadeIn(order, shift=UP * 0.12), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._topo = VGroup(dag, marks, lab, order)

    def _beat10(self):
        """Dijkstra: a heap instead of a queue, picking the cheapest node first."""
        with self.voiceover(text=BEATS[10]) as tr:
            self._set_rails(headline("Weights? A heap picks the cheapest node."),
                       caption("Dijkstra = BFS with a priority queue"))
            self._vanish(self._topo, run_time=0.35)
            self._forget_graphs()
            coords = {"A": [-4.4, 1.2], "B": [-1.2, 1.9], "C": [-1.2, -0.5],
                      "D": [1.8, 0.9], "E": [4.2, -0.1]}
            wedges = [("A", "B", 2), ("A", "C", 5), ("B", "C", 1), ("B", "D", 4),
                      ("C", "D", 2), ("D", "E", 3)]
            wg = graph_viz(coords, [(u, v) for u, v, _ in wedges], radius=0.34,
                           color=PRIMARY, directed=True)
            self.play(FadeIn(wg), run_time=0.5)
            labels = VGroup()
            for u, v, w in wedges:
                lb = Text(str(w), font=MONO, font_size=SMALL_FS, color=WINDOW)
                mid = (wg[1][list(coords).index(u)].get_center()
                       + wg[1][list(coords).index(v)].get_center()) / 2
                lb.move_to(mid)
                lb.shift(UP * 0.2 if u == "A" and v in ("B", "C") else UP * 0.0)
                labels.add(lb)
            self.play(*[FadeIn(l, scale=0.9) for l in labels], lag_ratio=0.18,
                      run_time=min(1.2, max(0.6, tr.duration * 0.26)))
            heap = chip("heap: (cost, node)", color=ACCENT, fs=SMALL_FS)
            heap.move_to([0, -2.6, 0])
            self.play(FadeIn(heap, shift=UP * 0.12), run_time=0.45)
            self.play(Circumscribe(wg[1][0], color=ACCENT, fade_out=True), run_time=0.7)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._dij = VGroup(wg, labels, heap)

    def _beat11(self):
        """The two one-line variants the card says to know cold."""
        with self.voiceover(text=BEATS[11]) as tr:
            self._set_rails(headline("Two one-line changes change the problem."),
                       caption("max(d, w)   ·   heap key = w"))
            self._vanish(self._dij, run_time=0.35)
            self._forget_graphs()
            eff = VGroup(
                Text("the path costs its worst edge", font=MONO, font_size=BODY_FS,
                     color=ACCENT),
                Text("nd = max(d, w)  →  min effort, swim", font=MONO, font_size=SMALL_FS,
                     color=INK),
            ).arrange(DOWN, buff=0.22)
            prim = VGroup(
                Text("cheapest way INTO the tree", font=MONO, font_size=BODY_FS, color=WINDOW),
                Text("heap key = the edge weight w", font=MONO, font_size=SMALL_FS, color=INK),
            ).arrange(DOWN, buff=0.22)
            box_a = card(eff.width + 0.9, eff.height + 0.7, color=ACCENT, fill=PANEL)
            box_b = card(prim.width + 0.9, prim.height + 0.7, color=WINDOW, fill=PANEL)
            VGroup(box_a, box_b).arrange(DOWN, buff=0.5).move_to(stage_center(-0.1))
            eff.move_to(box_a.get_center())
            prim.move_to(box_b.get_center())
            self.play(FadeIn(box_a), run_time=0.35)
            self.play(Write(eff[0]), run_time=0.5)
            self.play(FadeIn(eff[1]), run_time=0.4)
            self.play(FadeIn(box_b), run_time=0.35)
            self.play(Write(prim[0]), run_time=0.5)
            self.play(FadeIn(prim[1]), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._variants = VGroup(box_a, eff, box_b, prim)

    def _beat12(self):
        """What goes wrong #1: marking visited at pop instead of at push."""
        with self.voiceover(text=BEATS[12]) as tr:
            self._set_rails(headline("Mark at push, not at pop."),
                       caption("or the frontier and levels swell"))
            self._vanish(self._variants, run_time=0.35)
            head = Text("queue with C in it twice:", font=MONO, font_size=BODY_FS, color=GONE)
            queue = Text("[ C  B  C  E ]", font=MONO, font_size=BODY_FS, color=GONE)
            tail = Text("on a grid, each cell can enter four times", font=MONO,
                        font_size=SMALL_FS, color=MUTED)
            VGroup(head, queue, tail).arrange(DOWN, buff=0.32).move_to(stage_center(0.1))
            self.play(FadeIn(head), run_time=0.4)
            self.play(Write(queue), run_time=0.5)
            self.play(Indicate(queue, color=GONE, scale_factor=1.08), run_time=0.6)
            self.play(FadeIn(tail, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._wrong1 = VGroup(head, queue, tail)

    def _beat13(self):
        """What goes wrong #2: the parent check, and why directed needs colour."""
        with self.voiceover(text=BEATS[13]) as tr:
            self._set_rails(headline("Cycles need more than 'already seen'."),
                       caption("undirected: parent  ·  directed: on-path"))
            self._vanish(self._wrong1, run_time=0.35)
            coords = {"U": [-5.8, 1.05], "V": [-3.2, 1.05], "W": [-0.6, 1.05],
                      "A": [-5.8, -1.0], "B": [-3.2, -1.0], "C": [-0.6, -1.0]}
            ug = graph_viz(coords, [("U", "V"), ("V", "W")], radius=0.3, color=PRIMARY)
            dg = graph_viz(coords, [("A", "B"), ("B", "C"), ("A", "C")], radius=0.3,
                           color=PRIMARY, directed=True)
            parent = Text("v != parent", font=MONO, font_size=SMALL_FS, color=ACCENT)
            parent.move_to([1.9, 1.05, 0])
            gray = Text("GRAY = still on this path", font=MONO, font_size=SMALL_FS,
                        color=WINDOW)
            gray.move_to([2.1, -1.0, 0])
            note = Text("A → B, A → C, B → C: C is reached twice, and is not a cycle",
                        font=MONO, font_size=SMALL_FS, color=MUTED)
            note.move_to([0, -2.45, 0])
            self.play(FadeIn(ug), FadeIn(dg), run_time=0.45)
            self.play(FadeIn(parent, shift=UP * 0.12), run_time=0.35)
            self.play(FadeIn(gray, shift=UP * 0.12), run_time=0.35)
            self.play(dg[1][0][0].animate.set_stroke(WINDOW, width=2.6),
                      dg[1][1][0].animate.set_stroke(WINDOW, width=2.6), run_time=0.4)
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._wrong2 = VGroup(ug, dg, parent, gray, note)

    def _beat14(self):
        """What goes wrong #3: Bellman-Ford reading this round's own writes."""
        with self.voiceover(text=BEATS[14]) as tr:
            self._set_rails(headline("Bellman-Ford: copy the distances."),
                       caption("one round = at most one more edge"))
            self._vanish(self._wrong2, run_time=0.35)
            bad = VGroup(
                Text("dist[v] = min(dist[v], dist[u]+w)", font=MONO, font_size=BODY_FS,
                     color=GONE),
                Text("one path jumps many edges this round", font=MONO, font_size=SMALL_FS,
                     color=MUTED),
            ).arrange(DOWN, buff=0.24)
            good = VGroup(
                Text("prev = dist[:]", font=MONO, font_size=BODY_FS, color=GOOD),
                Text("relax from the snapshot of last round", font=MONO, font_size=SMALL_FS,
                     color=INK),
            ).arrange(DOWN, buff=0.24)
            VGroup(bad, good).arrange(DOWN, buff=0.95).move_to(stage_center(-0.2))
            self.play(FadeIn(bad[0], shift=UP * 0.14), run_time=0.45)
            self.play(FadeIn(bad[1]), run_time=0.35)
            self.play(FadeIn(good[0], shift=UP * 0.14), run_time=0.45)
            self.play(FadeIn(good[1]), run_time=0.35)
            feet = Text("K stops = K + 1 rounds", font=MONO, font_size=SMALL_FS, color=GOOD)
            feet.move_to([0, -2.6, 0])
            self.play(FadeIn(feet, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._wrong3 = VGroup(bad, good, feet)

    def _beat15(self):
        """Recognition: the graph is in the shape, not the wording."""
        with self.voiceover(text=BEATS[15]) as tr:
            self._set_rails(headline("The word 'graph' is rarely in the problem."),
                       caption("recognise the shape, not the word"))
            self._vanish(self._wrong3, run_time=0.35)
            cells = VGroup()
            for r in range(3):
                for c in range(4):
                    box = card(0.5, 0.5, color=PRIMARY, fill=PANEL)
                    box.move_to([-4.7 + c * 0.56, 1.15 - r * 0.56, 0])
                    cells.add(box)
            wires = VGroup()
            for r in range(3):
                for c in range(3):
                    wires.add(Line(cells[r * 4 + c].get_right(),
                                   cells[r * 4 + c + 1].get_left(),
                                   color=STROKE, stroke_width=2))
            for r in range(2):
                for c in range(4):
                    wires.add(Line(cells[r * 4 + c].get_bottom(),
                                   cells[(r + 1) * 4 + c].get_top(),
                                   color=STROKE, stroke_width=2))
            grid = VGroup(wires, cells)
            gl = Text("cells are nodes", font=MONO, font_size=SMALL_FS, color=MUTED)
            gl.next_to(grid, DOWN, buff=0.3)
            rows = VGroup(
                Text("grid + connected / island", font=MONO, font_size=SMALL_FS, color=GOOD),
                Text("fewest steps, unweighted", font=MONO, font_size=SMALL_FS, color=GOOD),
                Text("prerequisites / ordering", font=MONO, font_size=SMALL_FS, color=GOOD),
                Text("neighbours generated on the fly", font=MONO, font_size=SMALL_FS,
                     color=GOOD),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.62)
            rows.move_to([3.0, 0.45, 0])
            self.play(FadeIn(grid), FadeIn(gl), run_time=0.55)
            self.play(*[FadeIn(t, shift=RIGHT * 0.18) for t in rows], lag_ratio=0.32,
                      run_time=min(1.6, max(0.8, tr.duration * 0.36)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._recog = VGroup(grid, gl, rows)

    def _beat16(self):
        """The anti-signals: a TreeNode input, and equal weights."""
        with self.voiceover(text=BEATS[16]) as tr:
            self._set_rails(headline("Two things that are not this."),
                       caption("a tree  ·  equal weights"))
            self._vanish(self._recog, run_time=0.35)
            tree = VGroup(
                Text("✗  TreeNode input: one parent", font=MONO,
                     font_size=BODY_FS, color=GONE),
                Text("     so visited is unnecessary", font=MONO, font_size=SMALL_FS,
                     color=MUTED),
            ).arrange(DOWN, buff=0.2)
            flat = VGroup(
                Text("✗  every edge costs the same", font=MONO, font_size=BODY_FS, color=GONE),
                Text("     plain BFS already gives the shortest", font=MONO,
                     font_size=SMALL_FS, color=MUTED),
            ).arrange(DOWN, buff=0.2)
            VGroup(tree, flat).arrange(DOWN, buff=1.0).move_to(stage_center(-0.15))
            self.play(FadeIn(tree[0], shift=UP * 0.14), run_time=0.45)
            self.play(FadeIn(tree[1]), run_time=0.35)
            self.play(FadeIn(flat[0], shift=UP * 0.14), run_time=0.45)
            self.play(FadeIn(flat[1]), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._anti = VGroup(tree, flat)

    def _beat17(self):
        """Complexity, stated cold."""
        with self.voiceover(text=BEATS[17]) as tr:
            self._set_rails(headline("Every node once, every edge once."),
                       caption("O(V + E) time  ·  O(V) space"))
            self._vanish(self._anti, run_time=0.35)
            rows = [
                ("DFS / BFS, adjacency list", "O(V + E)", "O(V)", GOOD),
                ("DFS / BFS on a grid", "O(R·C)", "O(R·C)", GOOD),
                ("Kahn's, bipartite", "O(V + E)", "O(V)", GOOD),
                ("Dijkstra / Prim, binary heap", "O((V+E) log V)", "O(V + E)", WINDOW),
                ("Bellman-Ford", "O(V·E)", "O(V)", WINDOW),
            ]
            table = VGroup()
            for name, tm, sp, col in rows:
                table.add(VGroup(
                    Text(name, font=MONO, font_size=SMALL_FS, color=INK),
                    Text(tm, font=MONO, font_size=SMALL_FS, color=col),
                    Text(sp, font=MONO, font_size=SMALL_FS, color=MUTED),
                ).arrange(RIGHT, buff=0.5))
            table.arrange(DOWN, aligned_edge=LEFT, buff=0.26)
            if table.width > 12.4:
                table.scale_to_fit_width(12.4)
            table.move_to(stage_center(-0.15))
            self.play(*[FadeIn(r, shift=RIGHT * 0.15) for r in table], lag_ratio=0.28,
                      run_time=min(1.7, max(0.9, tr.duration * 0.38)))
            warn = Text("recursive DFS past ~10⁴ nodes: go iterative", font=MONO,
                        font_size=SMALL_FS, color=GONE)
            warn.move_to([0, -2.65, 0])
            self.play(FadeIn(warn, shift=UP * 0.12), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._complex = VGroup(table, warn)

    def _beat18(self):
        """Recall card: one line the viewer leaves with."""
        with self.voiceover(text=BEATS[18]) as tr:
            self._set_rails(headline("Same loop. Different container."),
                       caption("stack · queue · heap"))
            self._vanish(self._complex, run_time=0.3)
            box = card(9.6, 2.0, color=ACCENT, fill=PANEL)
            box.move_to(stage_center(-0.05))
            top = Text("Graphs", font=MONO, font_size=32, color=ACCENT)
            mid = Text("stack → DFS   ·   queue → BFS   ·   heap → Dijkstra",
                       font=MONO, font_size=SMALL_FS, color=INK)
            sub = Text("O(V + E)  ·  visited is non-negotiable", font=MONO,
                       font_size=SMALL_FS, color=MUTED)
            VGroup(top, mid, sub).arrange(DOWN, buff=0.26).move_to(box.get_center())
            self.play(FadeIn(box, scale=0.96), run_time=0.45)
            self.play(Write(top), run_time=0.5)
            self.play(FadeIn(mid), run_time=0.4)
            self.play(FadeIn(sub), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
