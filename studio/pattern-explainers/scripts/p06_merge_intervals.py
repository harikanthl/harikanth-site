"""
Pattern 06 — Merge Intervals.

The film follows the card's own argument: hook -> the job -> the six relative positions and
the quadratic pair check -> the sort that kills the mirrors -> the one surviving question ->
the sweep that holds one interval -> extend (and the `max` that must not be forgotten) ->
the gap that flushes -> why it's correct -> closed versus half-open -> complexity and the
pre-sorted shortcut -> the two other shapes -> recognition -> what breaks it -> the recall
card.

Narration lives in BEATS and the animation is written against `tracker.duration`, so the
picture and the voice cannot drift: one file is the single source of truth for both.
"""

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    DashedLine,
    FadeIn,
    FadeOut,
    Indicate,
    Line,
    MathTex,
    Restore,
    RoundedRectangle,
    Text,
    ValueTracker,
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
    stage_center,
    swap_rails,
)
from prebaked_voice import PrebakedVoiceMovingCameraScene
from shots import chip

PATTERN_SLUG = "merge-intervals"
TITLE = "Merge Intervals"
SUMMARY = "Sort by start time and every interval only ever has to meet the one you're holding."
SCENE_CLASS = "MergeIntervals"
POSTER_AT = 36.0

# The timeline: six intervals as given (unsorted), and where each one lands after the sort.
IN = [(6, 8), (2, 5), (1, 4), (7, 10), (11, 12), (2, 3)]
LANE_OF = [3, 1, 0, 4, 5, 2]        # sorted position of IN bar i
BAR_IN_LANE = [2, 1, 5, 0, 3, 4]    # after sorting, lane j holds IN bar BAR_IN_LANE[j]
MERGED = [(1, 5), (6, 10), (11, 12)]

LO, HI = 1, 12
LEN = 9.4
X_CENTER = -0.5
Y_TOP = 1.62
BAR_H = 0.28
LANE_GAP = 0.11
OUT_Y = -0.98
OUT_H = 0.32
AXIS_Y = -1.42
READOUT_Y = -2.05
RULE_Y = -2.55


class Lanes:
    """Interval bars on one shared time axis, one lane per interval, addressed by index."""

    def __init__(self, intervals, *, length=LEN, x_center=X_CENTER, y_top=Y_TOP,
                 bar_h=BAR_H, gap=LANE_GAP, color=PRIMARY):
        self.lo = min(s for s, _ in intervals)
        self.hi = max(e for _, e in intervals)
        self.scale = length / max(self.hi - self.lo, 1)
        self.x_left = x_center - length / 2
        self.bar_h = bar_h
        self.gap = gap
        self.y_top = y_top
        self.spans = list(intervals)
        self.bars = VGroup()
        for i, (s, e) in enumerate(self.spans):
            self.bars.add(self._rect(s, e, color=color).move_to([self.x_of((s + e) / 2), self.lane_y(i), 0]))
        self.group = self.bars

    def x_of(self, t: float) -> float:
        return self.x_left + (t - self.lo) * self.scale

    def lane_y(self, i: int) -> float:
        return self.y_top - i * (self.bar_h + self.gap) - self.bar_h / 2

    def _rect(self, s, e, *, color=PRIMARY, opacity: float = 0.5, h: float | None = None):
        return RoundedRectangle(
            corner_radius=0.06,
            width=max(0.16, (e - s) * self.scale),
            height=self.bar_h if h is None else h,
            stroke_color=color,
            stroke_width=1.8,
            fill_color=color,
            fill_opacity=opacity,
        )

    def bar(self, i: int):
        return self.bars[i]


def mini_axis(lo, hi, *, y, x0, unit, color=STROKE):
    """A second, smaller number line for the variant shapes. Returns (x_of, mobject)."""

    def x_of(t):
        return x0 + (t - lo) * unit

    g = VGroup(Line([x_of(lo), y, 0], [x_of(hi), y, 0], color=color, stroke_width=2))
    for t in range(lo, hi + 1):
        g.add(Line([x_of(t), y - 0.06, 0], [x_of(t), y + 0.06, 0], color=color, stroke_width=1.4))
        g.add(Text(str(t), font=MONO, font_size=16, color=MUTED).move_to([x_of(t), y - 0.26, 0]))
    return x_of, g


def mini_bar(x_of, s, e, *, y, h=0.3, color=PRIMARY, opacity=0.5):
    unit = x_of(1) - x_of(0)
    r = RoundedRectangle(
        corner_radius=0.05,
        width=max(0.16, (e - s) * unit),
        height=h,
        stroke_color=color,
        stroke_width=1.8,
        fill_color=color,
        fill_opacity=opacity,
    )
    r.move_to([x_of((s + e) / 2), y, 0])
    return r


