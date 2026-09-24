"""
Pattern 03 — Sliding Window.

The film follows the card's own argument: hook -> the job -> the brute force that rebuilds
every run -> the cardboard tube (shuffle, don't recount) -> one in, one out -> the only
question that varies -> the three shapes (fixed, longest, shortest) -> the trap where a
longest-window loop answers a shortest-window question -> why a nested loop is still O(n)
-> amortised -> the bookkeeping toolkit -> the missing counter -> what breaks it (negatives)
-> subarray versus subsequence -> the counter-tell -> the recall card.

Both edges of every window are ValueTrackers and every rectangle and readout is rebuilt from
them, so the window is computed state — never a keyframe. Narration lives in BEATS and all
timing is written against `tracker.duration`.
"""

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    FadeIn,
    FadeOut,
    Indicate,
    MathTex,
    Text,
    ValueTracker,
    VGroup,
    Write,
    always_redraw,
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
    stage_center,
    swap_rails,
)
from prebaked_voice import PrebakedVoiceMovingCameraScene
from shots import ArrayRow, chip, pointer, window_over

PATTERN_SLUG = "sliding-window"
TITLE = "Sliding Window"
SUMMARY = "A contiguous run slides instead of rebuilding: O(n^2) becomes O(n)."
SCENE_CLASS = "SlidingWindow"
POSTER_AT = 56.0

NUMS = [2, 1, 5, 1, 3, 2]
K = 3
CHARS = ["a", "b", "c", "a", "b", "b"]
K_DISTINCT = 2
SUMS = [2, 3, 1, 2, 4, 3]
TARGET = 7

BEATS = [
    # 0 hook
    "When the answer is a contiguous run of an array, don't rebuild it every time. Slide it.",
    # 1 the job
    "Here's the job. Find the three numbers sitting in a row with the biggest total.",
    # 2 brute force
    "The slow way rebuilds every window from scratch. Four windows, and three additions "
    "inside each one.",
    # 3 ELI5
    "The fast way is a cardboard tube at your eye. Keep it there, and shuffle sideways. "
    "One house enters, one leaves.",
    # 4 one in, one out
    "The two in the middle never changed, so you never recount them. One addition, "
    "one subtraction.",
    # 5 the only question
    "Everything here is that one idea. And only one question varies: when do I shuffle?",
    # 6 shape A
    "Shape one: the size k is given. Both edges move together, every single step, forever.",
    # 7 shape A cost
    "Linear time, constant extra space. The brute force you replaced was quadratic.",
    # 8 shape B
    "Shape two, the longest valid window: the right edge advances always, the left edge "
    "only to repair.",
    # 9 shape B rule
    "Then record the answer after the shrink loop, when the window is guaranteed good.",
    # 10 shape B demo
    "Watch it run. Kinds, length, best: the answer is only recorded once the window is "
    "good again.",
    # 11 shape C + the trap
    "Shape three is the mirror image: shrink while it is still good, and record before "
    "removing. Those two differences are exactly the ones people get wrong.",
    # 12 shape C demo
    "Watch the shortest version run. It records the length, then drops the left edge, "
    "over and over.",
    # 13 why linear
    "Why is it linear when there is a nested loop? Because the left edge only ever moves "
    "forward.",
    # 14 amortised
    "It crosses each index at most once, so both pointers take at most two n steps total. "
    "That is amortised.",
    # 15 the toolkit
    "What you keep about the window decides the difficulty: a sum, a count of zeros, "
    "or a dictionary.",
    # 16 the missing counter
    "The trick worth learning cold is one missing counter, instead of comparing whole "
    "dictionaries on every step.",
    # 17 what breaks it
    "Know what breaks it. Negative numbers destroy a sum window, because shrinking it "
    "stops helping you.",
    # 18 recognise
    "So reach for it when the problem says subarray or substring. Both of those words "
    "mean contiguous.",
    # 19 anti-signal
    "The anti-signal is subsequence. Those elements need not touch, and this pattern "
    "dies right there.",
    # 20 counter-tell
    "Sorted input that converges from both ends is a different pattern. This one drags "
    "forward, left to right.",
    # 21 recall
    "One window, two edges, and each edge moves forward only once.",
]

