"""
Pattern 10 — Binary Search.

The film follows the card's own argument, and its own spine: the *boundary discipline*.
Hook (guess the number) -> the predicate that flips exactly once -> the job -> the two
markers and the half-open window -> the two branches (`hi = mid` keeps the candidate,
`lo = mid + 1` throws it away) -> the window halving, drawn as a shrinking span on an
ArrayRow -> lo meets hi, one index left -> why it's correct -> complexity -> the two
templates you must never mix -> the trace -> the one-liners -> shapes B/C -> what breaks
it -> recognition -> the recall card.

The search span is computed state (ValueTrackers + always_redraw), so the halving you
watch is the algorithm's own arithmetic, not a hand-tuned keyframe.

Narration lives in BEATS and every animation is timed against `tracker.duration`, so the
picture and the voice cannot drift: one file is the source of truth for both.
"""

import math

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Circumscribe,
    DashedLine,
    FadeIn,
    FadeOut,
    Indicate,
    Line,
    MathTex,
    Rectangle,
    Restore,
    RoundedRectangle,
    Text,
    ValueTracker,
    VGroup,
    always_redraw,
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
from shots import ArrayRow, chip, pointer

PATTERN_SLUG = "binary-search"
TITLE = "Binary Search"
SUMMARY = "A question that flips exactly once turns a linear scan into a halving search."
SCENE_CLASS = "BinarySearch"
POSTER_AT = 32.0

ARR = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
TARGET = 8
N = len(ARR)

BEATS = [
    # 0 hook
    "Guess a number from one to a hundred. Seven questions, and you always win.",
    # 1 ELI5
    "You say fifty. They say higher, and half the numbers are gone forever.",
    # 2 the insight
    "It works because the question flips from no to yes exactly once.",
    # 3 the job
    "Here is the job: find eight in this sorted array of eleven numbers.",
    # 4 the two markers
    "Two markers. lo is a real candidate. hi is one past the last candidate.",
    # 5 mid
    "Look at the middle. Index five holds twelve, which is at least eight.",
    # 6 hi = mid
    "So the answer is at five or to its left. hi moves onto the middle, never past it.",
    # 7 lo = mid + 1
    "Now the middle is index two, holding six. Too small, so lo jumps past it.",
    # 8 halving
    "Either way the window halves: eleven candidates, then five, then two, then one.",
    # 9 lo meets hi
    "When lo meets hi, that position is the answer. Index three holds eight.",
    # 10 correctness
    "Why is that correct? The answer never leaves the window, and the window always shrinks.",
    # 11 complexity
    "Log n time, constant space. A million items takes twenty questions.",
    # 12 templates
    "Now the part that bites. Two consistent styles exist. Pick one and never mix them.",
    # 13 half-open
    "Half open: hi starts at n, the loop runs while lo is less than hi, and hi takes mid.",
    # 14 closed
    "Closed: hi starts at n minus one, loop while lo is at most hi, and hi takes mid minus one.",
    # 15 the trace
    "Mix them and you loop forever, or you skip the answer. Trace a two element array first.",
    # 16 one-liners
    "Everything else is a one liner. Last position is lower bound of x plus one, minus one.",
    # 17 shape B
    "Shape two: the array isn't sorted, but a condition over indices still flips once. Peaks.",
    # 18 rotated
    "In a rotated array, compare the middle with the left end to find the sorted half.",
    # 19 shape C
    "Shape three: search the answer, not the array. For Koko, x is eating speed.",
    # 20 range
    "Feasible means the hours fit. Pull the range from the data, never a magic constant.",
    # 21 min vs max
    "Minimise or maximise? Maximise flips the branches and rounds the middle up.",
    # 22 what breaks it
    "What breaks it: a predicate that flips more than once. The loop runs and returns garbage.",
    # 23 recall
    "A question that flips once, then halve the range.",
]

CHAPTERS = {
    0: "The hook",
    1: "Guess the number",
    2: "The insight",
    3: "The job",
    4: "The two markers",
    9: "lo meets hi",
    10: "Why it's correct",
    11: "Complexity",
    12: "Two templates, never mixed",
    16: "One template, many answers",
    17: "Shape B: conditions",
    19: "Shape C: search the answer",
    22: "What breaks it",
    23: "Recall",
}