BEATS = [
    # 0 hook
    "Sorting by start time is the whole algorithm.",
    # 1 the job
    "Here's the job: merge every overlapping meeting into one busy block.",
    # 2 six ways, and the pair check
    "Two intervals can sit six ways, and four of those are the same case flipped. Checking pairs is quadratic.",
    # 3 the sort
    "So sort by start time. The first interval always begins first, and the mirror images vanish.",
    # 4 one question left
    "One question is left: does the next interval start before this one ends?",
    # 5 the sweep
    "Everything after the sort is a single left-to-right sweep, carrying one interval.",
    # 6 hold the first
    "Hold the first interval. It is the block we're building.",
    # 7 extend
    "The next one starts inside it, so extend the end to whichever end is later.",
    # 8 max, not end
    "A short interval inside a long one would shrink the block. Take the maximum, never the new end.",
    # 9 the gap
    "When the next start is past our end, that's a real gap. Emit the block, and start a fresh one.",
    # 10 keep sweeping
    "Keep sweeping. Every interval is compared once, with the one we're holding.",
    # 11 done
    "Six intervals in, three merged blocks out. Every block is disjoint, and in order.",
    # 12 why correct
    "Why is it correct? The held end is the furthest right we've reached, so anything starting before it touches us.",
    # 13 the convention
    "First decide one thing: do touching intervals merge? Closed means yes; half-open means the room emptied.",
    # 14 the disagreement
    "Merging schedules and counting rooms genuinely disagree, and both are right. Say which you assume.",
    # 15 complexity
    "The sort costs n log n and dominates. The sweep after it is linear, and the output is linear space.",
    # 16 pre-sorted
    "Already sorted? Skip the sort, that's linear. Both lists sorted? Linear in both, constant extra.",
    # 17 shape two
    "Second shape: two sorted lists. Intersect with the later start and the earlier end, then advance the earlier end.",
    # 18 shape three
    "Third shape: stop merging and count. A heap of end times says what has already finished.",
    # 19 the peak
    "The heap's size is how many overlap right now, and the peak is the answer. A plus-one, minus-one sweep is the same thing.",
    # 20 recognise
    "Recognise it by pairs of start and end, and words like merge, overlap, conflict, or free time.",
    # 21 what breaks it
    "What breaks it: forgetting the maximum, and the wrong convention.",
    # 22 recall
    "Sort by start, hold one interval, extend with the max.",
]

CHAPTERS = {
    0: "The hook",
    1: "The job",
    2: "Six ways to sit",
    3: "Sort is the algorithm",
    4: "One question left",
    6: "Hold one interval",
    8: "Max, never the new end",
    9: "Gaps flush blocks",
    11: "Six in, three out",
    12: "Why it's correct",
    13: "Closed or half-open",
    15: "Complexity",
    17: "The three shapes",
    18: "Counting, not merging",
    20: "How to recognise it",
    22: "Recall",
}


