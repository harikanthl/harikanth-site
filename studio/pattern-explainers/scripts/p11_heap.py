"""
Pattern 11 — Heap.

The film follows the card's own argument: the one question a heap answers fast -> the
waiting-room intuition -> the single promise (every parent <= its children) -> the
array-as-tree duality, with the index arithmetic laid bare -> sift up on push -> sift down
on pop -> O(1) peek -> complexity -> the five shapes (top-k, k-way merge, greedy,
retroactive greedy, two-heap median) -> the two-heap invariant and the median readout ->
what breaks it -> the recall card.

The tree and the array are on screen together and move together: a swap the algorithm
performs in the tree is performed, at the same instant, on the same indices in the array,
so the duality is something you watch rather than something you are told.

Animation safety note: ArrayRow keeps its labels nested inside its cell groups, so this
scene only ever uses `.animate.<method>()` on them (never FadeIn/FadeOut), and fades whole
top-level groups instead. That is what keeps values from ghosting on screen.

Narration lives in BEATS and every animation is timed against `tracker.duration`, so the
picture and the voice cannot drift: one file is the source of truth for both.
"""

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    Circumscribe,
    Dot,
    FadeIn,
    FadeOut,
    GrowArrow,
    Indicate,
    Line,
    MathTex,
    Restore,
    Text,
    VGroup,
    Write,
)

