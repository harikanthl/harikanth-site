"""
Pattern 04 — Kadane's Algorithm.

The film follows the card's own argument: hook -> the job (best run of neighbours, negatives
allowed) -> the brute force -> walking with a score -> the one question -> carry it or drop
it -> the two lines -> the walk, one element at a time, driven by a single ValueTracker ->
current versus best (the subtlety) -> why one comparison is enough -> complexity -> the seed
trap -> the all-negative array -> the three variations (products, one deletion, circular) ->
Kadane versus a sliding window -> the recall card.

Every number on screen is recomputed from the tracker that drives the walk, so the running
total, the live run, and the best-so-far bar are computed state rather than keyframes.
"""

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Circumscribe,
    Dot,
    FadeIn,
    FadeOut,
    Indicate,
    Line,
    MathTex,
    Text,
    ValueTracker,
    VGroup,
    Write,
    always_redraw,
)

from house import (
    ACCENT,
    BG,
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
from shots import ArrayRow, chip, window_over

PATTERN_SLUG = "kadane"
TITLE = "Kadane's Algorithm"
SUMMARY = "Extend the run or start fresh: best contiguous subarray in one O(n) pass."
SCENE_CLASS = "Kadane"
POSTER_AT = 66.0

NUMS = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
NEGS = [-3, -1, -2]
ROW_Y = 0.75
BAR_Y = 0.28

BEATS = [
    # 0 hook
    "For the best contiguous subarray, ask one question per element: extend, or start fresh?",
    # 1 the job
    "Here's the job. In this array, find the run of neighbours with the biggest total. "
    "Negatives allowed.",
    # 2 brute force
    "The slow way tries every start and every end, adding them up again. That is quadratic.",
    # 3 ELI5
    "Picture walking the array collecting a score. At every step you ask one question.",
    # 4 the question
    "Is what I am carrying actually helping me?",
    # 5 carry it or drop it
    "If the running total is positive, carry it. If it is negative, drop it and start fresh.",
    # 6 the two lines
    "One line does the work: current becomes the bigger of this element, or this element plus "
    "the carry. A second line remembers the best current ever seen.",
    # 7 the walk begins
    "Let's run it. Seed current and best with the first real element, never with zero.",
    # 8 first element
    "Minus two. Nothing carried yet, so current is minus two, and best is minus two.",
    # 9 start fresh
    "One. Extending gives minus one, starting fresh gives one. Fresh wins, so drop the carry.",
    # 10 carry the smaller loss
    "Minus three. Extending gives minus two, which beats minus three. Carry the smaller loss.",
    # 11 fresh again
    "Four, and extending gives two. Starting fresh is better again.",
    # 12 the climb
    "Then minus one, two, one. The run keeps extending, and current climbs to six.",
    # 13 the tail
    "Minus five drags it down to one, then four brings it to five. Best stays six.",
    # 14 current vs best
    "Here is the subtlety. Current is the best run ending exactly here. Best is the best run "
    "anywhere so far.",
    # 15 why it is correct
    "Why is that enough? Any best run ending here either extends the previous one, or starts "
    "here. One comparison covers both.",
    # 16 complexity
    "Linear time, constant space. Every problem in this pattern is one pass and a handful "
    "of variables.",
    # 17 the seed trap
    "The classic trap: seed with the first element, never with zero.",
    # 18 all negative
    "On minus three, minus one, minus two, the answer is minus one. Seeding zero would return "
    "zero, and an empty subarray is not allowed.",
    # 19 products
    "Variations. For products, carry the minimum as well, because a negative times a negative "
    "is a big positive.",
    # 20 one deletion and circular
    "With one deletion allowed, a second state spends the budget. For a circular array, the "
    "answer is the total minus the smallest run.",
    # 21 versus sliding window
    "And with negatives in the array, do not reach for a sliding window. It needs positives.",
    # 22 recall
    "One pass, one running total, one best.",
]

CHAPTERS = {
    0: "The hook",
    1: "The job",
    2: "Brute force",
    3: "The one question",
    6: "The two lines",
    7: "The walk",
    14: "Current versus best",
    15: "Why it is correct",
    16: "Complexity",
    17: "The seed trap",
    19: "The variations",
    21: "Kadane versus a window",
    22: "Recall",
}


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


def kadane_trace(nums):
    """The whole walk as computed state — what the tracker's frame reads.

    Each step records: the best run ENDING here (cur), the best run ANYWHERE so far (best),
    the live run's left edge, the best run's span, and whether this step started fresh.
    """
    cur = best = nums[0]
    lo = 0
    blo = bhi = 0
    rows = [dict(i=0, cur=cur, best=best, lo=lo, blo=blo, bhi=bhi, fresh=True, prev=None)]
    for i in range(1, len(nums)):
        x = nums[i]
        prev = cur
        fresh = x >= cur + x
        cur = x if fresh else cur + x
        if fresh:
            lo = i
        if cur > best:
            best, blo, bhi = cur, lo, i
        rows.append(dict(i=i, cur=cur, best=best, lo=lo, blo=blo, bhi=bhi,
                         fresh=fresh, prev=prev))
    return rows


def verdict(row) -> str:
    """The one comparison, spelled out in the card's own words."""
    if row["prev"] is None:
        return f"seed: current = best = {row['cur']}"
    i = row["i"]
    which = "start fresh here" if row["fresh"] else "extend the run"
    return f"max({NUMS[i]}, {row['prev']} + {NUMS[i]}) = {row['cur']}   →   {which}"


class Kadane(PrebakedVoiceMovingCameraScene):
    # ---------------------------------------------------------------------------- setup
    def construct(self):
        bg(self)
        for i in range(len(BEATS)):
            getattr(self, f"_beat{i}")()

    # ------------------------------------------------------------------------- walk shots
    def _frame(self, step):
        """The walk's state for the tracker's current frame — read live, never captured."""
        i = int(round(step.get_value()))
        rows = self.rows
        return rows[max(0, min(i, len(rows) - 1))]

    def _live_run(self, row, step):
        def _make():
            r = self._frame(step)
            return window_over(row, r["lo"], r["i"], color=WINDOW, opacity=0.20)

        return always_redraw(_make)

    def _live_best_bar(self, row, step):
        """The best run so far, drawn UNDER the row so it never fights the live run."""
        def _make():
            r = self._frame(step)
            left = row.cell(r["blo"]).get_left()[0] - 0.03
            right = row.cell(r["bhi"]).get_right()[0] + 0.03
            return Line([left, BAR_Y, 0], [right, BAR_Y, 0], color=GOOD, stroke_width=7)

        return always_redraw(_make)

    # ---------------------------------------------------------------------------- beats
    def _beat0(self):
        """Hook: the trade, named plainly before any notation."""
        with self.voiceover(text=BEATS[0]) as tr:
            swap_rails(self, headline("One question per element."),
                       caption("extend the run, or start fresh?"))
            bad = chip("try every start and end: n^2", color=GONE, fs=BODY_FS)
            good = chip("one pass: n", color=GOOD, fs=BODY_FS)
            row = VGroup(bad, good).arrange(RIGHT, buff=0.7).move_to(stage_center(0.15))
            note = Text("works even when the numbers go negative",
                        font=MONO, font_size=SMALL_FS, color=MUTED)
            note.move_to([0, -1.5, 0])
            self.play(FadeIn(bad, shift=UP * 0.2), run_time=0.5)
            self.wait(0.25)
            self.play(FadeIn(good, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._hook = VGroup(row, note)

    def _beat1(self):
        """The job: the array, and the words that name what we want."""
        with self.voiceover(text=BEATS[1]) as tr:
            swap_rails(self, headline("Biggest total of neighbours."),
                       caption("a contiguous run, negatives allowed"))
            self.play(FadeOut(self._hook, run_time=0.3))
            row = make_row(NUMS)
            tag = chip("contiguous  ·  at least one element", color=ACCENT, fs=BODY_FS)
            tag.move_to([0, 1.95, 0])
            note = Text("subarray means neighbours, not a subset", font=MONO,
                        font_size=SMALL_FS, color=MUTED)
            note.move_to([0, -1.55, 0])
            self.play(FadeIn(row.cells, shift=UP * 0.22), run_time=0.55)
            self.play(FadeIn(tag, scale=0.92), run_time=0.4)
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._job = VGroup(row.cells, tag, note)

    def _beat2(self):
        """Brute force, drawn as the nested pair of choices it is."""
        with self.voiceover(text=BEATS[2]) as tr:
            swap_rails(self, headline("Every start, every end, added again."),
                       caption("n x n additions = quadratic"))
            self.play(FadeOut(self._job, run_time=0.3))
            code = VGroup(
                Text("for start in range(n):", font=MONO, font_size=BODY_FS, color=MUTED),
                Text("→  for end in range(start, n):", font=MONO, font_size=BODY_FS, color=MUTED),
                Text("→  →  total = sum(nums[start:end + 1])", font=MONO, font_size=BODY_FS,
                     color=GONE),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.36)
            box = card(code.width + 1.0, code.height + 0.9, color=STROKE, fill=PANEL)
            box.move_to(stage_center(0.0))
            code.move_to(box.get_center())
            tag = Text("n x n additions", font=MONO, font_size=SMALL_FS, color=GONE)
            tag.move_to([0, -2.3, 0])
            self.play(FadeIn(box), run_time=0.35)
            self.play(Write(code), run_time=min(1.5, max(0.8, tr.duration * 0.35)))
            self.play(FadeIn(tag, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._brute = VGroup(box, code, tag)

    def _beat3(self):
        """ELI5: walking the array with a score in your hands."""
        with self.voiceover(text=BEATS[3]) as tr:
            swap_rails(self, headline("Walk it once, carrying a score."),
                       caption("one element at a time"))
            self.play(FadeOut(self._brute, run_time=0.3))
            row = make_row(NUMS, y=0.7)
            self.p3 = ValueTracker(0.0)
            self.add(self.p3)
            walker = always_redraw(
                lambda: Dot(row.cell(int(round(self.p3.get_value()))).get_top() + UP * 0.42,
                            radius=0.14, color=ACCENT).set_stroke(BG, width=2.2)
            )
            note = Text("the score in your hands is the running total",
                        font=MONO, font_size=SMALL_FS, color=MUTED)
            note.move_to([0, -1.6, 0])
            self.play(FadeIn(row.cells, shift=UP * 0.22), run_time=0.5)
            self.play(FadeIn(walker), run_time=0.3)
            self.play(self.p3.animate.set_value(8.0),
                      run_time=min(2.0, max(1.0, tr.duration * 0.4)))
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._walk3 = VGroup(row.cells, walker, note)

    def _beat4(self):
        """The one question, isolated."""
        with self.voiceover(text=BEATS[4]) as tr:
            swap_rails(self, headline("Ask one question at every step."),
                       caption("does the carry help, or hurt?"))
            kill(self, *self._walk3.submobjects, run_time=0.3)
            q = Text("is what I am carrying helping me?", font=MONO, font_size=30, color=INK)
            q.move_to([0, 0.75, 0])
            yes = chip("helps  →  extend the run", color=GOOD, fs=BODY_FS)
            no = chip("hurts  →  drop it, start here", color=GONE, fs=BODY_FS)
            both = VGroup(yes, no).arrange(DOWN, buff=0.5).move_to([0, -0.85, 0])
            self.play(Write(q), run_time=min(1.1, max(0.6, tr.duration * 0.28)))
            self.play(FadeIn(yes, shift=UP * 0.2), run_time=0.45)
            self.play(FadeIn(no, shift=UP * 0.2), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._question = VGroup(q, both)

    def _beat5(self):
        """The rule in plain words."""
        with self.voiceover(text=BEATS[5]) as tr:
            swap_rails(self, headline("Positive carry: keep it. Negative: drop it."),
                       caption("one comparison per element"))
            self.play(FadeOut(self._question, run_time=0.3))
            keep = chip("carry is positive  →  add this element", color=GOOD, fs=BODY_FS)
            drop = chip("carry is negative  →  start fresh here", color=GONE, fs=BODY_FS)
            both = VGroup(keep, drop).arrange(DOWN, buff=0.6).move_to(stage_center(0.05))
            self.play(FadeIn(keep, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(drop, shift=UP * 0.2), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._rule = both

    def _beat6(self):
        """The two lines of code, named as the two quantities they are."""
        with self.voiceover(text=BEATS[6]) as tr:
            swap_rails(self, headline("Two lines do all the work."),
                       caption("one holds the run, one holds the record"))
            self.play(FadeOut(self._rule, run_time=0.3))
            line1 = Text("current = max(x, current + x)", font=MONO, font_size=26, color=ACCENT)
            line2 = Text("best = max(best, current)", font=MONO, font_size=26, color=GOOD)
            tag1 = Text("the run ending here", font=MONO, font_size=SMALL_FS, color=MUTED)
            tag2 = Text("the best run anywhere so far", font=MONO, font_size=SMALL_FS, color=MUTED)
            g1 = VGroup(line1, tag1).arrange(DOWN, buff=0.22)
            g2 = VGroup(line2, tag2).arrange(DOWN, buff=0.22)
            code = VGroup(g1, g2).arrange(DOWN, buff=0.85).move_to(stage_center(0.0))
            box = card(9.6, 3.0, color=STROKE, fill=PANEL).move_to(code.get_center())
            self.play(FadeIn(box), run_time=0.35)
            self.play(Write(line1), run_time=min(1.0, max(0.5, tr.duration * 0.22)))
            self.play(FadeIn(tag1), run_time=0.3)
            self.play(Write(line2), run_time=min(1.0, max(0.5, tr.duration * 0.22)))
            self.play(FadeIn(tag2), run_time=0.3)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._twolines = VGroup(box, code)

    def _beat7(self):
        """The walk is set up: the row, the seed, and the three live readouts."""
        with self.voiceover(text=BEATS[7]) as tr:
            swap_rails(self, headline("Seed with the first element."),
                       caption("never seed with zero"))
            self.play(FadeOut(self._twolines, run_time=0.3))
            self.row = make_row(NUMS)
            self.rows = kadane_trace(NUMS)
            self.step = ValueTracker(0.0)
            self.add(self.step)
            self.run_rect = self._live_run(self.row, self.step)
            self.best_bar = self._live_best_bar(self.row, self.step)
            self.cur_t = live_text(
                lambda: f"current = {self._frame(self.step)['cur']}",
                [-2.6, -0.9, 0], color=ACCENT,
            )
            self.best_t = live_text(
                lambda: f"best = {self._frame(self.step)['best']}",
                [2.6, -0.9, 0], color=GOOD,
            )
            self.verdict = live_text(
                lambda: verdict(self._frame(self.step)),
                [0, -1.75, 0], color=WINDOW,
            )
            legend = Text("current run", font=MONO, font_size=SMALL_FS, color=WINDOW)
            legend.move_to([0, -2.45, 0])
            self.add(self.cur_t, self.best_t, self.verdict)
            self.play(FadeIn(self.row.cells, shift=UP * 0.22), run_time=0.55)
            self.play(FadeIn(self.run_rect), FadeIn(self.best_bar), FadeIn(self.cur_t),
                      FadeIn(self.best_t), FadeIn(self.verdict), FadeIn(legend), run_time=0.6)
            self.play(*self.row.focus(0, color=ACCENT), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._legend = legend

    def _advance(self, index, runtime):
        """One step of the walk: move the tracker, move the highlight, leave nothing behind."""
        anims = [self.step.animate.set_value(float(index)),
                 *self.row.focus(index, color=ACCENT)]
        if index > 0:
            anims += self.row.reset(index - 1)
        self.play(*anims, run_time=runtime)

    def _beat8(self):
        """First element: seed both quantities with it."""
        with self.voiceover(text=BEATS[8]) as tr:
            swap_rails(self, headline("Minus two is the whole run so far."),
                       caption("current = best = -2"))
            self.play(Indicate(self.row.cell(0), color=ACCENT, scale_factor=1.14), run_time=0.6)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))

    def _beat9(self):
        """Start fresh: the carry was hurting."""
        with self.voiceover(text=BEATS[9]) as tr:
            swap_rails(self, headline("Extending gives minus one. Fresh gives one."),
                       caption("fresh wins — drop the carry"))
            self._advance(1, min(1.3, max(0.7, tr.duration * 0.3)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat10(self):
        """Carry the smaller loss."""
        with self.voiceover(text=BEATS[10]) as tr:
            swap_rails(self, headline("Carry the smaller loss."),
                       caption("minus two beats minus three"))
            self._advance(2, min(1.3, max(0.7, tr.duration * 0.3)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat11(self):
        """Fresh again, and now the run is positive."""
        with self.voiceover(text=BEATS[11]) as tr:
            swap_rails(self, headline("Starting fresh wins again."),
                       caption("four beats two"))
            self._advance(3, min(1.3, max(0.7, tr.duration * 0.3)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat12(self):
        """The climb: the run extends three times and current reaches six."""
        with self.voiceover(text=BEATS[12]) as tr:
            swap_rails(self, headline("Now the run just keeps extending."),
                       caption("current climbs to six"))
            self._advance(4, min(1.0, max(0.6, tr.duration * 0.22)))
            self.play(self.step.animate.set_value(6.0),
                      *self.row.focus(6, color=ACCENT), *self.row.reset(4),
                      run_time=min(1.4, max(0.7, tr.duration * 0.3)))
            self.play(Circumscribe(self.row.cells[3:7], color=GOOD), run_time=0.7)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))

    def _beat13(self):
        """The tail: the carry dips, but the record stands."""
        with self.voiceover(text=BEATS[13]) as tr:
            swap_rails(self, headline("The tail drags current down. Best stands."),
                       caption("best stays six"))
            self.play(self.step.animate.set_value(7.0),
                      *self.row.focus(7, color=ACCENT), *self.row.reset(6),
                      run_time=min(1.0, max(0.6, tr.duration * 0.22)))
            self.play(self.step.animate.set_value(8.0),
                      *self.row.focus(8, color=ACCENT), *self.row.reset(7),
                      run_time=min(1.0, max(0.6, tr.duration * 0.22)))
            self.play(Indicate(self.best_bar, color=GOOD, scale_factor=1.0), run_time=0.6)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat14(self):
        """Current versus best — the two quantities, read off the picture that is already up."""
        with self.voiceover(text=BEATS[14]) as tr:
            swap_rails(self, headline("Two different quantities."),
                       caption("ending here  vs  anywhere so far"))
            self.play(FadeOut(self.verdict), FadeOut(self._legend, run_time=0.3))
            self.verdict = None
            one = Text("current: the best run ENDING exactly here",
                       font=MONO, font_size=SMALL_FS, color=ACCENT)
            two = Text("best: the best run ANYWHERE so far",
                       font=MONO, font_size=SMALL_FS, color=GOOD)
            stack = VGroup(one, two).arrange(DOWN, buff=0.34).move_to([0, -1.85, 0])
            self.play(FadeIn(one, shift=UP * 0.12), run_time=0.45)
            self.play(FadeIn(two, shift=UP * 0.12), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._vs = stack

    def _beat15(self):
        """Why one comparison is enough: the two ways a run can end here."""
        with self.voiceover(text=BEATS[15]) as tr:
            swap_rails(self, headline("Why one comparison is enough."),
                       caption("extends the old run, or starts here"))
            kill(self, self.run_rect, self.best_bar, self.cur_t, self.best_t, self._vs,
                 run_time=0.35)
            self.play(FadeOut(self.row.cells, run_time=0.3))
            a = chip("extend: it came from the run before it", color=ACCENT, fs=BODY_FS)
            b = chip("start: it begins right here", color=PRIMARY, fs=BODY_FS)
            both = VGroup(a, b).arrange(DOWN, buff=0.5).move_to([0, 0.55, 0])
            concl = Text("max of those two covers every possibility",
                         font=MONO, font_size=SMALL_FS, color=GOOD)
            concl.move_to([0, -1.3, 0])
            self.play(FadeIn(a, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(b, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(concl, shift=UP * 0.12), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._why = VGroup(both, concl)

    def _beat16(self):
        """Complexity, stated cold."""
        with self.voiceover(text=BEATS[16]) as tr:
            swap_rails(self, headline("Linear time, constant space."),
                       caption("one pass, a few variables"))
            self.play(FadeOut(self._why, run_time=0.3))
            slow = VGroup(
                Text("try every run", font=MONO, font_size=BODY_FS, color=GONE),
                MathTex(r"O(n^2)", color=GONE).scale(1.25),
            ).arrange(DOWN, buff=0.26)
            fast = VGroup(
                Text("kadane", font=MONO, font_size=BODY_FS, color=GOOD),
                MathTex(r"O(n)", color=GOOD).scale(1.25),
            ).arrange(DOWN, buff=0.26)
            both = VGroup(slow, fast).arrange(RIGHT, buff=1.9).move_to(stage_center(-0.05))
            arrow = Text("→", font=MONO, font_size=44, color=MUTED)
            arrow.move_to((slow.get_right() + fast.get_left()) / 2)
            space = Text("space O(1)  ·  if you need an array, you have over-thought it",
                         font=MONO, font_size=SMALL_FS, color=GOOD)
            space.move_to([0, -2.2, 0])
            self.play(FadeIn(slow), run_time=0.45)
            self.play(FadeIn(arrow), run_time=0.3)
            self.play(FadeIn(fast), run_time=0.45)
            self.play(FadeIn(space, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._cost = VGroup(both, arrow, space)

    def _beat17(self):
        """The seed trap, named as the bug it is."""
        with self.voiceover(text=BEATS[17]) as tr:
            swap_rails(self, headline("Never seed with zero."),
                       caption("seed with the first element"))
            self.play(FadeOut(self._cost, run_time=0.3))
            bad = Text("best = current = 0", font=MONO, font_size=32, color=GONE)
            bad.move_to([0, 0.6, 0])
            good = Text("best = current = nums[0]", font=MONO, font_size=32, color=GOOD)
            good.move_to([0, -0.7, 0])
            note = Text("this is the most common Kadane mistake there is",
                        font=MONO, font_size=SMALL_FS, color=MUTED)
            note.move_to([0, -2.0, 0])
            self.play(Write(bad), run_time=0.6)
            self.play(Write(good), run_time=0.6)
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._seed = VGroup(bad, good, note)

    def _beat18(self):
        """The all-negative array, where the wrong seed is visibly wrong."""
        with self.voiceover(text=BEATS[18]) as tr:
            swap_rails(self, headline("All negative? The seed decides the answer."),
                       caption("an empty subarray is not allowed"))
            self.play(FadeOut(self._seed, run_time=0.3))
            row = make_row(NEGS, y=1.0, cell=0.75, fs=28)
            right = Text("correct: best = -1", font=MONO, font_size=26, color=GOOD)
            right.move_to([0, -0.7, 0])
            wrong = Text("seeded with 0: best = 0", font=MONO, font_size=26, color=GONE)
            wrong.move_to([0, -1.55, 0])
            note = Text("zero would be a subarray that does not exist",
                        font=MONO, font_size=SMALL_FS, color=MUTED)
            note.move_to([0, -2.35, 0])
            self.play(FadeIn(row.cells, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(right, shift=UP * 0.12), run_time=0.4)
            self.play(FadeIn(wrong, shift=UP * 0.12), run_time=0.4)
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.play(*row.mark_good(1), run_time=0.6)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._neg = VGroup(row.cells, right, wrong, note)

    def _beat19(self):
        """Variation one: products need a second state."""
        with self.voiceover(text=BEATS[19]) as tr:
            swap_rails(self, headline("For products, carry the minimum too."),
                       caption("a negative flips the roles"))
            self.play(FadeOut(self._neg, run_time=0.3))
            hi = Text("hi = max(x, hi * x)", font=MONO, font_size=28, color=GOOD)
            lo = Text("lo = min(x, lo * x)", font=MONO, font_size=28, color=ACCENT)
            stack = VGroup(hi, lo).arrange(DOWN, buff=0.55).move_to([0, 0.65, 0])
            note = Text("today's worst can be tomorrow's best", font=MONO,
                        font_size=SMALL_FS, color=MUTED)
            note.move_to([0, -1.15, 0])
            warn = Text("if x < 0, swap hi and lo first", font=MONO, font_size=SMALL_FS,
                        color=WINDOW)
            warn.move_to([0, -1.9, 0])
            self.play(Write(hi), run_time=0.6)
            self.play(Write(lo), run_time=0.6)
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.play(FadeIn(warn, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._products = VGroup(stack, note, warn)

    def _beat20(self):
        """Variations two and three: a spent budget, and the wrap."""
        with self.voiceover(text=BEATS[20]) as tr:
            swap_rails(self, headline("One deletion, and the circular case."),
                       caption("a second state, then total minus min"))
            self.play(FadeOut(self._products, run_time=0.3))
            a = chip("one deletion  →  a second state that spent it", color=ACCENT,
                     fs=BODY_FS)
            b = chip("circular  →  total − smallest run", color=PRIMARY, fs=BODY_FS)
            both = VGroup(a, b).arrange(DOWN, buff=0.55).move_to([0, 0.55, 0])
            guard = Text("guard: if everything is negative, that complement is empty",
                         font=MONO, font_size=SMALL_FS, color=GONE)
            guard.move_to([0, -1.45, 0])
            self.play(FadeIn(a, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(b, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(guard, shift=UP * 0.12), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._vars = VGroup(both, guard)

    def _beat21(self):
        """The distinction the card wants ready: Kadane versus a sliding window."""
        with self.voiceover(text=BEATS[21]) as tr:
            swap_rails(self, headline("Negatives? Do not use a sliding window."),
                       caption("a window needs all positives"))
            self.play(FadeOut(self._vars, run_time=0.3))
            win = chip("sliding window  →  all positive values", color=GONE, fs=BODY_FS)
            kad = chip("kadane  →  works with negatives", color=GOOD, fs=BODY_FS)
            both = VGroup(win, kad).arrange(DOWN, buff=0.55).move_to(stage_center(0.05))
            tell = Text("notice the sign of the input before you choose",
                        font=MONO, font_size=SMALL_FS, color=MUTED)
            tell.move_to([0, -2.2, 0])
            self.play(FadeIn(win, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(kad, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(tell, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._counter = VGroup(both, tell)

    def _beat22(self):
        """Recall card."""
        with self.voiceover(text=BEATS[22]) as tr:
            swap_rails(self, headline("One pass, one total, one record."),
                       caption("extend it, or restart it"))
            self.play(FadeOut(self._counter, run_time=0.3))
            box = card(8.8, 1.55, color=ACCENT, fill=PANEL)
            box.move_to(stage_center(-0.05))
            top = Text("Kadane's Algorithm", font=MONO, font_size=32, color=ACCENT)
            sub = Text("O(n) time  ·  O(1) space  ·  negatives welcome",
                       font=MONO, font_size=SMALL_FS, color=MUTED)
            VGroup(top, sub).arrange(DOWN, buff=0.24).move_to(box.get_center())
            self.play(FadeIn(box, scale=0.96), run_time=0.45)
            self.play(Write(top), run_time=0.5)
            self.play(FadeIn(sub), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))


__all__ = [
    "PATTERN_SLUG", "TITLE", "SUMMARY", "SCENE_CLASS", "POSTER_AT", "BEATS", "CHAPTERS",
    "Kadane",
]