# The two templates, side by side: the card's number-one failure mode is mixing them.
HALF_OPEN = [
    "def lower_bound(arr, x):",
    "    lo, hi = 0, len(arr)",
    "    while lo < hi:",
    "        mid = (lo + hi) // 2",
    "        if arr[mid] < x:",
    "            lo = mid + 1",
    "        else:",
    "            hi = mid",
    "    return lo",
]
CLOSED = [
    "lo, hi = 0, len(arr) - 1",
    "while lo <= hi:",
    "    mid = (lo + hi) // 2",
    "    if arr[mid] == x:",
    "        return mid",
    "    if arr[mid] < x:",
    "        lo = mid + 1",
    "    else:",
    "        hi = mid - 1",
]


class BinarySearch(PrebakedVoiceMovingCameraScene):
    # ---------------------------------------------------------------------------- setup
    def construct(self):
        bg(self)
        self.row = ArrayRow(ARR, cell=0.64, fs=26, index_fs=SMALL_FS)
        self.row.group.move_to([0, 0.55, 0])
        # The search window is computed state: lo and hi are the algorithm's own variables.
        self.lo_t = ValueTracker(0)
        self.hi_t = ValueTracker(N)
        self.span = None
        self.lo_ptr = None
        self.fence = None
        self._note = None
        for i in range(len(BEATS)):
            getattr(self, f"_beat{i}")()

    # ------------------------------------------------------------------------- geometry
    def _left_anchor(self, i: int) -> float:
        """x of the boundary just BEFORE cell i (and past the row when i == n)."""
        i = max(0, min(int(i), N))
        if i >= N:
            return self.row.cells[N - 1].get_right()[0] + 0.26
        return self.row.cells[i].get_left()[0] - 0.05

    def _right_anchor(self, i: int) -> float:
        """x of the boundary just AFTER cell i."""
        i = max(0, min(int(i), N))
        if i >= N:
            return self.row.cells[N - 1].get_right()[0] + 0.26
        return self.row.cells[i].get_right()[0] + 0.05

    def _at(self, fn, t: float) -> float:
        t = max(0.0, min(float(t), float(N)))
        i = int(math.floor(t))
        f = t - i
        return fn(i) + (fn(min(i + 1, N)) - fn(i)) * f

    def _span_mob(self):
        """The live candidate window: cells lo .. hi-1, shrinking with the trackers."""
        x0 = self._at(self._left_anchor, self.lo_t.get_value())
        x1 = self._at(self._right_anchor, self.hi_t.get_value() - 1)
        x1 = max(x1, x0 + 0.05)
        top = self.row.cells[0].get_top()[1] + 0.09
        bot = self.row.cells[0].get_bottom()[1] - 0.09
        r = RoundedRectangle(
            corner_radius=min(0.12, (x1 - x0) / 2),
            width=x1 - x0,
            height=top - bot,
            stroke_color=WINDOW,
            stroke_width=2.4,
            fill_color=WINDOW,
            fill_opacity=0.18,
        )
        r.move_to([(x0 + x1) / 2, (top + bot) / 2, 0])
        return r

    def _fence_mob(self):
        """hi as a fence: the wall one past the last candidate."""
        x = self._at(self._left_anchor, self.hi_t.get_value())
        top = self.row.cells[0].get_top()[1] + 0.36
        bot = self.row.cells[0].get_bottom()[1] - 0.10
        ln = DashedLine(
            [x, bot, 0], [x, top, 0], color=PRIMARY, stroke_width=3.0, dash_length=0.09
        )
        lb = Text("hi", font=MONO, font_size=SMALL_FS, color=PRIMARY)
        lb.next_to(ln, UP, buff=0.12)
        return VGroup(ln, lb)

    def _lo_mob(self):
        i = max(0, min(int(round(self.lo_t.get_value())), N - 1))
        return pointer(self.row, i, "lo", color=ACCENT, fs=SMALL_FS)

    # ------------------------------------------------------------------------- utilities
    def _set_note(self, text: str, color=WINDOW, *, y: float = -1.25, fs: int = SMALL_FS,
                  rt: float = 0.42):
        new = Text(text, font=MONO, font_size=fs, color=color).move_to([0, y, 0])
        anims = []
        if self._note is not None:
            anims.append(FadeOut(self._note))
        anims.append(FadeIn(new, shift=UP * 0.12))
        self.play(*anims, run_time=rt)
        self._note = new
        return new

    def _drop_note(self, rt: float = 0.25):
        if self._note is not None:
            self.play(FadeOut(self._note), run_time=rt)
            self._note = None

    def _drop_search(self, rt: float = 0.45):
        """Fade the whole array phase — updaters first, or they fight the fade."""
        for m in (self.span, self.lo_ptr, self.fence):
            if m is not None:
                m.clear_updaters()
        self._drop_note(rt=0.2)
        stuff = [m for m in (self.span, self.lo_ptr, self.fence) if m is not None]
        stuff += [self.row.group]
        if getattr(self, "_tchip", None) is not None:
            stuff.append(self._tchip)
        self.play(*[FadeOut(m) for m in stuff], run_time=rt)
        self.span = self.lo_ptr = self.fence = None

    def _code_card(self, title: str, lines, key: int, color, fs: int = 15):
        rows = VGroup()
        key_row = None
        for i, ln in enumerate(lines):
            t = Text(ln, font=MONO, font_size=fs,
                     color=ACCENT if i == key else MUTED)
            rows.add(t)
            if i == key:
                key_row = t
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.115)
        box = card(rows.width + 0.7, rows.height + 0.6, color=color, fill=PANEL)
        rows.move_to(box.get_center())
        ttl = Text(title, font=FONT, font_size=SMALL_FS, color=color)
        ttl.next_to(box, UP, buff=0.16)
        return VGroup(ttl, box, rows), key_row

    # ---------------------------------------------------------------------------- beats
    def _beat0(self):
        """Hook: the two costs, as objects."""
        with self.voiceover(text=BEATS[0]) as tr:
            swap_rails(self, headline("Seven questions beat a hundred guesses."),
                       caption("linear scan vs bisection"))
            self.play(FadeIn(rule()), run_time=0.3)
            bad = chip("linear scan: 100 steps", color=GONE, fs=BODY_FS)
            good = chip("bisection: 7 steps", color=GOOD, fs=BODY_FS)
            self._hook = VGroup(bad, good).arrange(DOWN, buff=0.52).move_to(stage_center(-0.1))
            self.play(FadeIn(bad, shift=UP * 0.2), run_time=0.5)
            self.wait(0.2)
            self.play(FadeIn(good, shift=UP * 0.2), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))

    def _beat1(self):
        """ELI5: one guess kills half the range. The range is the object from now on."""
        with self.voiceover(text=BEATS[1]) as tr:
            swap_rails(self, headline("Half the numbers leave after one guess."),
                       caption("1..100  →  50, then half again"))
            self.play(FadeOut(self._hook, run_time=0.3))
            bar = Rectangle(width=11.0, height=0.66, stroke_color=STROKE, stroke_width=1.6,
                            fill_color=PANEL, fill_opacity=1.0).move_to([0, 0.45, 0])
            killed = Rectangle(width=5.5, height=0.66, stroke_color=GONE, stroke_width=1.6,
                               fill_color=GONE, fill_opacity=0.20).move_to([2.75, 0.45, 0])
            mid_line = Line([0, 0.12, 0], [0, 0.78, 0], color=ACCENT, stroke_width=4)
            lo_lb = Text("1", font=MONO, font_size=SMALL_FS, color=MUTED)
            lo_lb.next_to(bar, DOWN, buff=0.14).align_to(bar, LEFT).shift(RIGHT * 0.2)
            hi_lb = Text("100", font=MONO, font_size=SMALL_FS, color=MUTED)
            hi_lb.next_to(bar, DOWN, buff=0.14).align_to(bar, RIGHT).shift(LEFT * 0.2)
            mid_lb = Text("50", font=MONO, font_size=SMALL_FS, color=ACCENT)
            mid_lb.next_to(mid_line, UP, buff=0.12)
            self.play(FadeIn(bar), FadeIn(lo_lb), FadeIn(hi_lb), run_time=0.45)
            self.play(FadeIn(mid_line), FadeIn(mid_lb), run_time=0.4)
            self.play(FadeIn(killed), run_time=min(1.0, max(0.5, tr.duration * 0.28)))
            verdict = Text("higher  →  half gone forever", font=MONO, font_size=SMALL_FS,
                           color=GOOD).move_to([0, -1.35, 0])
            self.play(FadeIn(verdict, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._bar = VGroup(bar, killed, mid_line, lo_lb, hi_lb, mid_lb, verdict)

    def _beat2(self):
        """The insight, as a shape: false, false, false, true, true, true."""
        with self.voiceover(text=BEATS[2]) as tr:
            swap_rails(self, headline("The question flips from no to yes once."),
                       caption("no, no, no, yes, yes, yes"))
            self.play(FadeOut(self._bar, run_time=0.32))
            words = ["no", "no", "no", "yes", "yes", "yes"]
            cells = VGroup()
            for w in words:
                col = GONE if w == "no" else GOOD
                bx = card(0.78, 0.66, color=col, fill=PANEL)
                tx = Text(w, font=MONO, font_size=SMALL_FS, color=col)
                tx.move_to(bx.get_center())
                cells.add(VGroup(bx, tx))
            cells.arrange(RIGHT, buff=0.11).move_to([0, 0.5, 0])
            gap = (cells[2].get_right()[0] + cells[3].get_left()[0]) / 2
            flip = DashedLine([gap, -0.1, 0], [gap, 1.1, 0], color=ACCENT, stroke_width=3.4,
                              dash_length=0.08)
            flip_lb = Text("the flip", font=MONO, font_size=SMALL_FS, color=ACCENT)
            flip_lb.next_to(flip, UP, buff=0.12)
            self.play(FadeIn(cells, shift=UP * 0.2),
                      run_time=min(1.2, max(0.6, tr.duration * 0.3)))
            self.play(FadeIn(flip), FadeIn(flip_lb), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._flip = VGroup(cells, flip, flip_lb)

    def _beat3(self):
        """The job: the array + the target. This is the film's persistent anchor."""
        with self.voiceover(text=BEATS[3]) as tr:
            swap_rails(self, headline("Find eight in this sorted array."),
                       caption("sorted array, one target"))
            self.play(FadeOut(self._flip, run_time=0.32))
            self.play(FadeIn(self.row.cells, shift=UP * 0.25), FadeIn(self.row.idx),
                      run_time=min(1.2, max(0.6, tr.duration * 0.3)))
            self._tchip = chip("target = 8", color=ACCENT, fs=SMALL_FS)
            self._tchip.move_to([-5.2, 2.25, 0])
            self.play(FadeIn(self._tchip, scale=0.9), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat4(self):
        """The two markers land, and the window opens over the whole row."""
        with self.voiceover(text=BEATS[4]) as tr:
            swap_rails(self, headline("lo is a candidate; hi is one past it."),
                       caption("answer in [lo, hi)"))
            self.lo_t.set_value(5.6)
            self.hi_t.set_value(5.6)
            self.span = always_redraw(self._span_mob)
            self.lo_ptr = always_redraw(self._lo_mob)
            self.fence = always_redraw(self._fence_mob)
            self.add(self.span, self.lo_ptr, self.fence)
            self.play(
                self.lo_t.animate.set_value(0),
                self.hi_t.animate.set_value(N),
                run_time=min(1.5, max(0.8, tr.duration * 0.35)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat5(self):
        """First look at the middle: index five holds twelve."""
        with self.voiceover(text=BEATS[5]) as tr:
            swap_rails(self, headline("The middle is twelve — big enough."),
                       caption("mid = 5, value 12"))
            self.play(*self.row.focus(5, color=WINDOW, fill_opacity=0.30), run_time=0.45)
            self._set_note("mid = 5   ·   12 >= 8   ·   so 8 is here or to the left",
                           color=WINDOW)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat6(self):
        """The right edge moves ONTO the middle — never past it."""
        with self.voiceover(text=BEATS[6]) as tr:
            swap_rails(self, headline("Big enough: hi moves onto mid."),
                       caption("hi = mid, never mid - 1"))
            self.play(self.hi_t.animate.set_value(5),
                      *self.row.reset_all(),
                      run_time=min(1.2, max(0.6, tr.duration * 0.3)))
            self._set_note("hi = mid   ·   mid could still be the answer", color=PRIMARY)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat7(self):
        """The mirror branch: too small, so lo jumps PAST the middle."""
        with self.voiceover(text=BEATS[7]) as tr:
            swap_rails(self, headline("Too small: lo jumps past mid."),
                       caption("lo = mid + 1"))
            self.play(*self.row.focus(2, color=WINDOW, fill_opacity=0.30), run_time=0.4)
            self.play(self.lo_t.animate.set_value(3),
                      *self.row.reset_all(),
                      run_time=min(1.2, max(0.6, tr.duration * 0.3)))
            self._set_note("lo = mid + 1   ·   mid and everything before it are out",
                           color=ACCENT)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat8(self):
        """The halving, counted."""
        with self.voiceover(text=BEATS[8]) as tr:
            swap_rails(self, headline("Every step, the window halves."),
                       caption("11  →  5  →  2  →  1 candidates"))
            self._set_note("11 candidates", color=MUTED)
            for nxt_txt in ("11  →  5", "11  →  5  →  2", "11  →  5  →  2  →  1"):
                self._set_note(nxt_txt, color=WINDOW, rt=0.32)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat9(self):
        """lo meets hi: the window collapses to the answer index. Camera into the term."""
        with self.voiceover(text=BEATS[9]) as tr:
            swap_rails(self, headline("lo meets hi — that index is the answer."),
                       caption("lo == hi == 3"))
            self.play(*self.row.focus(4, color=WINDOW, fill_opacity=0.30), run_time=0.35)
            self.play(self.hi_t.animate.set_value(4), *self.row.reset_all(), run_time=0.5)
            self.play(*self.row.focus(3, color=WINDOW, fill_opacity=0.30), run_time=0.35)
            self.play(self.hi_t.animate.set_value(3), *self.row.reset_all(), run_time=0.5)
            self.camera.frame.save_state()  # bare: stores only, never animates
            self.play(
                self.camera.auto_zoom([self.row.cell(3), self.fence], margin=1.5),
                *self.row.mark_good(3),
                run_time=min(1.2, max(0.6, tr.duration * 0.28)),
            )
            self.play(Circumscribe(self.row.cell(3), color=GOOD), run_time=0.6)
            self.play(Restore(self.camera.frame), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat10(self):
        """The correctness argument: invariant plus shrinking."""
        with self.voiceover(text=BEATS[10]) as tr:
            swap_rails(self, headline("The answer never leaves the window."),
                       caption("invariant plus a shrinking window"))
            self._drop_note(rt=0.2)
            good = Text("answer in [lo, hi)   ·   window shrinks every step",
                        font=MONO, font_size=SMALL_FS, color=GOOD)
            stop = Text("lo == hi  →  one index left  →  that is the answer",
                        font=MONO, font_size=SMALL_FS, color=GOOD)
            stack = VGroup(good, stop).arrange(DOWN, buff=0.42).move_to([0, -1.5, 0])
            self.play(FadeIn(good, shift=UP * 0.12), run_time=0.45)
            self.play(FadeIn(stop, shift=UP * 0.12),
                      run_time=min(1.0, max(0.5, tr.duration * 0.26)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._why = stack

    def _beat11(self):
        """Complexity, stated cold."""
        with self.voiceover(text=BEATS[11]) as tr:
            swap_rails(self, headline("Log n time, constant space."),
                       caption("O(log n) time  ·  O(1) space"))
            self.play(FadeOut(self._why, run_time=0.3))
            self._drop_search(rt=0.4)
            slow = VGroup(
                Text("linear scan", font=MONO, font_size=BODY_FS, color=GONE),
                MathTex(r"O(n)", color=GONE).scale(1.25),
            ).arrange(DOWN, buff=0.22)
            fast = VGroup(
                Text("bisection", font=MONO, font_size=BODY_FS, color=GOOD),
                MathTex(r"O(\log n)", color=GOOD).scale(1.25),
            ).arrange(DOWN, buff=0.22)
            both = VGroup(slow, fast).arrange(RIGHT, buff=2.0).move_to(stage_center(0.15))
            arrow = Text("→", font=MONO, font_size=44, color=MUTED)
            arrow.move_to((slow.get_right() + fast.get_left()) / 2)
            note = Text("1,000,000 items  →  20 questions", font=MONO, font_size=SMALL_FS,
                        color=INK).move_to([0, -1.65, 0])
            self.play(FadeIn(slow), run_time=0.4)
            self.play(FadeIn(arrow), run_time=0.25)
            self.play(FadeIn(fast), run_time=0.45)
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._complexity = VGroup(both, arrow, note)

    def _beat12(self):
        """Two styles exist. Both correct alone; fatal together."""
        with self.voiceover(text=BEATS[12]) as tr:
            swap_rails(self, headline("Two styles exist. Never mix them."),
                       caption("half-open vs closed"))
            self.play(FadeOut(self._complexity, run_time=0.32))
            left, self._key_half = self._code_card("half-open", HALF_OPEN, 7, WINDOW)
            right, self._key_closed = self._code_card("closed", CLOSED, 8, PRIMARY)
            cards = VGroup(left, right).arrange(RIGHT, buff=0.5)
            cards.move_to([0, -0.15, 0])
            self._cards = cards
            self.play(FadeIn(left, shift=LEFT * 0.15),
                      run_time=min(1.1, max(0.5, tr.duration * 0.28)))
            self.play(FadeIn(right, shift=RIGHT * 0.15),
                      run_time=min(1.1, max(0.5, tr.duration * 0.28)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat13(self):
        """The half-open discipline, line by line."""
        with self.voiceover(text=BEATS[13]) as tr:
            swap_rails(self, headline("Half-open: hi = n, loop while lo < hi."),
                       caption("hi = n, lo < hi, hi = mid"))
            self.play(Indicate(self._key_half, color=ACCENT, scale_factor=1.06),
                      run_time=0.7)
            self._set_note("hi is exclusive: mid can still be where lo lands", color=WINDOW,
                           y=-2.25)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat14(self):
        """The closed discipline — also correct, and also self-consistent."""
        with self.voiceover(text=BEATS[14]) as tr:
            swap_rails(self, headline("Closed: hi = n-1, loop while lo <= hi."),
                       caption("hi = n-1, lo <= hi, hi = mid-1"))
            self.play(Indicate(self._key_closed, color=ACCENT, scale_factor=1.06),
                      run_time=0.7)
            self._set_note("a hit returns from inside the loop, or tracks a best",
                           color=PRIMARY, y=-2.25)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat15(self):
        """The card's own trace, run on a two-element array."""
        with self.voiceover(text=BEATS[15]) as tr:
            swap_rails(self, headline("Mixing them loops forever or skips."),
                       caption("infinite loop, or a skipped answer"))
            self._drop_note(rt=0.2)
            self.play(FadeOut(self._cards, run_time=0.35))
            trace = VGroup(
                Text("[1, 3]   target 3", font=MONO, font_size=SMALL_FS, color=INK),
                Text("lo=0 hi=2  mid=1  arr[1] >= 3  →  hi=1",
                     font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("lo=0 hi=1  mid=0  arr[0] <  3  →  lo=1",
                     font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("lo=1 hi=1  stop  →  index 1  ✓",
                     font=MONO, font_size=SMALL_FS, color=GOOD),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.30)
            box = card(trace.width + 0.9, trace.height + 0.8, color=WINDOW, fill=PANEL)
            box.move_to([0, -0.15, 0])
            trace.move_to(box.get_center())
            self.play(FadeIn(box), run_time=0.35)
            self.play(*[FadeIn(t, shift=RIGHT * 0.15) for t in trace],
                      lag_ratio=0.35, run_time=min(1.6, max(0.8, tr.duration * 0.38)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._trace = VGroup(box, trace)

    def _beat16(self):
        """lower_bound is the whole family."""
        with self.voiceover(text=BEATS[16]) as tr:
            swap_rails(self, headline("One template, three answers."),
                       caption("lower_bound derives the rest"))
            self.play(FadeOut(self._trace, run_time=0.32))
            rows = VGroup(
                Text("first(x)  = lower_bound(x)", font=MONO, font_size=BODY_FS, color=INK),
                Text("last(x)   = lower_bound(x + 1) - 1", font=MONO, font_size=BODY_FS,
                     color=INK),
                Text("count(x)  = last(x) - first(x) + 1", font=MONO, font_size=BODY_FS,
                     color=INK),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.36)
            box = card(rows.width + 1.1, rows.height + 0.9, color=PRIMARY, fill=PANEL)
            box.move_to(stage_center(-0.1))
            rows.move_to(box.get_center())
            self.play(FadeIn(box), run_time=0.32)
            self.play(*[FadeIn(t, shift=RIGHT * 0.18) for t in rows],
                      lag_ratio=0.4, run_time=min(1.5, max(0.8, tr.duration * 0.36)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._oneliners = VGroup(box, rows)

    def _beat17(self):
        """Shape B: the predicate lives on indices, not on a sorted value."""
        with self.voiceover(text=BEATS[17]) as tr:
            swap_rails(self, headline("Shape B: the predicate is on indices."),
                       caption("peaks, mountain arrays"))
            self.play(FadeOut(self._oneliners, run_time=0.32))
            r = ArrayRow([1, 3, 5, 7, 6, 4, 2], cell=0.66, fs=26, index_fs=SMALL_FS)
            r.group.move_to([0, 1.05, 0])
            strip = VGroup()
            for w in ("yes", "yes", "yes", "no", "no", "no"):
                col = GOOD if w == "yes" else GONE
                bx = card(0.74, 0.52, color=col, fill=PANEL)
                tx = Text(w, font=MONO, font_size=SMALL_FS, color=col)
                tx.move_to(bx.get_center())
                strip.add(VGroup(bx, tx))
            strip.arrange(RIGHT, buff=0.09).move_to([0, -0.35, 0])
            q = Text("climbing?  arr[mid] < arr[mid + 1]", font=MONO, font_size=SMALL_FS,
                     color=MUTED)
            q.next_to(strip, DOWN, buff=0.32)
            note = Text("the peak is the first  no", font=MONO, font_size=SMALL_FS, color=GOOD)
            note.next_to(q, DOWN, buff=0.28)
            self.play(FadeIn(r.cells), FadeIn(r.idx), run_time=0.45)
            self.play(*[FadeIn(c, shift=UP * 0.15) for c in strip],
                      lag_ratio=0.25, run_time=min(1.4, max(0.7, tr.duration * 0.34)))
            self.play(FadeIn(q), run_time=0.35)
            self.play(*r.focus(3, color=GOOD), FadeIn(note), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._mountain = VGroup(r.group, strip, q, note)

    def _beat18(self):
        """Rotated: find which half is sorted, then range-check."""
        with self.voiceover(text=BEATS[18]) as tr:
            swap_rails(self, headline("Rotated: find which half is sorted."),
                       caption("compare mid with lo"))
            self.play(FadeOut(self._mountain, run_time=0.32))
            r = ArrayRow([4, 5, 6, 7, 0, 1, 2], cell=0.68, fs=26, show_index=False)
            r.group.move_to([0, 0.85, 0])
            labels = VGroup()
            for i, name, col in ((0, "lo", ACCENT), (3, "mid", WINDOW), (6, "hi", PRIMARY)):
                t = Text(name, font=MONO, font_size=SMALL_FS, color=col)
                t.next_to(r.cell(i), DOWN, buff=0.30)
                labels.add(t)
            sorted_half = Text("left half 4..7 is sorted", font=MONO, font_size=SMALL_FS,
                               color=GOOD)
            check = Text("is 0 inside [4, 7]?   no  →  go right", font=MONO,
                         font_size=SMALL_FS, color=MUTED)
            stack = VGroup(sorted_half, check).arrange(DOWN, buff=0.34).move_to([0, -1.5, 0])
            self.play(FadeIn(r.cells), run_time=0.4)
            self.play(FadeIn(labels), run_time=0.4)
            self.play(*[r.focus(i, color=GOOD, fill_opacity=0.22)[0] for i in range(4)],
                      run_time=min(1.1, max(0.55, tr.duration * 0.28)))
            self.play(FadeIn(stack, shift=UP * 0.12), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._rotated = VGroup(r.group, labels, stack)

    def _beat19(self):
        """Shape C: the range is the set of possible answers, not an array."""
        with self.voiceover(text=BEATS[19]) as tr:
            swap_rails(self, headline("Shape C: search the answer, not the array."),
                       caption("x is the answer, feasible(x) is the check"))
            self.play(FadeOut(self._rotated, run_time=0.32))
            cells = VGroup()
            for w, x in (("no", "2"), ("no", "4"), ("no", "6"), ("yes", "8"), ("yes", "10")):
                col = GONE if w == "no" else GOOD
                bx = card(0.86, 0.72, color=col, fill=PANEL)
                tx = Text(w, font=MONO, font_size=SMALL_FS, color=col)
                tx.move_to(bx.get_center())
                cells.add(VGroup(bx, tx))
            cells.arrange(RIGHT, buff=0.12).move_to([0, 0.75, 0])
            gap = (cells[2].get_right()[0] + cells[3].get_left()[0]) / 2
            fence = DashedLine([gap, 0.15, 0], [gap, 1.5, 0], color=ACCENT, stroke_width=3.4,
                               dash_length=0.08)
            flb = Text("smallest feasible x", font=MONO, font_size=SMALL_FS, color=ACCENT)
            flb.next_to(fence, UP, buff=0.12)
            note = Text("x = eating speed  ·  feasible(x): hours(x) <= h",
                        font=MONO, font_size=SMALL_FS, color=MUTED).move_to([0, -1.0, 0])
            self.play(FadeIn(cells, shift=UP * 0.2),
                      run_time=min(1.3, max(0.65, tr.duration * 0.32)))
            self.play(FadeIn(fence), FadeIn(flb), run_time=0.45)
            self.play(FadeIn(note), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._answersearch = VGroup(cells, fence, flb, note)

    def _beat20(self):
        """The range comes from the data, never from a magic constant."""
        with self.voiceover(text=BEATS[20]) as tr:
            swap_rails(self, headline("Take the range from the data."),
                       caption("lo and hi from the input"))
            self.play(FadeOut(self._answersearch, run_time=0.32))
            rows = VGroup(
                Text("x  =  eating speed", font=MONO, font_size=BODY_FS, color=INK),
                Text("lo = 1          hi = max(piles)", font=MONO, font_size=BODY_FS,
                     color=INK),
                Text("feasible(x):  sum(ceil(p / x)) <= h", font=MONO, font_size=BODY_FS,
                     color=GOOD),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.38)
            box = card(rows.width + 1.1, rows.height + 0.9, color=WINDOW, fill=PANEL)
            box.move_to(stage_center(0.0))
            rows.move_to(box.get_center())
            self.play(FadeIn(box), run_time=0.32)
            self.play(*[FadeIn(t, shift=RIGHT * 0.18) for t in rows],
                      lag_ratio=0.4, run_time=min(1.5, max(0.8, tr.duration * 0.36)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._rangesrc = VGroup(box, rows)

    def _beat21(self):
        """Minimise vs maximise: flip the branches and round mid up."""
        with self.voiceover(text=BEATS[21]) as tr:
            swap_rails(self, headline("Maximise flips the branches and rounds up."),
                       caption("minimise vs maximise"))
            self.play(FadeOut(self._rangesrc, run_time=0.32))
            lo_card, _ = self._code_card(
                "minimise x", ["if feasible(mid):", "    hi = mid", "else:", "    lo = mid + 1"],
                1, GOOD, fs=17,
            )
            hi_card, _ = self._code_card(
                "maximise x",
                ["if feasible(mid):", "    lo = mid", "else:", "    hi = mid - 1",
                 "mid = (lo + hi + 1) // 2"],
                4, ACCENT, fs=17,
            )
            pair = VGroup(lo_card, hi_card).arrange(RIGHT, buff=0.9)
            pair.move_to(stage_center(-0.05))
            self.play(FadeIn(lo_card, shift=LEFT * 0.15), run_time=0.45)
            self.play(FadeIn(hi_card, shift=RIGHT * 0.15),
                      run_time=min(1.1, max(0.55, tr.duration * 0.3)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._minmax = pair

    def _beat22(self):
        """What breaks it: a predicate that flips more than once."""
        with self.voiceover(text=BEATS[22]) as tr:
            swap_rails(self, headline("A predicate that flips twice gives garbage."),
                       caption("monotonicity is the load-bearing rule"))
            self.play(FadeOut(self._minmax, run_time=0.32))
            cells = VGroup()
            for w in ("true", "false", "true", "false", "true"):
                bx = card(1.24, 0.6, color=GONE, fill=PANEL)
                tx = Text(w, font=MONO, font_size=SMALL_FS, color=GONE)
                tx.move_to(bx.get_center())
                cells.add(VGroup(bx, tx))
            cells.arrange(RIGHT, buff=0.12).move_to([0, 0.55, 0])
            note = Text("say why bigger x makes it easier — or don't binary search",
                        font=MONO, font_size=SMALL_FS, color=MUTED).move_to([0, -1.05, 0])
            self.play(FadeIn(cells, shift=UP * 0.2),
                      run_time=min(1.3, max(0.65, tr.duration * 0.32)))
            self.play(Indicate(cells, color=GONE, scale_factor=1.04), run_time=0.6)
            self.play(FadeIn(note), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._breaks = VGroup(cells, note)

    def _beat23(self):
        """Recall card: the line the viewer leaves with."""
        with self.voiceover(text=BEATS[23]) as tr:
            swap_rails(self, headline("A question that flips once — then halve."),
                       caption("halve the range, O(log n)"))
            self.play(FadeOut(self._breaks, run_time=0.3))
            box = card(9.6, 1.7, color=ACCENT, fill=PANEL)
            box.move_to(stage_center(-0.1))
            top = Text("Binary Search", font=MONO, font_size=32, color=ACCENT)
            sub = Text("monotone predicate  ·  halve the window  ·  O(log n)",
                       font=MONO, font_size=SMALL_FS, color=MUTED)
            VGroup(top, sub).arrange(DOWN, buff=0.24).move_to(box.get_center())
            self.play(FadeIn(box, scale=0.96), run_time=0.45)
            self.play(FadeIn(top, shift=UP * 0.12), run_time=0.5)
            self.play(FadeIn(sub), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