from house import (
    ACCENT,
    BODY_FS,
    FONT,
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

PATTERN_SLUG = "heap"
TITLE = "Heap"
SUMMARY = "A loose ordering that keeps the extreme at the top, in O(log n) per change."
SCENE_CLASS = "Heap"
POSTER_AT = 34.0

# A six-element min-heap plus one deliberately free slot — the "next" position a push uses.
HEAP_VALUES = [1, 3, 2, 7, 4, 9, None]
FREE = 6

BEATS = [
    # 0 hook
    "A heap answers one question fast: what is the smallest thing right now?",
    # 1 the one-sentence version
    "It gives the current extreme in constant time, and survives changes in log n.",
    # 2 ELI5
    "A waiting room never sorts everyone. It only needs to know who's most urgent.",
    # 3 the promise
    "A heap promises one thing: every parent is no larger than its children.",
    # 4 the promise is loose
    "Look: three and two are siblings, out of order. That's allowed.",
    # 5 array as tree
    "And here's the trick. That tree is really an array, filled level by level.",
    # 6 index arithmetic
    "The parent of i sits at i minus one, halved. Its children sit at two i plus one and two i plus two.",
    # 7 sift up
    "To insert, put the value at the end and let it climb: if it beats its parent, swap up. That's sift up.",
    # 8 sift up cost
    "Each swap halves the distance to the root, so an insert costs log n.",
    # 9 pop
    "To remove the top, move the last element to the root, shrink, then let it sink.",
    # 10 sift down
    "Compare it with both children, swap with the smaller, and repeat.",
    # 11 peek
    "The minimum is always index zero. That's the constant time peek.",
    # 12 complexity
    "Peek is constant, push and pop are log n, and heapify builds the array in linear time.",
    # 13 shape A
    "Shape one: top k. Keep a heap of only k items and evict the weakest survivor.",
    # 14 the counter-intuitive line
    "For the k largest you keep a min heap, because the thing you discard is your weakest keeper.",
    # 15 cost of top k
    "The heap never holds more than k, so each step costs log k, not log n.",
    # 16 shape C
    "Shape three: merge k sorted lists. One head per list. Pop the smallest, push its successor.",
    # 17 shape D
    "Shape four: greedy. Pop the best, take a step, push the remainder back.",
    # 18 retroactive greedy
    "The deep one: the heap decides retroactively. Run dry, then refuel at the best station you passed.",
    # 19 shape E
    "Shape five: the running median, with two heaps, a low half and a high half.",
    # 20 the invariant
    "Everything in low is at most everything in high, and sizes differ by at most one.",
    # 21 the readout
    "So the median is the top of low, or the average of both tops.",
    # 22 what breaks it
    "What breaks it: needing the full order, or a lookup by key. That's a sort or a hash map.",
    # 23 recall
    "Need the extreme of a changing set? That's a heap.",
]

CHAPTERS = {
    0: "The hook",
    2: "The waiting room",
    3: "The one promise",
    5: "Tree is an array",
    6: "Index arithmetic",
    7: "Sift up",
    9: "Sift down",
    11: "Peek",
    12: "Complexity",
    13: "Shape A: top k",
    16: "Shape C: k-way merge",
    17: "Shape D: greedy",
    19: "Shape E: two heaps",
    22: "What breaks it",
    23: "Recall",
}


class Heap(PrebakedVoiceMovingCameraScene):
    # ---------------------------------------------------------------------------- setup
    def construct(self):
        bg(self)
        self.tree = TreeViz(3, radius=0.28, v_gap=0.95, label_fs=SMALL_FS)
        self.tree.group.shift(UP * 1.55)
        self.node_pos = [n.get_center() for n in self.tree.nodes]
        self.tvals = []  # one value label per tree node (None == the free slot)
        for v in HEAP_VALUES:
            i = len(self.tvals)
            self.tvals.append(None if v is None else self._node_text(v, INK, i))
        self.row = ArrayRow(HEAP_VALUES, cell=0.66, fs=24, index_fs=SMALL_FS)
        self.row.group.move_to([0, -1.45, 0])
        self.avalues = list(HEAP_VALUES)  # the array's values, tracked so rewrites stay true
        self.col_top = 1.05
        self.col_gap = 0.66
        self.low_x, self.high_x = -2.45, 2.45
        for i in range(len(BEATS)):
            getattr(self, f"_beat{i}")()

    # --------------------------------------------------------------------- animation
    def _set_cell(self, row, i: int, value, color=INK, fs: int = 24):
        """Write a value into a cell, nested-safe.

        `ArrayRow.set_value` in shots.py calls `VGroup.replace(old, new)`, which passes the
        new text where manim expects `dim_to_match`, so it raises as soon as the cell is not
        empty. This is the same operation done correctly, and it never touches scene lists.
        """
        box = row.boxes[i]
        new = Text(str(value), font=MONO, font_size=fs, color=color)
        if new.width > box.width - 0.12:
            new.scale_to_fit_width(box.width - 0.12)
        if new.height > box.height - 0.12:
            new.scale_to_fit_height(box.height - 0.12)
        new.move_to(box.get_center())
        old = row.texts[i]
        row.texts[i] = new
        if old is None:
            row.cells[i].add(new)
        else:
            row.cells[i].remove(old)
            row.cells[i].add(new)
        return new

    def _reveal(self, mob, *, rt: float = 0.4):
        """Fade a (possibly deeply nested) mobject in without touching the scene list."""
        mob.set_opacity(0.0)
        self.play(mob.animate.set_opacity(1.0), run_time=rt)

    def _hide(self, mob, *, rt: float = 0.35):
        self.play(mob.animate.set_opacity(0.0), run_time=rt)

    def _out(self, mob):
        """Animation: fade a nested label out (opacity only — scene-list safe)."""
        mob.set_opacity(1.0)
        return mob.animate.set_opacity(0.0)

    def _array_write(self, i: int, value, color=INK, *, rt: float = 0.45):
        """Rewrite one array cell in place, fading the old glyph out first.

        An ArrayRow label may NOT be moved to another cell: each cell box is filled
        opaque and drawn in row order, so a label that travels into a later cell is
        painted over, and manim's nested-mobject transform lands it at the wrong x.
        Rewriting the value where it lives keeps the array honest at every frame.
        """
        old = self.row.texts[i]
        if old is not None:
            self.play(self._out(old), run_time=rt * 0.4)
        new = self._set_cell(self.row, i, value, color=color)
        new.set_opacity(0.0)
        self.play(new.animate.set_opacity(1.0), run_time=rt * 0.6)
        self.avalues[i] = value
        return new

    # ------------------------------------------------------------------------- layout
    def _node_text(self, value, color=INK, i: int = 0) -> Text:
        t = Text(str(value), font=MONO, font_size=SMALL_FS, color=color)
        t.move_to(self.tree.nodes[i].get_center())
        return t

    def _tint(self, i: int, color=ACCENT, opacity: float = 0.28):
        return self.tree.nodes[i].animate.set_stroke(color, width=2.8).set_fill(
            color, opacity=opacity
        )

    def _swap(self, i: int, j: int, *, rt: float = 0.55):
        """The algorithm's own swap: the tree labels travel, the array rewrites in place."""
        self.play(
            self.tvals[i].animate.move_to(self.node_pos[j]),
            self.tvals[j].animate.move_to(self.node_pos[i]),
            *self.row.focus(i, color=ACCENT, fill_opacity=0.24),
            *self.row.focus(j, color=ACCENT, fill_opacity=0.24),
            run_time=rt,
        )
        self.tvals[i], self.tvals[j] = self.tvals[j], self.tvals[i]
        vi, vj = self.avalues[i], self.avalues[j]
        old_i, old_j = self.row.texts[i], self.row.texts[j]
        self.play(self._out(old_i), self._out(old_j), run_time=rt * 0.25)
        new_i = self._set_cell(self.row, i, vj, color=INK)
        new_j = self._set_cell(self.row, j, vi, color=INK)
        new_i.set_opacity(0.0)
        new_j.set_opacity(0.0)
        # Only ONE animation may touch each mobject here: a second (colour) animation would
        # interpolate from a snapshot taken at opacity 0 and leave the value invisible.
        self.play(
            new_i.animate.set_opacity(1.0),
            new_j.animate.set_opacity(1.0),
            self.row.boxes[i].animate.set_stroke(STROKE, width=1.6).set_fill(PANEL, opacity=1.0),
            self.row.boxes[j].animate.set_stroke(STROKE, width=1.6).set_fill(PANEL, opacity=1.0),
            run_time=rt * 0.4,
        )
        self.avalues[i], self.avalues[j] = vj, vi

    def _column(self, x: float, title: str, color, n: int = 3):
        boxes = VGroup()
        for i in range(n):
            b = card(1.06, 0.56, color=STROKE, fill=PANEL)
            b.move_to([x, self.col_top - i * self.col_gap, 0])
            boxes.add(b)
        ttl = Text(title, font=MONO, font_size=SMALL_FS, color=color)
        ttl.next_to(boxes[0], UP, buff=0.24)
        return boxes, ttl

    # ---------------------------------------------------------------------------- beats
    def _beat0(self):
        """Hook: one fast question, and what each structure charges for it."""
        with self.voiceover(text=BEATS[0]) as tr:
            swap_rails(self, headline("A heap answers one question fast."),
                       caption("what is the smallest right now?"))
            self.play(FadeIn(rule()), run_time=0.3)
            q = chip("min  ?", color=ACCENT, fs=BODY_FS).move_to(stage_center(1.05))
            slow = chip("sorted list:  O(n) to insert", color=GONE, fs=BODY_FS)
            fast = chip("heap:  O(log n) to insert", color=GOOD, fs=BODY_FS)
            costs = VGroup(slow, fast).arrange(DOWN, buff=0.5).move_to(stage_center(-0.9))
            self.play(FadeIn(q, scale=0.9), run_time=0.5)
            self.play(FadeIn(slow, shift=UP * 0.2), run_time=0.45)
            self.play(FadeIn(fast, shift=UP * 0.2), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._hook = VGroup(q, costs)

    def _beat1(self):
        """The one-sentence version: the three costs, as objects."""
        with self.voiceover(text=BEATS[1]) as tr:
            swap_rails(self, headline("The extreme in O(1); changes in O(log n)."),
                       caption("peek, push, pop"))
            self.play(FadeOut(self._hook, run_time=0.3))
            items = VGroup(
                chip("peek  O(1)", color=GOOD, fs=BODY_FS),
                chip("push  O(log n)", color=PRIMARY, fs=BODY_FS),
                chip("pop   O(log n)", color=PRIMARY, fs=BODY_FS),
            ).arrange(DOWN, buff=0.44).move_to(stage_center(-0.1))
            self.play(*[FadeIn(m, shift=RIGHT * 0.2) for m in items],
                      lag_ratio=0.4, run_time=min(1.6, max(0.8, tr.duration * 0.4)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._costs = items

    def _beat2(self):
        """The waiting room becomes the tree — the film's anchor object."""
        with self.voiceover(text=BEATS[2]) as tr:
            swap_rails(self, headline("It never sorts. It only needs the top."),
                       caption("the most urgent, right now"))
            self.play(FadeOut(self._costs, run_time=0.3))
            labels = [t for t in self.tvals if t is not None]
            self.play(FadeIn(self.tree.group),
                      run_time=min(0.9, max(0.45, tr.duration * 0.22)))
            self.play(*[FadeIn(t) for t in labels],
                      run_time=min(0.9, max(0.45, tr.duration * 0.22)))
            self.play(self._tint(0, ACCENT), run_time=0.4)
            top = Text("most urgent", font=MONO, font_size=SMALL_FS, color=ACCENT)
            top.next_to(self.tree.nodes[0], LEFT, buff=0.28)
            self.play(FadeIn(top, shift=RIGHT * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._toplab = top

    def _beat3(self):
        """The promise, drawn on the edges."""
        with self.voiceover(text=BEATS[3]) as tr:
            swap_rails(self, headline("Every parent is no larger than its children."),
                       caption("the one heap rule"))
            self.play(FadeOut(self._toplab, run_time=0.25))
            for e in self.tree.edges:
                e.set_stroke(opacity=0.30)
            self.play(
                self.tree.edges[0].animate.set_stroke(color=GOOD, width=3.2),
                self.tree.edges[1].animate.set_stroke(color=GOOD, width=3.2),
                run_time=min(0.9, max(0.45, tr.duration * 0.22)),
            )
            self.play(
                self.tree.edges[2].animate.set_stroke(color=GOOD, width=3.2),
                self.tree.edges[3].animate.set_stroke(color=GOOD, width=3.2),
                self.tree.edges[4].animate.set_stroke(color=GOOD, width=3.2),
                self.tree.edges[5].animate.set_stroke(color=GOOD, width=3.2),
                run_time=min(0.9, max(0.45, tr.duration * 0.22)),
            )
            note = Text("1 <= 3 and 2   ·   3 <= 7 and 4   ·   2 <= 9", font=MONO,
                        font_size=SMALL_FS, color=GOOD).move_to([0, -2.32, 0])
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._ruletext = note

    def _beat4(self):
        """The promise is loose on purpose: siblings may be unordered."""
        with self.voiceover(text=BEATS[4]) as tr:
            swap_rails(self, headline("Siblings can be out of order."),
                       caption("the promise is loose on purpose"))
            self.play(FadeOut(self._ruletext, run_time=0.25))
            self.play(self._tint(1, WINDOW), self._tint(2, WINDOW), run_time=0.45)
            note = Text("3 and 2 are siblings — the rule says nothing about them",
                        font=MONO, font_size=SMALL_FS, color=WINDOW)
            note.move_to([0, -2.32, 0])
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._sibnote = note

    def _beat5(self):
        """The duality: the same heap, laid out level by level in an array."""
        with self.voiceover(text=BEATS[5]) as tr:
            swap_rails(self, headline("The tree is really an array."),
                       caption("filled level by level"))
            self.play(FadeOut(self._sibnote, run_time=0.25))
            self.play(self._tint(1, PRIMARY, 0.12), self._tint(2, PRIMARY, 0.12),
                      run_time=0.3)
            self.play(FadeIn(self.row.cells, shift=UP * 0.25), FadeIn(self.row.idx),
                      run_time=min(1.2, max(0.6, tr.duration * 0.3)))
            link = Text("index 0 at the root  ·  same values, same order", font=MONO,
                        font_size=SMALL_FS, color=MUTED).move_to([0, -2.32, 0])
            self.play(FadeIn(link, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._link = link

    def _beat6(self):
        """Index arithmetic, shown on both views at once."""
        with self.voiceover(text=BEATS[6]) as tr:
            swap_rails(self, headline("Index arithmetic gives the family."),
                       caption("parent (i-1)//2  ·  kids 2i+1, 2i+2"))
            self.play(FadeOut(self._link, run_time=0.25))
            self.play(self._tint(1, ACCENT), *self.row.focus(1, color=ACCENT),
                      run_time=0.45)
            self.play(self._tint(0, PRIMARY), *self.row.focus(0, color=PRIMARY),
                      run_time=0.4)
            self.play(self._tint(3, GOOD), self._tint(4, GOOD),
                      *self.row.focus(3, color=GOOD), *self.row.focus(4, color=GOOD),
                      run_time=0.45)
            self.play(
                Indicate(self.tvals[1], color=ACCENT, scale_factor=1.3),
                Indicate(self.row.texts[1], color=ACCENT, scale_factor=1.3),
                run_time=0.7,
            )
            l1 = Text("i = 1   ·   parent = (i - 1) // 2 = 0", font=MONO,
                      font_size=SMALL_FS, color=INK).move_to([0, -2.28, 0])
            l2 = Text("children = 2i + 1 = 3   and   2i + 2 = 4", font=MONO,
                      font_size=SMALL_FS, color=INK).move_to([0, -2.62, 0])
            self.play(FadeIn(l1, shift=UP * 0.1), run_time=0.4)
            self.play(FadeIn(l2, shift=UP * 0.1), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._arith = VGroup(l1, l2)

    def _beat7(self):
        """Push: the value lands in the free slot."""
        with self.voiceover(text=BEATS[7]) as tr:
            swap_rails(self, headline("Insert at the end, then climb."),
                       caption("sift up while it beats its parent"))
            self.play(FadeOut(self._arith, run_time=0.3))
            self.play(*self.row.reset_all(), self._tint(0, PRIMARY, 0.10),
                      self._tint(1, PRIMARY, 0.10), self._tint(3, PRIMARY, 0.10),
                      self._tint(4, PRIMARY, 0.10), run_time=0.35)
            free = Text("free slot", font=MONO, font_size=SMALL_FS, color=MUTED)
            free.next_to(self.tree.nodes[FREE], DOWN, buff=0.14)
            self.play(FadeIn(free), run_time=0.3)
            new_t = self._node_text(0, ACCENT, FREE)
            self.tvals[FREE] = new_t
            self.play(FadeIn(new_t, scale=1.3), run_time=0.45)
            self._array_write(FREE, 0, color=ACCENT, rt=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.45)))
            self._free = free

    def _beat8(self):
        """Sift up: two swaps, each one level closer to the root."""
        with self.voiceover(text=BEATS[8]) as tr:
            swap_rails(self, headline("Climbing never costs more than log n."),
                       caption("one swap per level"))
            self.play(FadeOut(self._free, run_time=0.25))
            self._swap(FREE, 2, rt=min(0.9, max(0.5, tr.duration * 0.22)))
            self._swap(2, 0, rt=min(0.9, max(0.5, tr.duration * 0.22)))
            self.play(self._tint(0, GOOD), *self.row.focus(0, color=GOOD), run_time=0.4)
            note = Text("2 swaps for 7 slots  ·  each swap halves the distance",
                        font=MONO, font_size=SMALL_FS, color=MUTED).move_to([0, -2.32, 0])
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._climb = note

    def _beat9(self):
        """Pop: the top leaves, the last element takes the root, then sinks."""
        with self.voiceover(text=BEATS[9]) as tr:
            swap_rails(self, headline("Remove the top: last one up, then sink."),
                       caption("sift down"))
            self.play(FadeOut(self._climb, run_time=0.25))
            last_v = self.avalues[FREE]
            self.play(FadeOut(self.tvals[0]), self._out(self.row.texts[0]),
                      run_time=0.4)
            self.tvals[0] = None
            self.avalues[0] = None
            # the array shrinks at the tail; the last value becomes the new root
            self.play(self.tvals[FREE].animate.move_to(self.node_pos[0]),
                      self._out(self.row.texts[FREE]),
                      run_time=min(0.9, max(0.5, tr.duration * 0.22)))
            self.tvals[0], self.tvals[FREE] = self.tvals[FREE], None
            self.row.texts[FREE] = None
            self.avalues[FREE] = None
            self._array_write(0, last_v, color=ACCENT, rt=0.5)
            self.play(self._tint(0, ACCENT), self._tint(1, WINDOW), self._tint(2, WINDOW),
                      *self.row.focus(0, color=ACCENT),
                      run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat10(self):
        """Sift down: compare both children, swap with the smaller."""
        with self.voiceover(text=BEATS[10]) as tr:
            swap_rails(self, headline("Swap with the smaller child, repeat."),
                       caption("sift down until it beats both"))
            self._swap(0, 2, rt=min(1.0, max(0.55, tr.duration * 0.26)))
            self.play(*self.row.reset_all(), self._tint(0, GOOD),
                      self._tint(1, PRIMARY, 0.10), self._tint(2, PRIMARY, 0.10),
                      self._tint(3, PRIMARY, 0.10), self._tint(4, PRIMARY, 0.10),
                      self._tint(5, PRIMARY, 0.10), *self.row.focus(0, color=GOOD),
                      run_time=0.45)
            note = Text("children are 3 and 1, so the 1 rises and the 2 sinks",
                        font=MONO, font_size=SMALL_FS, color=MUTED).move_to([0, -2.32, 0])
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._sink = note

    def _beat11(self):
        """Peek: index zero, in both views."""
        with self.voiceover(text=BEATS[11]) as tr:
            swap_rails(self, headline("The minimum is always index zero."),
                       caption("peek is O(1)"))
            self.play(FadeOut(self._sink, run_time=0.25))
            self.play(Circumscribe(self.tree.nodes[0], color=GOOD),
                      Circumscribe(self.row.cell(0), color=GOOD), run_time=0.8)
            note = Text("min = heap[0]   ·   nothing to search", font=MONO,
                        font_size=SMALL_FS, color=GOOD).move_to([0, -2.32, 0])
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._peek = note

    def _beat12(self):
        """Complexity, stated cold."""
        with self.voiceover(text=BEATS[12]) as tr:
            swap_rails(self, headline("O(1) peek, O(log n) push and pop."),
                       caption("heapify is O(n), not O(n log n)"))
            self.play(FadeOut(self._peek, run_time=0.25))
            labels = [t for t in self.tvals if t is not None]
            self.play(FadeOut(self.tree.group), FadeOut(self.row.cells),
                      FadeOut(self.row.idx), *[FadeOut(t) for t in labels],
                      run_time=0.45)
            peek = VGroup(Text("peek", font=MONO, font_size=BODY_FS, color=GOOD),
                          MathTex(r"O(1)", color=GOOD).scale(1.2)).arrange(DOWN, buff=0.2)
            change = VGroup(Text("push / pop", font=MONO, font_size=BODY_FS, color=PRIMARY),
                            MathTex(r"O(\log n)", color=PRIMARY).scale(1.2)
                            ).arrange(DOWN, buff=0.2)
            build = VGroup(Text("heapify", font=MONO, font_size=BODY_FS, color=WINDOW),
                           MathTex(r"O(n)", color=WINDOW).scale(1.2)).arrange(DOWN, buff=0.2)
            trio = VGroup(peek, change, build).arrange(RIGHT, buff=1.5)
            trio.move_to(stage_center(0.15))
            note = Text("build from n items in one pass — most nodes are leaves",
                        font=MONO, font_size=SMALL_FS, color=MUTED)
            note.move_to([0, -1.85, 0])
            self.play(*[FadeIn(m) for m in (peek, change, build)],
                      lag_ratio=0.45, run_time=min(1.6, max(0.8, tr.duration * 0.4)))
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._complexity = VGroup(peek, change, build, note)

    def _beat13(self):
        """Shape A: top k, with a bounded heap."""
        with self.voiceover(text=BEATS[13]) as tr:
            swap_rails(self, headline("Top k: keep only k items."),
                       caption("evict the weakest survivor"))
            self.play(FadeOut(self._complexity, run_time=0.3))
            self.stream = ArrayRow([5, 1, 8, 3, 9, 2, 7], cell=0.66, fs=24,
                                   show_index=False)
            self.stream.group.move_to([0, 1.15, 0])
            self.keep = ArrayRow([None, None, None], cell=0.8, fs=24, show_index=False)
            self.keep.group.move_to([0, -0.95, 0])
            st = Text("stream, one value at a time", font=MONO, font_size=SMALL_FS,
                      color=MUTED)
            st.next_to(self.stream.cells, UP, buff=0.2)
            kt = Text("keep the 3 largest so far", font=MONO, font_size=SMALL_FS,
                      color=PRIMARY)
            kt.next_to(self.keep.cells, UP, buff=0.2)
            self._kparts = [self.stream.cells, st, self.keep.cells, kt]
            self.play(FadeIn(self.stream.cells), FadeIn(st), run_time=0.45)
            self.play(FadeIn(self.keep.cells), FadeIn(kt), run_time=0.45)
            self.keep_vals = [None, None, None]

            def kwrite(i: int, v: int):
                """Keep the row a *true* min-heap array, not just the arrival order."""
                if self.keep_vals[i] == v:
                    return
                self.keep_vals[i] = v
                self._reveal(self._set_cell(self.keep, i, v), rt=0.3)

            # [5] -> the 1 floats above the 5 -> the 8 lands in the last slot
            self.play(*self.stream.focus(0, color=WINDOW), run_time=0.3)
            kwrite(0, 5)
            self.play(*self.stream.focus(1, color=WINDOW), run_time=0.3)
            kwrite(0, 1)
            kwrite(1, 5)
            self.play(*self.stream.focus(2, color=WINDOW), run_time=0.3)
            kwrite(2, 8)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat14(self):
        """The counter-intuitive line: a min-heap keeps the k largest."""
        with self.voiceover(text=BEATS[14]) as tr:
            swap_rails(self, headline("The k largest live in a min-heap."),
                       caption("its top is your weakest keeper"))
            self.play(self.keep.focus(0, color=ACCENT),
                      self.keep.texts[0].animate.set_color(ACCENT),
                      run_time=0.45)
            self.play(*self.stream.focus(3, color=WINDOW), run_time=0.4)
            self.play(self.keep.texts[0].animate.set_color(GONE),
                      run_time=0.35)
            self._hide(self.keep.texts[0], rt=0.3)
            self.keep_vals[0] = 3
            self._reveal(self._set_cell(self.keep, 0, 3, color=ACCENT), rt=0.35)
            note = Text("the top is the weakest survivor — it is what leaves",
                        font=MONO, font_size=SMALL_FS, color=MUTED).move_to([0, -2.32, 0])
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._weak = note

    def _beat15(self):
        """Why top-k is O(n log k)."""
        with self.voiceover(text=BEATS[15]) as tr:
            swap_rails(self, headline("It never holds more than k."),
                       caption("O(n log k), not O(n log n)"))
            self.play(FadeOut(self._weak, run_time=0.25))
            sortc = chip("sort:  n log n", color=GONE, fs=SMALL_FS)
            heapc = chip("heap of size k:  n log k", color=GOOD, fs=SMALL_FS)
            pair = VGroup(sortc, heapc).arrange(RIGHT, buff=0.5).move_to([0, 0.15, 0])
            note = Text("k much smaller than n  →  log k much smaller than log n",
                        font=MONO, font_size=SMALL_FS, color=MUTED).move_to([0, -1.9, 0])
            self.play(FadeIn(sortc, shift=UP * 0.15), run_time=0.45)
            self.play(FadeIn(heapc, shift=UP * 0.15),
                      run_time=min(1.0, max(0.5, tr.duration * 0.26)))
            self.play(FadeIn(note), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._topk = VGroup(*self._kparts, pair, note)

    def _beat16(self):
        """Shape C: k-way merge, the heap as a bank of pointers."""
        with self.voiceover(text=BEATS[16]) as tr:
            swap_rails(self, headline("Merge k lists: one head per list."),
                       caption("pop the smallest, push its successor"))
            self.play(FadeOut(self._topk, run_time=0.35))
            sources = VGroup(
                chip("A:  1  4  9", color=WINDOW, fs=SMALL_FS),
                chip("B:  2  6", color=WINDOW, fs=SMALL_FS),
                chip("C:  3  7", color=WINDOW, fs=SMALL_FS),
            ).arrange(DOWN, buff=0.34).move_to([-4.3, 0.15, 0])
            heads = ArrayRow([1, 2, 3], cell=0.78, fs=24, show_index=False)
            heads.group.move_to([0.2, 0.15, 0])
            heapt = Text("one head per list", font=MONO, font_size=SMALL_FS, color=PRIMARY)
            heapt.next_to(heads.cells, UP, buff=0.2)
            out = ArrayRow([None, None, None], cell=0.78, fs=24, show_index=False)
            out.group.move_to([4.3, 0.15, 0])
            outt = Text("output", font=MONO, font_size=SMALL_FS, color=GOOD)
            outt.next_to(out.cells, UP, buff=0.2)
            self.play(FadeIn(sources), run_time=0.4)
            self.play(FadeIn(heads.cells), FadeIn(heapt), run_time=0.45)
            self.play(FadeIn(out.cells), FadeIn(outt), run_time=0.4)
            self.play(*heads.focus(0, color=ACCENT), run_time=0.3)
            self._set_cell(out, 0, 1, color=GOOD)
            self._reveal(out.texts[0], rt=0.35)
            self.play(self._out(heads.texts[0]), run_time=0.3)
            # the heap re-forms on {2, 3} and list A's successor (4) comes in behind
            self.play(self._out(heads.texts[1]), self._out(heads.texts[2]), run_time=0.3)
            for i, v in ((0, 2), (1, 3), (2, 4)):
                new = self._set_cell(heads, i, v, color=WINDOW if i == 2 else INK)
                new.set_opacity(0.0)
                self.play(new.animate.set_opacity(1.0), run_time=0.3)
            note = Text("4 comes from list A — the same list the 1 came from",
                        font=MONO, font_size=SMALL_FS, color=MUTED).move_to([0, -1.75, 0])
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._merge = VGroup(sources, heads.cells, heapt, out.cells, outt, note)

    def _beat17(self):
        """Shape D: greedy — pop the best, push the remainder back."""
        with self.voiceover(text=BEATS[17]) as tr:
            swap_rails(self, headline("Greedy: pop the best, push the rest back."),
                       caption("Last Stone Weight"))
            self.play(FadeOut(self._merge, run_time=0.35))
            stones = ArrayRow([9, 7, 4, 2], cell=0.86, fs=26, show_index=False)
            stones.group.move_to([0, 0.95, 0])
            cap = Text("the two heaviest are always at the top", font=MONO,
                       font_size=SMALL_FS, color=MUTED)
            cap.next_to(stones.cells, UP, buff=0.25)
            self.play(FadeIn(stones.cells), FadeIn(cap), run_time=0.45)
            self.play(*stones.focus(0, color=ACCENT), *stones.focus(1, color=ACCENT),
                      run_time=0.45)
            diff = Text("9  −  7  =  2", font=MONO, font_size=BODY_FS, color=GOOD)
            diff.move_to([0, -0.85, 0])
            self.play(Write(diff), run_time=min(1.0, max(0.5, tr.duration * 0.28)))
            nxt = ArrayRow([4, 2, 2], cell=0.86, fs=26, show_index=False)
            nxt.group.move_to([0, 0.95, 0])
            self.play(FadeOut(stones.cells), FadeIn(nxt.cells), run_time=0.4)
            self.play(*nxt.focus(2, color=GOOD), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._greedy = VGroup(cap, diff, nxt.cells)

    def _beat18(self):
        """Retroactive greedy: the heap remembers what you already passed."""
        with self.voiceover(text=BEATS[18]) as tr:
            swap_rails(self, headline("The heap lets you decide retroactively."),
                       caption("refuel at the best station you passed"))
            self.play(FadeOut(self._greedy, run_time=0.35))
            road = Line([-5.6, 0.5, 0], [5.6, 0.5, 0], color=STROKE, stroke_width=3)
            stations = [(-3.6, "10"), (-0.8, "30"), (2.2, "20")]
            dots = VGroup()
            labels = VGroup()
            for x, fuel in stations:
                d = Dot([x, 0.5, 0], radius=0.11, color=PRIMARY)
                dots.add(d)
                lb = Text(fuel, font=MONO, font_size=SMALL_FS, color=MUTED)
                lb.next_to(d, DOWN, buff=0.18)
                labels.add(lb)
            start = Text("start", font=MONO, font_size=SMALL_FS, color=INK)
            start.move_to([-5.1, 1.05, 0])
            dry = Text("dry", font=MONO, font_size=SMALL_FS, color=GONE)
            dry.move_to([4.9, 1.05, 0])
            xmark = Text("✗", font=MONO, font_size=30, color=GONE).move_to([4.9, 0.5, 0])
            self.play(FadeIn(road), FadeIn(start), run_time=0.4)
            self.play(FadeIn(dots), FadeIn(labels), run_time=0.45)
            self.play(FadeIn(xmark), FadeIn(dry), run_time=0.45)
            back = Arrow([4.4, 0.85, 0], [-0.8, 1.05, 0], buff=0.1, color=GOOD,
                         stroke_width=3.0, max_tip_length_to_length_ratio=0.07)
            best = Text("fuel 30 — the best station you passed", font=MONO,
                        font_size=SMALL_FS, color=GOOD).move_to([-0.8, -1.35, 0])
            self.play(dots[1].animate.set_color(GOOD).scale(1.5), GrowArrow(back),
                      run_time=0.7)
            self.play(FadeIn(best, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._retro = VGroup(road, start, dots, labels, xmark, dry, best, back)

    def _beat19(self):
        """Shape E: two heaps, and the median between them."""
        with self.voiceover(text=BEATS[19]) as tr:
            swap_rails(self, headline("Two heaps hold a running median."),
                       caption("a low half and a high half"))
            self.play(FadeOut(self._retro, run_time=0.35))
            self.low_boxes, self.low_ttl = self._column(self.low_x, "low  ·  max-heap",
                                                       ACCENT)
            self.high_boxes, self.high_ttl = self._column(self.high_x, "high  ·  min-heap",
                                                          WINDOW)
            self.low_vals = [None, None, None]
            self.high_vals = [None, None, None]
            rule_txt = Text("every low value <= every high value", font=MONO,
                            font_size=SMALL_FS, color=MUTED).move_to([0, -1.35, 0])
            sizes = Text("sizes differ by at most one", font=MONO, font_size=SMALL_FS,
                         color=MUTED).move_to([0, -1.75, 0])
            self.play(FadeIn(self.low_boxes), FadeIn(self.high_boxes), run_time=0.45)
            self.play(FadeIn(self.low_ttl), FadeIn(self.high_ttl), run_time=0.4)
            self.play(FadeIn(rule_txt, shift=UP * 0.12), run_time=0.4)
            self.play(FadeIn(sizes, shift=UP * 0.12), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._heapdocs = VGroup(rule_txt, sizes)

    def _cell_point(self, side: str, i: int):
        x = self.low_x if side == "low" else self.high_x
        return [x, self.col_top - i * self.col_gap, 0]

    def _put(self, side: str, i: int, value, color=INK, rt: float = 0.4):
        t = Text(str(value), font=MONO, font_size=BODY_FS, color=color)
        t.move_to(self._cell_point(side, i))
        (self.low_vals if side == "low" else self.high_vals)[i] = t
        self.play(FadeIn(t, scale=1.2), run_time=rt)
        return t

    def _move(self, t, side: str, i: int, rt: float = 0.5):
        self.play(t.animate.move_to(self._cell_point(side, i)), run_time=rt)

    def _beat20(self):
        """The invariant on real values: 5 and 2, then the median between the tops."""
        with self.voiceover(text=BEATS[20]) as tr:
            swap_rails(self, headline("Low <= high, sizes differ by at most one."),
                       caption("the two-heap invariant"))
            self.play(self.low_boxes[0].animate.set_stroke(ACCENT, width=2.6),
                      run_time=0.3)
            self._put("low", 0, 5, ACCENT, rt=0.4)
            self.play(self.low_boxes[1].animate.set_stroke(ACCENT, width=2.6),
                      run_time=0.25)
            self._put("low", 1, 2, ACCENT, rt=0.4)
            # low's max crosses to high, and 2 rises into low's top
            self._move(self.low_vals[0], "high", 0, rt=0.55)
            self._move(self.low_vals[1], "low", 0, rt=0.55)
            self.high_vals[0], self.high_vals[1] = self.low_vals[0], None
            self.low_vals[0], self.low_vals[1] = self.low_vals[1], None
            med = chip("median = 3.5", color=GOOD, fs=SMALL_FS).move_to([0, 0.39, 0])
            self.play(FadeIn(med, scale=1.1), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._med = med

    def _beat21(self):
        """The readout: the top of low, or the average of both tops. Camera into the tops."""
        with self.voiceover(text=BEATS[21]) as tr:
            swap_rails(self, headline("The median lives at the two tops."),
                       caption("top of low, or both tops averaged"))
            self.play(self.low_boxes[1].animate.set_stroke(ACCENT, width=2.6),
                      self.high_boxes[1].animate.set_stroke(WINDOW, width=2.6),
                      run_time=0.3)
            eight = self._put("low", 1, 8, WINDOW, rt=0.4)
            # 8 crosses to high, high's 5 trades places with low's 2 — one exchange
            five, two = self.high_vals[0], self.low_vals[0]
            self.play(eight.animate.move_to(self._cell_point("high", 0)),
                      five.animate.move_to(self._cell_point("low", 0)),
                      two.animate.move_to(self._cell_point("low", 1)),
                      run_time=0.65)
            self.high_vals[0] = eight
            self.low_vals[0], self.low_vals[1] = five, two
            self.play(FadeOut(self._med), run_time=0.25)
            med = chip("median = low[0] = 5", color=GOOD, fs=SMALL_FS).move_to([0, 0.39, 0])
            self.camera.frame.save_state()  # bare: stores only, never animates
            self.play(
                FadeIn(med, scale=1.1),
                self.camera.auto_zoom([self.low_boxes[0], self.high_boxes[0], med],
                                      margin=1.2),
                run_time=min(1.1, max(0.55, tr.duration * 0.28)),
            )
            self.play(Circumscribe(self.low_boxes[0], color=GOOD), run_time=0.6)
            self.play(Restore(self.camera.frame), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._med2 = med

    def _beat22(self):
        """What breaks it."""
        with self.voiceover(text=BEATS[22]) as tr:
            swap_rails(self, headline("Full order or key lookup? Not a heap."),
                       caption("that's a sort or a hash map"))
            self.play(FadeOut(self._med2), FadeOut(self.low_boxes),
                      FadeOut(self.high_boxes), FadeOut(self.low_ttl),
                      FadeOut(self.high_ttl), FadeOut(self._heapdocs),
                      *[FadeOut(t) for t in (self.low_vals + self.high_vals)
                        if t is not None],
                      run_time=0.4)
            items = VGroup(
                chip("need every element in order  →  sort", color=GONE, fs=BODY_FS),
                chip("lookup by key  →  hash map", color=GONE, fs=BODY_FS),
                chip("k close to n  →  sorting is no slower", color=MUTED, fs=BODY_FS),
            ).arrange(DOWN, buff=0.42).move_to(stage_center(-0.1))
            self.play(*[FadeIn(m, shift=RIGHT * 0.2) for m in items],
                      lag_ratio=0.4, run_time=min(1.6, max(0.8, tr.duration * 0.4)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._breaks = items

    def _beat23(self):
        """Recall card: the line the viewer leaves with."""
        with self.voiceover(text=BEATS[23]) as tr:
            swap_rails(self, headline("Need the extreme of a changing set?"),
                       caption("that's a heap  ·  O(log n) changes"))
            self.play(FadeOut(self._breaks, run_time=0.3))
            box = card(9.6, 1.7, color=ACCENT, fill=PANEL)
            box.move_to(stage_center(-0.1))
            top = Text("Heap", font=MONO, font_size=32, color=ACCENT)
            sub = Text("peek O(1)  ·  push / pop O(log n)  ·  top k is O(n log k)",
                       font=MONO, font_size=SMALL_FS, color=MUTED)
            VGroup(top, sub).arrange(DOWN, buff=0.24).move_to(box.get_center())
            self.play(FadeIn(box, scale=0.96), run_time=0.45)
            self.play(Write(top), run_time=0.5)
            self.play(FadeIn(sub), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