CHAPTERS = {
    0: "The hook",
    1: "The job",
    2: "Brute force",
    3: "The cardboard tube",
    5: "When do I shuffle?",
    6: "Shape A: fixed size",
    7: "Complexity",
    8: "Shape B: longest",
    10: "Shape B on screen",
    11: "Shape C: shortest",
    13: "Why it is still O(n)",
    15: "The toolkit",
    17: "What breaks it",
    18: "How to recognise it",
    21: "Recall",
}

ROW_Y = 0.62


# --------------------------------------------------------------------------------------
# local primitives
# --------------------------------------------------------------------------------------
def live_text(builder, anchor, *, color=INK, fs=SMALL_FS):
    """A Text whose string comes from computed state — never a keyframe."""
    def _make():
        t = Text(builder(), font=MONO, font_size=fs, color=color)
        t.move_to(anchor)
        return t

    return always_redraw(_make)


def kill(scene, *mobs, run_time: float = 0.3):
    """Fade out live (always_redraw) mobjects without their updaters fighting the fade."""
    live = [m for m in mobs if m is not None]
    for m in live:
        m.clear_updaters()
    if live:
        scene.play(*[FadeOut(m, run_time=run_time) for m in live])


def make_row(values, y=ROW_Y, *, cell=0.62, fs=26, show_index=False):
    r = ArrayRow(values, cell=cell, fs=fs, show_index=show_index, index_fs=SMALL_FS)
    r.group.move_to([0, y, 0])
    return r


def fixed_trace(values, k):
    """Shape A: every (lo, hi) the fixed window visits, its sum, and the best sum so far."""
    total = sum(values[:k])
    states, sums, bests = [(0, k - 1)], [total], [total]
    best = total
    for hi in range(k, len(values)):
        total += values[hi] - values[hi - k]
        best = max(best, total)
        states.append((hi - k + 1, hi))
        sums.append(total)
        bests.append(best)
    return states, sums, bests


def longest_trace(values, k):
    """Shape B: longest window with at most k distinct values, as the edges actually move."""
    counts, lo, best = {}, 0, 0
    states, info = [], []
    for hi, x in enumerate(values):
        counts[x] = counts.get(x, 0) + 1
        while len(counts) > k:
            counts[values[lo]] -= 1
            if counts[values[lo]] == 0:
                del counts[values[lo]]
            lo += 1
        best = max(best, hi - lo + 1)
        states.append((lo, hi))
        info.append((best, len(counts), hi - lo + 1))
    return states, info


def shortest_trace(values, target):
    """Shape C: shrink while still valid, recording the length BEFORE the left edge moves."""
    lo, total, best = 0, 0, None
    states, sums, bests = [], [], []
    for hi, x in enumerate(values):
        total += x
        while total >= target and lo <= hi:
            if best is None or hi - lo + 1 < best:
                best = hi - lo + 1
            total -= values[lo]
            lo += 1
        states.append((lo, hi))
        sums.append(total)
        bests.append(best if best is not None else 0)
    return states, sums, bests