class MergeIntervals(PrebakedVoiceMovingCameraScene):
    # ---------------------------------------------------------------------------- setup
    def construct(self):
        bg(self)
        self.lanes = Lanes(IN)
        self.axis = self._axis()
        self.axis_label = Text("input", font=MONO, font_size=SMALL_FS, color=MUTED)
        self.axis_label.move_to([4.45, 0.53, 0], aligned_edge=LEFT)
        self.out_label = Text("merged", font=MONO, font_size=SMALL_FS, color=MUTED)
        self.out_label.move_to([4.45, OUT_Y, 0], aligned_edge=LEFT)
        self.sorted_bars = None
        self.held = None
        self.held_tr = None
        self.held_color = ACCENT
        self.merged_bars = []
        for i in range(len(BEATS)):
            getattr(self, f"_beat{i}")()

    # ------------------------------------------------------------------------- utilities
    def _axis(self):
        ax = Line(
            [self.lanes.x_of(LO) - 0.12, AXIS_Y, 0],
            [self.lanes.x_of(HI) + 0.12, AXIS_Y, 0],
            color=STROKE,
            stroke_width=2,
        )
        g = VGroup(ax)
        for t in range(LO, HI + 1):
            x = self.lanes.x_of(t)
            g.add(Line([x, AXIS_Y - 0.07, 0], [x, AXIS_Y + 0.07, 0], color=STROKE, stroke_width=1.4))
            g.add(Text(str(t), font=MONO, font_size=16, color=MUTED).move_to([x, AXIS_Y - 0.28, 0]))
        return g

    def _timeline(self):
        return VGroup(self.lanes.bars, self.axis, self.axis_label, self.out_label)

    def _fade(self, *mobs, run_time: float = 0.3):
        live = [m for m in mobs if m is not None]
        if live:
            self.play(*[FadeOut(m, run_time=run_time) for m in live])

    def _readout_text(self, s, e, color=ACCENT):
        return Text(f"held = [{s}, {e}]", font=MONO, font_size=BODY_FS, color=color).move_to(
            [-0.4, READOUT_Y, 0]
        )

    def _rule_text(self, text, color=MUTED):
        return Text(text, font=MONO, font_size=16, color=color).move_to([-0.9, RULE_Y, 0])

    def _swap_readout(self, s, e, color=ACCENT, run_time=0.35):
        new = self._readout_text(s, e, color)
        old = getattr(self, "_readout", None)
        if old is None:
            self.play(FadeIn(new), run_time=run_time)
        else:
            self.play(FadeOut(old), FadeIn(new), run_time=run_time)
        self._readout = new

    def _held_from(self, bar, s, e):
        """Make `bar` the running merged interval, sized by computed state (a ValueTracker)."""
        tr = ValueTracker(e)
        self.add(tr)
        self.held_tr = tr
        self.held_color = ACCENT
        scale = self.lanes.scale

        def upd(m):
            e_now = tr.get_value()
            new = RoundedRectangle(
                corner_radius=0.06,
                width=max(0.18, (e_now - s) * scale),
                height=OUT_H,
                stroke_color=self.held_color,
                stroke_width=2.6,
                fill_color=self.held_color,
                fill_opacity=0.45,
            )
            new.move_to([self.lanes.x_of((s + e_now) / 2), OUT_Y, 0])
            m.become(new)

        bar.add_updater(upd)
        upd(bar)
        self.held = bar
        return bar

    def _to_merged_lane(self, bar, mid, color=ACCENT):
        return bar.animate.move_to([self.lanes.x_of(mid), OUT_Y, 0]).set_stroke(
            color, width=2.6
        ).set_fill(color, opacity=0.45)

    def _consume(self, bar):
        return [
            bar.animate.set_stroke(MUTED, width=1.2).set_fill(MUTED, opacity=0.12)
        ]

    def _flush_held(self, *, run_time: float = 0.45):
        """Freeze the running interval: it becomes an emitted, disjoint merged block."""
        self.held.clear_updaters()
        self.merged_bars.append(self.held)
        self.play(
            self.held.animate.set_stroke(GOOD, width=2.6).set_fill(GOOD, opacity=0.45),
            run_time=run_time,
        )

    # ---------------------------------------------------------------------------- beats
    def _beat0(self):
        """Hook: the trade, stated as two costs."""
        with self.voiceover(text=BEATS[0]) as tr:
            swap_rails(
                self, headline("The sort is the algorithm."), caption("O(n^2)  ->  O(n log n)")
            )
            bad = chip("every pair: n^2", color=GONE, fs=BODY_FS)
            good = chip("sort + one sweep: n log n", color=GOOD, fs=BODY_FS)
            row = VGroup(bad, good).arrange(RIGHT, buff=0.7).move_to(stage_center(-0.2))
            self.play(FadeIn(bad, shift=UP * 0.2), run_time=0.5)
            self.wait(0.25)
            self.play(FadeIn(good, shift=UP * 0.2), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._hook = row

    def _beat1(self):
        """The job: six intervals, as given, on one shared time line."""
        with self.voiceover(text=BEATS[1]) as tr:
            swap_rails(
                self, headline("Merge the overlapping meetings."), caption("pairs of [start, end]")
            )
            self._fade(self._hook)
            self.play(
                FadeIn(self.lanes.bars, shift=UP * 0.2),
                FadeIn(self.axis),
                FadeIn(self.axis_label),
                FadeIn(self.out_label),
                run_time=min(1.4, max(0.8, tr.duration * 0.35)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat2(self):
        """Six relative positions, four of them mirrors — and the pair check they force."""
        with self.voiceover(text=BEATS[2]) as tr:
            swap_rails(
                self, headline("Six ways to sit, four of them mirrors."), caption("checking pairs is quadratic")
            )
            self._fade(self._timeline(), run_time=0.35)
            unit = 1.15
            x0 = -3.0
            rows = VGroup()
            for y, (a, b) in zip(
                (1.35, 0.45, -0.45),
                (((0, 1.4), (1.8, 2.8)), ((0, 1.5), (1.0, 2.6)), ((0, 2.8), (0.7, 1.6))),
            ):
                for (s, e), col in ((a, PRIMARY), (b, ACCENT)):
                    r = RoundedRectangle(
                        corner_radius=0.05,
                        width=max(0.2, (e - s) * unit),
                        height=0.3,
                        stroke_color=col,
                        stroke_width=1.8,
                        fill_color=col,
                        fill_opacity=0.45,
                    )
                    r.move_to([x0 + ((s + e) / 2) * unit, y, 0])
                    rows.add(r)
            labels = VGroup(
                Text("apart", font=MONO, font_size=SMALL_FS, color=INK),
                Text("overlap", font=MONO, font_size=SMALL_FS, color=INK),
                Text("one holds the other", font=MONO, font_size=SMALL_FS, color=INK),
            )
            for lb, y in zip(labels, (1.35, 0.45, -0.45)):
                lb.move_to([x0 - 0.35, y, 0], aligned_edge=RIGHT)
            note = Text(
                "plus their three mirror images  =  six positions", font=MONO,
                font_size=SMALL_FS, color=MUTED,
            )
            note.move_to([-0.6, -1.6, 0])
            tag = chip("checking pairs: n^2", color=GONE, fs=SMALL_FS)
            tag.move_to([3.1, -0.45, 0])
            self.play(FadeIn(rows), FadeIn(labels), run_time=0.5)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.play(FadeIn(tag, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._cases = VGroup(rows, labels, note, tag)

    def _beat3(self):
        """The sort: bars keep their horizontal place and slot into start order."""
        with self.voiceover(text=BEATS[3]) as tr:
            swap_rails(
                self, headline("Sort by start; the mirrors vanish."), caption("sorting is the algorithm")
            )
            self._fade(self._cases, run_time=0.35)
            tag = Text("sorted by start", font=MONO, font_size=SMALL_FS, color=GOOD)
            tag.move_to([-0.4, 2.3, 0])
            self.play(
                FadeIn(self.lanes.bars),
                FadeIn(self.axis),
                FadeIn(self.axis_label),
                FadeIn(self.out_label),
                run_time=0.45,
            )
            self.play(FadeIn(tag), run_time=0.3)
            self.play(
                *[
                    self.lanes.bar(i).animate.move_to(
                        [self.lanes.x_of(sum(IN[i]) / 2), self.lanes.lane_y(LANE_OF[i]), 0]
                    )
                    for i in range(len(IN))
                ],
                run_time=min(1.8, max(1.0, tr.duration * 0.4)),
            )
            self.sorted_bars = [self.lanes.bar(i) for i in BAR_IN_LANE]
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._sort_tag = tag

    def _beat4(self):
        """The one question the sort leaves behind."""
        with self.voiceover(text=BEATS[4]) as tr:
            swap_rails(
                self, headline("Does the next one start before this ends?"), caption("b.start <= a.end")
            )
            a, b = self.sorted_bars[0], self.sorted_bars[1]
            rule = self._rule_text("overlap   <=>   b.start <= a.end", color=GOOD)
            line = DashedLine(
                [self.lanes.x_of(4), 1.78, 0],
                [self.lanes.x_of(4), -0.66, 0],
                color=WINDOW,
                stroke_width=2.6,
                dash_length=0.09,
            )
            self.play(
                a.animate.set_stroke(ACCENT, width=2.6).set_fill(ACCENT, opacity=0.5),
                b.animate.set_stroke(WINDOW, width=2.6).set_fill(WINDOW, opacity=0.5),
                run_time=0.5,
            )
            self.play(FadeIn(line), run_time=0.4)
            self.play(Write(rule), run_time=min(1.1, max(0.5, tr.duration * 0.3)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._rule = rule
            self._dash = line

    def _beat5(self):
        """The whole algorithm after the sort is one sweep."""
        with self.voiceover(text=BEATS[5]) as tr:
            swap_rails(
                self, headline("After the sort, one sweep."), caption("carry one interval")
            )
            self._fade(self._dash, self._rule)
            note = self._rule_text(
                "if s <= held_end:   held_end = max(held_end, e)", color=INK
            )
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.45)
            self.play(
                Indicate(self.sorted_bars[0], color=ACCENT, scale_factor=1.08),
                run_time=min(1.2, max(0.6, tr.duration * 0.3)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._rule2 = note

    def _beat6(self):
        """The first interval becomes the block we hold, on the merged lane."""
        with self.voiceover(text=BEATS[6]) as tr:
            swap_rails(self, headline("Hold the first interval."), caption("the block being built"))
            self._fade(self._rule, self._rule2)
            self._fade(self._sort_tag)
            first = self.sorted_bars[0]
            self.play(
                self._to_merged_lane(first, 2.5),
                run_time=min(1.0, max(0.55, tr.duration * 0.25)),
            )
            self._held_from(first, 1, 4)
            self._swap_readout(1, 4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat7(self):
        """Overlap: extend the held end to whichever end is later."""
        with self.voiceover(text=BEATS[7]) as tr:
            swap_rails(self, headline("It starts inside, so extend."), caption("end = max(end, e)"))
            bar = self.sorted_bars[1]
            self.play(
                bar.animate.set_stroke(WINDOW, width=2.6).set_fill(WINDOW, opacity=0.5),
                run_time=0.4,
            )
            self.play(
                self.held_tr.animate.set_value(5),
                run_time=min(1.4, max(0.8, tr.duration * 0.35)),
            )
            self._swap_readout(1, 5)
            self.play(*self._consume(bar), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat8(self):
        """The bug of the pattern: a contained interval must not shrink the block."""
        with self.voiceover(text=BEATS[8]) as tr:
            swap_rails(self, headline("Never shrink: take the maximum."), caption("max(5, 3) = 5"))
            self._fade(self._readout, run_time=0.25)
            bar = self.sorted_bars[2]
            rule = self._rule_text("max(held_end, e)   not   e", color=GONE)
            self.play(FadeIn(rule), run_time=0.35)
            self.play(
                bar.animate.set_stroke(GONE, width=2.6).set_fill(GONE, opacity=0.5),
                run_time=0.4,
            )
            self.camera.frame.save_state()  # bare: stores, doesn't animate
            self.play(
                self.camera.auto_zoom([self.held, bar, rule], margin=0.9),
                run_time=min(1.0, max(0.6, tr.duration * 0.25)),
            )
            # computed state: the wrong answer really is [1, 3] for a moment, then corrected.
            self.held_color = GONE
            self.play(self.held_tr.animate.set_value(3), run_time=0.7)
            self.held_color = GOOD
            self.play(
                self.held_tr.animate.set_value(5),
                run_time=min(1.1, max(0.6, tr.duration * 0.28)),
            )
            self.play(*self._consume(bar), run_time=0.3)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.45)))
            self._max_rule = rule

    def _beat9(self):
        """A gap: flush the block, start a fresh one."""
        with self.voiceover(text=BEATS[9]) as tr:
            swap_rails(self, headline("A gap flushes the block."), caption("emit, then start fresh"))
            self.play(Restore(self.camera.frame), run_time=0.6)
            self._fade(self._max_rule, run_time=0.3)
            nxt = self.sorted_bars[3]
            self._flush_held()
            self.play(
                nxt.animate.set_stroke(WINDOW, width=2.6).set_fill(WINDOW, opacity=0.5),
                run_time=0.35,
            )
            self.play(
                self._to_merged_lane(nxt, 7),
                run_time=min(0.9, max(0.5, tr.duration * 0.22)),
            )
            self._held_from(nxt, 6, 8)
            self._swap_readout(6, 8)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat10(self):
        """The sweep continues: one comparison per interval, nothing rescanned."""
        with self.voiceover(text=BEATS[10]) as tr:
            swap_rails(self, headline("Every interval is compared once."), caption("with the one being held"))
            bar = self.sorted_bars[4]
            self.play(
                bar.animate.set_stroke(WINDOW, width=2.6).set_fill(WINDOW, opacity=0.5),
                run_time=0.4,
            )
            self.play(
                self.held_tr.animate.set_value(10),
                run_time=min(1.4, max(0.8, tr.duration * 0.35)),
            )
            self._swap_readout(6, 10)
            self.play(*self._consume(bar), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat11(self):
        """Six in, three out — and the blocks are disjoint and ordered."""
        with self.voiceover(text=BEATS[11]) as tr:
            swap_rails(self, headline("Six in, three merged blocks out."), caption("disjoint, in order"))
            last = self.sorted_bars[5]
            tag = chip("6 in  ->  3 out", color=GOOD, fs=SMALL_FS)
            tag.move_to([3.5, 2.3, 0])
            self._flush_held(run_time=0.4)
            self.play(self._to_merged_lane(last, 11.5), run_time=0.7)
            self._held_from(last, 11, 12)
            self.held.clear_updaters()
            self.merged_bars.append(self.held)
            self.play(
                self.held.animate.set_stroke(GOOD, width=2.6).set_fill(GOOD, opacity=0.45),
                FadeIn(tag),
                run_time=0.5,
            )
            self._swap_readout(11, 12, color=GOOD)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.5)))
            self._count_tag = tag

    def _beat12(self):
        """Why it's correct, with the camera on the merged lane."""
        with self.voiceover(text=BEATS[12]) as tr:
            swap_rails(
                self, headline("The held end is the furthest right."), caption("anything before it touches us")
            )
            self._fade(
                self._count_tag,
                self.axis_label,
                self.out_label,
                *[self.sorted_bars[i] for i in (0, 1, 2, 3, 4)],
                run_time=0.4,
            )
            note = self._rule_text("sorted order  ->  no earlier start can appear later", color=INK)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            new_readout = self._readout_text(1, 5, GOOD)
            self.play(FadeOut(self._readout), FadeIn(new_readout), run_time=0.35)
            self._readout = new_readout
            self.camera.frame.save_state()  # bare: stores, doesn't animate
            self.play(
                self.camera.auto_zoom(
                    [*self.merged_bars, self.axis, self._readout, note], margin=0.8
                ),
                run_time=min(1.2, max(0.7, tr.duration * 0.3)),
            )
            self.play(Indicate(self.merged_bars[0], color=GOOD, scale_factor=1.0), run_time=0.6)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.45)))
            self._why = note

    def _beat13(self):
        """Closed versus half-open: one character, two different answers."""
        with self.voiceover(text=BEATS[13]) as tr:
            swap_rails(
                self, headline("Do touching intervals merge?"), caption("closed versus half-open")
            )
            self.play(Restore(self.camera.frame), run_time=0.6)
            self._fade(self._why, self._readout, self.lanes.bars, self.axis, run_time=0.35)

            def x_of(t):  # a tiny, self-contained number line for the touching pair
                return -3.5 + (t - 1) * 0.95

            top_bars = VGroup(
                mini_bar(x_of, 1, 4, y=1.35, color=GOOD, opacity=0.5),
                mini_bar(x_of, 4, 5, y=1.35, color=GOOD, opacity=0.5),
            )
            low_bars = VGroup(
                mini_bar(x_of, 1, 4, y=-0.2, color=WINDOW, opacity=0.5),
                mini_bar(x_of, 4, 5, y=-0.2, color=WINDOW, opacity=0.5),
            )
            t1 = Text("closed [s, e]:  b.start <= a.end  ->  merge", font=MONO,
                      font_size=SMALL_FS, color=GOOD).move_to([-1.4, 0.62, 0])
            t2 = Text("half-open [s, e):  b.start < a.end  ->  separate", font=MONO,
                      font_size=SMALL_FS, color=WINDOW).move_to([-1.4, -0.92, 0])
            note = Text("merging schedules and counting rooms disagree here", font=MONO,
                        font_size=SMALL_FS, color=MUTED).move_to([-0.4, -1.85, 0])
            self.play(FadeIn(top_bars), FadeIn(t1), run_time=0.45)
            self.play(FadeIn(low_bars), FadeIn(t2), run_time=0.45)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._conv = VGroup(top_bars, low_bars, t1, t2, note)

    def _beat14(self):
        """Say the convention out loud."""
        with self.voiceover(text=BEATS[14]) as tr:
            swap_rails(
                self, headline("Say which convention you assume."), caption("it is worth more than the code")
            )
            self._fade(self._conv, run_time=0.3)
            say = chip("closed  ->  touch merges", color=GOOD, fs=SMALL_FS)
            say2 = chip("half-open  ->  room emptied", color=WINDOW, fs=SMALL_FS)
            row = VGroup(say, say2).arrange(RIGHT, buff=0.8).move_to([-0.4, 1.5, 0])
            note = Text("both are right - the question decides", font=MONO, font_size=BODY_FS,
                        color=INK).move_to([-0.4, -0.1, 0])
            self.play(FadeIn(row, shift=UP * 0.15), run_time=0.5)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._say = VGroup(row, note)

    def _beat15(self):
        """Complexity, stated cold."""
        with self.voiceover(text=BEATS[15]) as tr:
            swap_rails(
                self, headline("n log n time, n space."), caption("the sort dominates")
            )
            self._fade(self._say, run_time=0.35)
            brute = VGroup(
                Text("every pair", font=MONO, font_size=BODY_FS, color=GONE),
                MathTex(r"O(n^2)", color=GONE).scale(1.2),
            ).arrange(DOWN, buff=0.18)
            fast = VGroup(
                Text("sort + sweep", font=MONO, font_size=BODY_FS, color=GOOD),
                MathTex(r"O(n \log n)", color=GOOD).scale(1.2),
            ).arrange(DOWN, buff=0.18)
            arrow = Text("->", font=MONO, font_size=40, color=MUTED)
            both = VGroup(brute, arrow, fast).arrange(RIGHT, buff=0.9).move_to([-0.5, 1.0, 0])
            note = Text("the log n is the sort; the sweep is linear", font=MONO,
                        font_size=SMALL_FS, color=MUTED).move_to([-0.4, -0.9, 0])
            note2 = Text("space O(n) for the merged output", font=MONO, font_size=SMALL_FS,
                         color=MUTED).move_to([-0.4, -1.7, 0])
            self.play(FadeIn(brute), run_time=0.4)
            self.play(FadeIn(arrow), run_time=0.25)
            self.play(FadeIn(fast), run_time=0.45)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.35)
            self.play(FadeIn(note2, shift=UP * 0.15), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._complexity = VGroup(both, note, note2)

    def _beat16(self):
        """The pre-sorted shortcut: check before you sort."""
        with self.voiceover(text=BEATS[16]) as tr:
            swap_rails(
                self, headline("Already sorted? Drop the sort."), caption("check, don't assume")
            )
            self._fade(self._complexity, run_time=0.3)
            a = chip("input already sorted: O(n)", color=GOOD, fs=SMALL_FS)
            b = chip("two sorted lists: O(n + m)", color=PRIMARY, fs=SMALL_FS)
            row = VGroup(a, b).arrange(DOWN, buff=0.45).move_to([-0.4, 0.6, 0])
            note = Text("ask before you sort reflexively", font=MONO, font_size=SMALL_FS,
                        color=MUTED).move_to([-0.4, -1.0, 0])
            self.play(FadeIn(a, shift=UP * 0.15), run_time=0.45)
            self.play(FadeIn(b, shift=UP * 0.15), run_time=0.45)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._presorted = VGroup(row, note)

    def _beat17(self):
        """Shape two: two sorted lists, two pointers, advance the earlier end."""
        with self.voiceover(text=BEATS[17]) as tr:
            swap_rails(
                self, headline("Shape two: two lists, two pointers."), caption("advance the earlier end")
            )
            self._fade(self._presorted, run_time=0.3)
            x_of, ax = mini_axis(0, 10, y=-0.4, x0=-4.6, unit=0.6)
            A = [(0, 3), (5, 8)]
            B = [(1, 4), (6, 10)]
            a_bars = VGroup(*[mini_bar(x_of, s, e, y=1.2, color=PRIMARY) for s, e in A])
            b_bars = VGroup(*[mini_bar(x_of, s, e, y=0.4, color=ACCENT) for s, e in B])
            la = Text("A", font=MONO, font_size=SMALL_FS, color=PRIMARY)
            la.move_to([x_of(0) - 0.3, 1.2, 0])
            lb = Text("B", font=MONO, font_size=SMALL_FS, color=ACCENT)
            lb.move_to([x_of(0) - 0.3, 0.4, 0])
            inter = VGroup(
                mini_bar(x_of, 1, 3, y=-1.05, color=GOOD, h=0.26),
                mini_bar(x_of, 6, 8, y=-1.05, color=GOOD, h=0.26),
            )
            formula = Text("lo = max(starts),  hi = min(ends)", font=MONO, font_size=SMALL_FS,
                           color=INK).move_to([-0.5, -1.65, 0])
            out = Text("overlaps: [1, 3] and [6, 8]", font=MONO, font_size=SMALL_FS,
                       color=GOOD).move_to([-0.5, -2.35, 0])
            tag = chip("advance the earlier end", color=WINDOW, fs=SMALL_FS)
            tag.move_to([3.9, 2.3, 0])
            self.play(FadeIn(a_bars), FadeIn(la), run_time=0.4)
            self.play(FadeIn(b_bars), FadeIn(lb), run_time=0.4)
            self.play(FadeIn(ax), run_time=0.35)
            self.play(FadeIn(formula, shift=UP * 0.15), run_time=0.4)
            self.play(FadeIn(inter), FadeIn(out), run_time=0.5)
            self.play(FadeIn(tag), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._shape2 = VGroup(a_bars, b_bars, la, lb, inter, ax, formula, out, tag)

    def _beat18(self):
        """Shape three: counting, not merging — a heap of end times."""
        with self.voiceover(text=BEATS[18]) as tr:
            swap_rails(
                self, headline("Shape three: stop merging, count."), caption("a heap of end times")
            )
            self._fade(self._shape2, run_time=0.3)
            x_of, ax = mini_axis(0, 8, y=-0.5, x0=-4.6, unit=0.6)
            meet = [(1, 4), (2, 5), (3, 6)]
            bars = VGroup(
                *[mini_bar(x_of, s, e, y=1.5 - i * 0.7, color=PRIMARY) for i, (s, e) in enumerate(meet)]
            )
            heap_box = card(1.5, 2.3, color=ACCENT, fill=PANEL)
            heap_box.move_to([3.6, 0.7, 0])
            heap_lb = Text("heap of ends", font=MONO, font_size=SMALL_FS, color=ACCENT)
            heap_lb.next_to(heap_box, UP, buff=0.18)
            ends = VGroup(
                *[
                    Text(str(e), font=MONO, font_size=SMALL_FS, color=INK).move_to([3.6, y, 0])
                    for e, y in ((4, 1.45), (5, 0.7), (6, -0.05))
                ]
            )
            note = Text("has anything finished by the time this one starts?",
                        font=MONO, font_size=SMALL_FS, color=MUTED).move_to([-1.1, -1.5, 0])
            self.play(FadeIn(bars), run_time=0.45)
            self.play(FadeIn(ax), run_time=0.3)
            self.play(FadeIn(heap_box), FadeIn(heap_lb), run_time=0.4)
            self.play(FadeIn(ends, shift=DOWN * 0.15), run_time=0.5)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._heap = VGroup(bars, ax, heap_box, heap_lb, ends, note)

    def _beat19(self):
        """The heap size is the answer; the sweep line is the same algorithm."""
        with self.voiceover(text=BEATS[19]) as tr:
            swap_rails(
                self, headline("The peak heap size is the answer."), caption("same as a +1 / -1 sweep")
            )
            peak = chip("3 rooms overlap here", color=GOOD, fs=SMALL_FS)
            peak.move_to([-0.4, -0.2, 0])
            sweep = Text("+1 at every start,  -1 at every end,  track the peak",
                         font=MONO, font_size=SMALL_FS, color=WINDOW).move_to([-0.4, -1.2, 0])
            self.play(FadeIn(peak, scale=0.95), run_time=0.5)
            self.play(FadeIn(sweep, shift=UP * 0.15), run_time=0.45)
            self.play(
                *[Indicate(e, color=ACCENT, scale_factor=1.15) for e in self._heap[4]],
                run_time=0.7,
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._peak = VGroup(peak, sweep)

    def _beat20(self):
        """Recognition signals."""
        with self.voiceover(text=BEATS[20]) as tr:
            swap_rails(
                self, headline("When to reach for it."), caption("starts, ends, conflicts")
            )
            self._fade(self._heap, self._peak, run_time=0.3)
            yes = VGroup(
                Text("input is pairs of [start, end]", font=MONO, font_size=SMALL_FS, color=GOOD),
                Text("merge, overlap, conflict, collide", font=MONO, font_size=SMALL_FS, color=GOOD),
                Text("how many run at the same time", font=MONO, font_size=SMALL_FS, color=GOOD),
                Text("free time, gaps, available slots", font=MONO, font_size=SMALL_FS, color=GOOD),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.26)
            yes.move_to(stage_center(0.0))
            self.play(
                *[FadeIn(t, shift=RIGHT * 0.2) for t in yes],
                lag_ratio=0.32,
                run_time=min(1.7, max(0.9, tr.duration * 0.4)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._yes = yes

    def _beat21(self):
        """What breaks it."""
        with self.voiceover(text=BEATS[21]) as tr:
            swap_rails(self, headline("Know what breaks it."), caption("the max, and the convention"))
            self._fade(self._yes)
            no = VGroup(
                Text("x  extend with `end` instead of max", font=MONO, font_size=SMALL_FS, color=GONE),
                Text("x  the wrong open / closed convention", font=MONO, font_size=SMALL_FS, color=GONE),
                Text("x  sorting input that was already sorted", font=MONO, font_size=SMALL_FS, color=GONE),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
            no.move_to(stage_center(0.0))
            self.play(
                *[FadeIn(t, shift=RIGHT * 0.2) for t in no],
                lag_ratio=0.35,
                run_time=min(1.6, max(0.9, tr.duration * 0.4)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._no = no

    def _beat22(self):
        """Recall card."""
        with self.voiceover(text=BEATS[22]) as tr:
            swap_rails(
                self, headline("Sort, hold one, extend with max."), caption("the whole pattern")
            )
            self._fade(self._no)
            box = card(8.6, 1.5, color=ACCENT, fill=PANEL)
            box.move_to(stage_center(-0.1))
            top = Text("Merge Intervals", font=MONO, font_size=32, color=ACCENT)
            sub = Text("O(n log n) time  .  O(n) space  .  sort by start",
                       font=MONO, font_size=SMALL_FS, color=MUTED)
            VGroup(top, sub).arrange(DOWN, buff=0.22).move_to(box.get_center())
            self.play(FadeIn(box, scale=0.96), run_time=0.45)
            self.play(Write(top), run_time=0.5)
            self.play(FadeIn(sub), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