class SlidingWindow(PrebakedVoiceMovingCameraScene):
    # ---------------------------------------------------------------------------- setup
    def construct(self):
        bg(self)
        for i in range(len(BEATS)):
            getattr(self, f"_beat{i}")()

    # ------------------------------------------------------------------------- utilities
    def _frame(self, step):
        """The (lo, hi) pair for the tracker's current frame. Read live, never captured.

        Binding the state list as a default argument captures the list OBJECT, so a later
        beat that rebinds `self.states` leaves the live rectangle indexing a stale list.
        """
        i = int(round(step.get_value()))
        states = self.states
        return states[max(0, min(i, len(states) - 1))]

    def _live_window(self, row, step, *, color=WINDOW, opacity=0.22):
        def _make():
            lo, hi = self._frame(step)
            return window_over(row, lo, hi, color=color, opacity=opacity)

        return always_redraw(_make)

    def _live_ptr(self, row, step, which, text, color):
        """which=1 is the right edge (labelled above), which=0 the left edge (below)."""
        def _make():
            return pointer(row, self._frame(step)[which], text,
                           color=color, above=which == 1)

        return always_redraw(_make)

    # ---------------------------------------------------------------------------- beats
    def _beat0(self):
        """Hook: the trade, named in plain words before any notation."""
        with self.voiceover(text=BEATS[0]) as tr:
            swap_rails(self, headline("Do not rebuild a run. Slide it."),
                       caption("O(n^2)  →  O(n)"))
            bad = chip("rebuild every run: n^2", color=GONE, fs=BODY_FS)
            good = chip("slide the window: n", color=GOOD, fs=BODY_FS)
            row = VGroup(bad, good).arrange(RIGHT, buff=0.7).move_to(stage_center(0.15))
            note = Text("adding what enters, removing what leaves",
                        font=MONO, font_size=SMALL_FS, color=MUTED)
            note.move_to([0, -1.5, 0])
            self.play(FadeIn(bad, shift=UP * 0.2), run_time=0.5)
            self.wait(0.25)
            self.play(FadeIn(good, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._hook = VGroup(row, note)

    def _beat1(self):
        """The job: array + k, and the first window named as an object."""
        with self.voiceover(text=BEATS[1]) as tr:
            swap_rails(self, headline("Best sum of three in a row."),
                       caption("a contiguous run, size k"))
            self.play(FadeOut(self._hook, run_time=0.3))
            self.row = make_row(NUMS)
            self.step = ValueTracker(0.0)
            self.states = [(0, K - 1)]
            self.add(self.step)
            kchip = chip(f"k = {K}", color=ACCENT, fs=BODY_FS).move_to([0, 1.95, 0])
            self.win = self._live_window(self.row, self.step)
            note = Text("the first window of three", font=MONO, font_size=SMALL_FS, color=MUTED)
            note.move_to([0, -1.55, 0])
            self.play(FadeIn(self.row.cells, shift=UP * 0.22), run_time=0.55)
            self.play(FadeIn(kchip, scale=0.92), run_time=0.4)
            self.play(FadeIn(self.win), FadeIn(note), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._kchip = kchip
            self._jobnote = note

    def _beat2(self):
        """Brute force, shown as the thing it is: the same cells added up again and again."""
        with self.voiceover(text=BEATS[2]) as tr:
            swap_rails(self, headline("Recounting every window from scratch."),
                       caption("four windows, three additions each"))
            self.states = [(i, i + K - 1) for i in range(len(NUMS) - K + 1)]
            self.play(FadeOut(self._jobnote, run_time=0.25))
            count = live_text(
                lambda: f"windows rebuilt = {int(round(self.step.get_value())) + 1}"
                        f"   additions = {(int(round(self.step.get_value())) + 1) * K}",
                [0, -1.55, 0], color=GONE,
            )
            self.add(count)
            self.play(self.step.animate.set_value(3.0),
                      run_time=min(2.2, max(1.2, tr.duration * 0.42)))
            self.play(self.step.animate.set_value(0.0), run_time=0.7)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._brute = count

    def _beat3(self):
        """ELI5: the tube shuffles sideways, and the middle cells are never touched."""
        with self.voiceover(text=BEATS[3]) as tr:
            swap_rails(self, headline("Shuffle the tube sideways."),
                       caption("the middle never changes"))
            mid = Text("these two never changed", font=MONO, font_size=SMALL_FS, color=GOOD)
            mid.move_to([0, -2.2, 0])
            self.states = [(0, K - 1), (1, K)]
            self.play(*self.row.focus(1, color=GOOD), *self.row.focus(2, color=GOOD),
                      run_time=0.5)
            self.play(FadeIn(mid, shift=UP * 0.12), run_time=0.35)
            self.play(self.step.animate.set_value(1.0),
                      *self.row.focus(0, color=GONE, fill_opacity=0.18),
                      *self.row.focus(3, color=ACCENT),
                      run_time=min(1.5, max(0.8, tr.duration * 0.3)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._tube = mid

    def _beat4(self):
        """One in, one out — the arithmetic that replaces the recount."""
        with self.voiceover(text=BEATS[4]) as tr:
            swap_rails(self, headline("One addition, one subtraction."),
                       caption("8 - 2 + 1 = 7"))
            self.play(FadeOut(self._tube), FadeOut(self._kchip, run_time=0.25))
            kill(self, self._brute, run_time=0.25)
            self._brute = None
            math = Text("8  −  2  +  1  =  7", font=MONO, font_size=32, color=WINDOW)
            math.move_to([0, -1.5, 0])
            note = Text("out goes the 2, in comes the 1", font=MONO, font_size=SMALL_FS,
                        color=MUTED)
            note.move_to([0, -2.2, 0])
            self.play(Write(math), run_time=min(1.2, max(0.6, tr.duration * 0.3)))
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._math = VGroup(math, note)

    def _beat5(self):
        """The pivot: everything else is fixed, only the shrink rule varies."""
        with self.voiceover(text=BEATS[5]) as tr:
            swap_rails(self, headline("Only one question ever varies."),
                       caption("when do I shuffle?"))
            kill(self, self.win, self.row.cells, self._math, run_time=0.35)
            fixed = chip("size k given  →  no decision", color=PRIMARY, fs=BODY_FS)
            varying = chip("no size given  →  when do I shrink?", color=ACCENT, fs=BODY_FS)
            both = VGroup(fixed, varying).arrange(DOWN, buff=0.55).move_to(stage_center(0.05))
            self.play(FadeIn(fixed, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(varying, shift=UP * 0.2), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._question = both

    def _beat6(self):
        """Shape A on screen: both edges move together, and the best window is remembered."""
        with self.voiceover(text=BEATS[6]) as tr:
            swap_rails(self, headline("Fixed size: both edges move together."),
                       caption("no decision, just a slide"))
            self.play(FadeOut(self._question, run_time=0.3))
            self.row = make_row(NUMS)
            self.step = ValueTracker(0.0)
            self.states, self.sums, self.bests = fixed_trace(NUMS, K)
            self.add(self.step)
            self.win = self._live_window(self.row, self.step)
            self.lo_p = self._live_ptr(self.row, self.step, 0, "lo", ACCENT)
            self.hi_p = self._live_ptr(self.row, self.step, 1, "hi", PRIMARY)
            readout = live_text(
                lambda: f"sum = {self.sums[int(round(self.step.get_value()))]}"
                        f"   best = {self.bests[int(round(self.step.get_value()))]}",
                [0, -1.55, 0], color=WINDOW,
            )
            self.add(readout)
            self.play(FadeIn(self.row.cells, shift=UP * 0.22), run_time=0.5)
            self.play(FadeIn(self.win), FadeIn(self.lo_p), FadeIn(self.hi_p), FadeIn(readout),
                      run_time=0.5)
            self.play(self.step.animate.set_value(2.0), run_time=0.9)
            self.play(self.step.animate.set_value(3.0), run_time=0.7)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._shapeA = readout

    def _beat7(self):
        """Shape A's cost, stated cold."""
        with self.voiceover(text=BEATS[7]) as tr:
            swap_rails(self, headline("Linear time, constant space."),
                       caption("the brute force was quadratic"))
            kill(self, self.win, self.lo_p, self.hi_p, self._shapeA, self.row.cells,
                 run_time=0.35)
            slow = VGroup(
                Text("recount every window", font=MONO, font_size=BODY_FS, color=GONE),
                MathTex(r"O(n^2)", color=GONE).scale(1.25),
            ).arrange(DOWN, buff=0.26)
            fast = VGroup(
                Text("slide the window", font=MONO, font_size=BODY_FS, color=GOOD),
                MathTex(r"O(n)", color=GOOD).scale(1.25),
            ).arrange(DOWN, buff=0.26)
            both = VGroup(slow, fast).arrange(RIGHT, buff=1.9).move_to(stage_center(-0.05))
            arrow = Text("→", font=MONO, font_size=44, color=MUTED)
            arrow.move_to((slow.get_right() + fast.get_left()) / 2)
            space = Text("space O(1) for a fixed k", font=MONO, font_size=SMALL_FS, color=GOOD)
            space.move_to([0, -2.2, 0])
            self.play(FadeIn(slow), run_time=0.45)
            self.play(FadeIn(arrow), run_time=0.3)
            self.play(FadeIn(fast), run_time=0.45)
            self.play(FadeIn(space, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._cost = VGroup(both, arrow, space)

    def _beat8(self):
        """Shape B: grow right always, shrink left only to repair."""
        with self.voiceover(text=BEATS[8]) as tr:
            swap_rails(self, headline("Longest valid: grow right, repair left."),
                       caption("right always advances"))
            self.play(FadeOut(self._cost, run_time=0.3))
            grow = VGroup(
                Text("hi += 1", font=MONO, font_size=BODY_FS, color=PRIMARY),
                Text("always, unconditionally", font=MONO, font_size=SMALL_FS, color=MUTED),
            ).arrange(DOWN, buff=0.2)
            shrink = VGroup(
                Text("while not valid:  lo += 1", font=MONO, font_size=BODY_FS, color=ACCENT),
                Text("only while the window is broken", font=MONO, font_size=SMALL_FS, color=MUTED),
            ).arrange(DOWN, buff=0.2)
            both = VGroup(grow, shrink).arrange(DOWN, buff=0.75).move_to(stage_center(0.0))
            self.play(FadeIn(grow, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(shrink, shift=UP * 0.2), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._rulesB = both

    def _beat9(self):
        """Shape B's rule, in one line."""
        with self.voiceover(text=BEATS[9]) as tr:
            swap_rails(self, headline("Record the answer after the repair."),
                       caption("the window is good by then"))
            self.play(FadeOut(self._rulesB, run_time=0.3))
            code = VGroup(
                Text("hi += 1", font=MONO, font_size=BODY_FS, color=PRIMARY),
                Text("while not valid:  lo += 1", font=MONO, font_size=BODY_FS, color=ACCENT),
                Text("best = max(best, hi - lo + 1)", font=MONO, font_size=BODY_FS, color=GOOD),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to(stage_center(0.0))
            after = Text("record AFTER the while loop", font=MONO, font_size=SMALL_FS, color=GOOD)
            after.move_to([0, -2.25, 0])
            self.play(*[FadeIn(t, shift=RIGHT * 0.2) for t in code],
                      lag_ratio=0.4, run_time=min(1.6, max(0.8, tr.duration * 0.4)))
            self.play(FadeIn(after, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._ruleB = VGroup(code, after)

    def _beat10(self):
        """Shape B on screen: right edge always grows, left edge only repairs."""
        with self.voiceover(text=BEATS[10]) as tr:
            swap_rails(self, headline("Longest run with at most two kinds."),
                       caption("grow right, repair left, then record"))
            self.play(FadeOut(self._ruleB, run_time=0.3))
            self.row = make_row(CHARS)
            self.step = ValueTracker(0.0)
            self.states, self.info = longest_trace(CHARS, K_DISTINCT)
            self.add(self.step)
            self.win = self._live_window(self.row, self.step)
            self.lo_p = self._live_ptr(self.row, self.step, 0, "lo", ACCENT)
            self.hi_p = self._live_ptr(self.row, self.step, 1, "hi", PRIMARY)
            readout = live_text(
                lambda: "kinds {}   length {}   best {}".format(
                    *self.info[int(round(self.step.get_value()))]),
                [0, -1.6, 0], color=WINDOW,
            )
            self.add(readout)
            self.play(FadeIn(self.row.cells, shift=UP * 0.22), run_time=0.45)
            self.play(FadeIn(self.win), FadeIn(self.lo_p), FadeIn(self.hi_p), FadeIn(readout),
                      run_time=0.45)
            self.play(self.step.animate.set_value(2.0),
                      run_time=min(1.4, max(0.7, tr.duration * 0.28)))
            self.play(self.step.animate.set_value(5.0),
                      run_time=min(1.4, max(0.7, tr.duration * 0.28)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._shapeB = VGroup(readout, self.win, self.lo_p, self.hi_p)

    def _beat11(self):
        """Shape C and its trap, in one beat: the mirror rule, and the bug it causes."""
        with self.voiceover(text=BEATS[11]) as tr:
            swap_rails(self, headline("Shortest valid: shrink while still good."),
                       caption("record inside, before removing"))
            self.play(FadeOut(self._shapeB), FadeOut(self.row.cells, run_time=0.3))
            code = VGroup(
                Text("while valid:", font=MONO, font_size=BODY_FS, color=GOOD),
                Text("→ best = min(best, hi - lo + 1)", font=MONO, font_size=BODY_FS,
                     color=GOOD),
                Text("→ lo += 1", font=MONO, font_size=BODY_FS, color=ACCENT),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.36).move_to([0, 0.7, 0])
            warn = chip("longest code answering a shortest question", color=GONE, fs=BODY_FS)
            warn.move_to([0, -1.85, 0])
            self.play(*[FadeIn(t, shift=RIGHT * 0.2) for t in code],
                      lag_ratio=0.4, run_time=min(1.5, max(0.8, tr.duration * 0.35)))
            self.play(FadeIn(warn, shift=UP * 0.2), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._ruleC = VGroup(code, warn)

    def _beat12(self):
        """Shape C on screen: shrink while valid, record before the left edge moves."""
        with self.voiceover(text=BEATS[12]) as tr:
            swap_rails(self, headline("Shortest window summing to seven."),
                       caption("shrink, record, drop, repeat"))
            self.play(FadeOut(self._ruleC, run_time=0.3))
            self.row = make_row(SUMS)
            self.step = ValueTracker(0.0)
            self.states, self.sums, self.bests = shortest_trace(SUMS, TARGET)
            self.add(self.step)
            self.win = self._live_window(self.row, self.step)
            self.lo_p = self._live_ptr(self.row, self.step, 0, "lo", ACCENT)
            self.hi_p = self._live_ptr(self.row, self.step, 1, "hi", PRIMARY)
            readout = live_text(
                lambda: f"sum = {self.sums[int(round(self.step.get_value()))]}"
                        f"   best = {self.bests[int(round(self.step.get_value()))] or '—'}",
                [0, -1.6, 0], color=WINDOW,
            )
            self.add(readout)
            self.play(FadeIn(self.row.cells, shift=UP * 0.22), run_time=0.5)
            self.play(FadeIn(self.win), FadeIn(self.lo_p), FadeIn(self.hi_p), FadeIn(readout),
                      run_time=0.5)
            self.play(self.step.animate.set_value(3.0),
                      run_time=min(1.6, max(0.8, tr.duration * 0.3)))
            self.play(self.step.animate.set_value(5.0),
                      run_time=min(1.6, max(0.8, tr.duration * 0.3)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._shapeC = VGroup(readout, self.win, self.lo_p, self.hi_p)

    def _beat13(self):
        """Why a nested loop is still linear: the left edge only ever walks forward."""
        with self.voiceover(text=BEATS[13]) as tr:
            swap_rails(self, headline("The left edge only moves forward."),
                       caption("never backwards, never twice"))
            self.play(FadeOut(self._shapeC), FadeOut(self.row.cells, run_time=0.35))
            self.row = make_row([1, 2, 3, 4, 5, 6], y=0.75)
            self.p = ValueTracker(0.0)
            self.add(self.p)
            crossed = always_redraw(
                lambda: window_over(self.row, 0, max(0, int(round(self.p.get_value()))),
                                    color=ACCENT, opacity=0.16)
            )
            lo_ptr = always_redraw(
                lambda: pointer(self.row, int(round(self.p.get_value())), "lo",
                                color=ACCENT, above=False)
            )
            count = live_text(
                lambda: f"lo has moved {int(round(self.p.get_value()))} of 6 times",
                [0, -1.7, 0], color=ACCENT,
            )
            self.add(count)
            self.play(FadeIn(self.row.cells), run_time=0.45)
            self.play(FadeIn(crossed), FadeIn(lo_ptr), FadeIn(count), run_time=0.45)
            self.play(self.p.animate.set_value(5.0),
                      run_time=min(2.0, max(1.0, tr.duration * 0.4)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._forward = VGroup(self.row.cells, crossed, lo_ptr, count)

    def _beat14(self):
        """Amortised — the word the card says to say out loud."""
        with self.voiceover(text=BEATS[14]) as tr:
            swap_rails(self, headline("At most two n steps in total."),
                       caption("this is called amortised"))
            kill(self, *self._forward.submobjects, run_time=0.3)
            word = Text("amortised", font=MONO, font_size=40, color=ACCENT)
            word.move_to([0, 0.55, 0])
            eq = MathTex(r"n + n = 2n", color=GOOD).scale(1.25)
            eq.move_to([0, -0.75, 0])
            note = Text("each index is entered once and left once",
                        font=MONO, font_size=SMALL_FS, color=MUTED)
            note.move_to([0, -1.95, 0])
            self.play(Write(word), run_time=min(1.1, max(0.6, tr.duration * 0.25)))
            self.play(Write(eq), run_time=min(1.0, max(0.5, tr.duration * 0.25)))
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._amortised = VGroup(word, eq, note)

    def _beat15(self):
        """The bookkeeping toolkit — what you keep about the window."""
        with self.voiceover(text=BEATS[15]) as tr:
            swap_rails(self, headline("What you keep decides the difficulty."),
                       caption("sum, count of zeros, or a dict"))
            self.play(FadeOut(self._amortised, run_time=0.3))
            keep = VGroup(
                Text("✓  a running sum  →  sum thresholds", font=MONO, font_size=BODY_FS,
                     color=INK),
                Text("✓  a count of zeros  →  flip at most k", font=MONO, font_size=BODY_FS,
                     color=INK),
                Text("✓  char → count  →  distinct limits", font=MONO, font_size=BODY_FS,
                     color=INK),
                Text("✓  last index seen  →  jump lo", font=MONO, font_size=BODY_FS, color=INK),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            keep.move_to(stage_center(0.0))
            self.play(*[FadeIn(t, shift=RIGHT * 0.2) for t in keep],
                      lag_ratio=0.32, run_time=min(1.8, max(0.9, tr.duration * 0.45)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._toolkit = keep

    def _beat16(self):
        """The missing counter: one integer instead of a dictionary comparison per step."""
        with self.voiceover(text=BEATS[16]) as tr:
            swap_rails(self, headline("One counter, not two dictionaries."),
                       caption("zero unmatched means valid"))
            self.play(FadeOut(self._toolkit, run_time=0.3))
            bad = VGroup(
                Text("compare whole dicts every step", font=MONO, font_size=BODY_FS,
                     color=GONE),
                MathTex(r"O(nk)", color=GONE).scale(1.2),
            ).arrange(DOWN, buff=0.24)
            good = VGroup(
                Text("one integer: how many still missing", font=MONO, font_size=BODY_FS,
                     color=GOOD),
                MathTex(r"O(n)", color=GOOD).scale(1.2),
            ).arrange(DOWN, buff=0.24)
            both = VGroup(bad, good).arrange(DOWN, buff=0.85).move_to(stage_center(0.0))
            self.play(FadeIn(bad, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(good, shift=UP * 0.2), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._missing = both

    def _beat17(self):
        """What breaks it: negatives, and a sum threshold that stops being monotone."""
        with self.voiceover(text=BEATS[17]) as tr:
            swap_rails(self, headline("Know what breaks it."),
                       caption("negatives kill a sum window"))
            self.play(FadeOut(self._missing, run_time=0.3))
            ok = chip("all positive  →  shrinking works", color=GOOD, fs=BODY_FS)
            bad = chip("negatives  →  shrinking stops helping", color=GONE, fs=BODY_FS)
            both = VGroup(ok, bad).arrange(DOWN, buff=0.55).move_to(stage_center(0.1))
            note = Text("Subarray Product Less Than K needs all-positive input",
                        font=MONO, font_size=SMALL_FS, color=MUTED)
            note.move_to([0, -2.35, 0])
            self.play(FadeIn(ok, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(bad, shift=UP * 0.2), run_time=0.5)
            self.play(Indicate(bad, color=GONE, scale_factor=1.06), run_time=0.6)
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._breaks = VGroup(both, note)

    def _beat18(self):
        """Recognition signals."""
        with self.voiceover(text=BEATS[18]) as tr:
            swap_rails(self, headline("When to reach for it."),
                       caption("subarray or substring"))
            self.play(FadeOut(self._breaks, run_time=0.3))
            yes = VGroup(
                Text("✓  the word subarray or substring", font=MONO, font_size=BODY_FS,
                     color=GOOD),
                Text("✓  of size k, or longest such that", font=MONO, font_size=BODY_FS,
                     color=GOOD),
                Text("✓  smallest window meeting a target", font=MONO, font_size=BODY_FS,
                     color=GOOD),
                Text("✓  a count of qualifying runs", font=MONO, font_size=BODY_FS, color=GOOD),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            yes.move_to(stage_center(0.0))
            self.play(*[FadeIn(t, shift=RIGHT * 0.2) for t in yes],
                      lag_ratio=0.32, run_time=min(1.8, max(0.9, tr.duration * 0.45)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._recognise = yes

    def _beat19(self):
        """The anti-signal: one word decides it."""
        with self.voiceover(text=BEATS[19]) as tr:
            swap_rails(self, headline("Read one word very carefully."),
                       caption("subarray vs subsequence"))
            self.play(FadeOut(self._recognise, run_time=0.3))
            good = Text("subarray  ·  contiguous  ·  ✓  this pattern",
                        font=MONO, font_size=BODY_FS, color=GOOD)
            bad = Text("subsequence  ·  may skip  ·  ✗  not this pattern",
                       font=MONO, font_size=BODY_FS, color=GONE)
            both = VGroup(good, bad).arrange(DOWN, buff=0.65).move_to(stage_center(0.05))
            self.play(FadeIn(good, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(bad, shift=UP * 0.2), run_time=0.5)
            self.play(Indicate(bad, color=GONE, scale_factor=1.05), run_time=0.6)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._antisignal = both

    def _beat20(self):
        """The counter-tell: converging on sorted input is a different pattern."""
        with self.voiceover(text=BEATS[20]) as tr:
            swap_rails(self, headline("Sorted and converging? That is pattern one."),
                       caption("this one drags forward"))
            self.play(FadeOut(self._antisignal, run_time=0.3))
            other = chip("sorted  +  converge from both ends  →  two pointers",
                         color=PRIMARY, fs=BODY_FS)
            mine = chip("contiguous  +  drag left to right  →  sliding window",
                        color=ACCENT, fs=BODY_FS)
            both = VGroup(other, mine).arrange(DOWN, buff=0.55).move_to(stage_center(0.05))
            self.play(FadeIn(other, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(mine, shift=UP * 0.2), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._counter = both

    def _beat21(self):
        """Recall card."""
        with self.voiceover(text=BEATS[21]) as tr:
            swap_rails(self, headline("One window, two edges, one pass."),
                       caption("contiguous run  →  slide it"))
            self.play(FadeOut(self._counter, run_time=0.3))
            box = card(8.8, 1.55, color=ACCENT, fill=PANEL)
            box.move_to(stage_center(-0.05))
            top = Text("Sliding Window", font=MONO, font_size=32, color=ACCENT)
            sub = Text("O(n) time  ·  O(k) space  ·  contiguous only",
                       font=MONO, font_size=SMALL_FS, color=MUTED)
            VGroup(top, sub).arrange(DOWN, buff=0.24).move_to(box.get_center())
            self.play(FadeIn(box, scale=0.96), run_time=0.45)
            self.play(Write(top), run_time=0.5)
            self.play(FadeIn(sub), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))


__all__ = [
    "PATTERN_SLUG", "TITLE", "SUMMARY", "SCENE_CLASS", "POSTER_AT", "BEATS", "CHAPTERS",
    "SlidingWindow",
]
