"""
Pattern 05 — Prefix Sum.

The film follows the card's own argument: hook -> the job -> the brute-force cost -> the
running total -> the empty prefix -> the slice identity -> the question changes shape ->
the map -> the two seeding bugs -> the walk (the heart) -> complexity and its honest space
cost -> why it's correct -> the three variations -> the honest boundary -> recognition ->
what breaks it -> the recall card.

Narration lives in BEATS and the animation is written against `tracker.duration`, so the
picture and the voice cannot drift: one file is the single source of truth for both.
"""

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    Circumscribe,
    FadeIn,
    FadeOut,
    GrowArrow,
    Indicate,
    Line,
    MathTex,
    Restore,
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
from shots import ArrayRow, chip, hash_buckets, window_over

PATTERN_SLUG = "prefix-sum"
TITLE = "Prefix Sum"
SUMMARY = "Every range sum is two running totals subtracted, so a map answers pair questions in O(1)."
SCENE_CLASS = "PrefixSum"
POSTER_AT = 34.0

NUMS = [3, 4, 7, 2, -3, 1]
PREFIX = [0, 3, 7, 14, 16, 13, 14]
MOD = [v % 7 for v in PREFIX]
K = 7
# How many subarrays summing to k have been found after t steps of the walk.
COUNT_AT = [0, 0, 1, 2, 2, 2, 3]

BEATS = [
    # 0 hook
    "Every range sum is just two running totals subtracted.",
    # 1 the job
    "Here's the job: how many subarrays of this array add up to seven?",
    # 2 brute force
    "The slow way tries every start and every end. That's quadratic.",
    # 3 the running total
    "Instead, walk once and keep a running total. At each step you hold the sum of everything behind you.",
    # 4 the empty prefix
    "Put a zero in front. That's the empty prefix, the sum of nothing at all.",
    # 5 the slice identity
    "So the slice sum is the total at b plus one, minus the total at a.",
    # 6 the question changes shape
    "Now the question changes shape. A slice summing to k means two running totals that differ by k.",
    # 7 the map
    "So ask the map: have I seen a total like that before? That's one lookup, and it's constant time.",
    # 8 seed the zero
    "Seed the map with zero, seen once. Without it, every answer starting at the first element disappears.",
    # 9 add, don't flag
    "Add the count, never set a flag. Several earlier totals can match, each a different slice.",
    # 10 the walk
    "Watch it run. Three plus four is seven. Seven alone. Then seven, two, minus three, one.",
    # 11 complexity
    "One pass, one lookup per element. Linear time, and linear space for the map.",
    # 12 the honest cost
    "That space is the honest cost. You're buying constant-time questions about any earlier position.",
    # 13 why it's correct
    "Why correct? Any slice sum is the difference of two totals, and we stored every total we passed.",
    # 14 variation one
    "First variation: change the values until the question is equality. Key on the remainder.",
    # 15 divisibility
    "Equal remainders mean the difference is a multiple of k. That's divisibility, answered by a map.",
    # 16 variation two
    "Second variation: counting? Store a count and increment it. Want the longest? Store the earliest index.",
    # 17 the overwrite bug
    "Overwrite that earliest index and you measure from the wrong place, reporting a slice that's too short.",
    # 18 variation three
    "Third: when the question is a range, not an exact value, a map cannot help. You need order.",
    # 19 upgrade the lookup
    "So upgrade the lookup: a monotonic deque, a sorted structure, or a merge sort.",
    # 20 recognise
    "Reach for prefix sums for counting, longest, remainders, and repeated range sums, especially with negatives.",
    # 21 what breaks it
    "What breaks it: a range question, a forgotten zero, and flagging instead of adding.",
    # 22 recall
    "Running total, plus a map of the past.",
]

CHAPTERS = {
    0: "The hook",
    1: "The job",
    2: "Brute force",
    3: "The running total",
    4: "The empty prefix",
    5: "The slice identity",
    6: "The question changes",
    7: "The map",
    8: "Seed the zero",
    10: "The walk",
    11: "Complexity",
    13: "Why it's correct",
    14: "The three variations",
    18: "The honest boundary",
    20: "How to recognise it",
    22: "Recall",
}


class PrefixSum(PrebakedVoiceMovingCameraScene):
    # ---------------------------------------------------------------------------- setup
    def construct(self):
        bg(self)
        self.nums = ArrayRow(NUMS, cell=0.62, fs=26, index_fs=SMALL_FS)
        self.pre = ArrayRow(PREFIX, cell=0.62, fs=26, index_fs=SMALL_FS)
        self.nums.group.move_to([-0.3, 1.05, 0])
        self.pre.group.move_to([0.0, -0.18, 0])
        # pre[i + 1] sits directly under nums[i]: the totals line up with the elements.
        self.pre.group.shift(
            RIGHT * (self.nums.cells.get_right()[0] - self.pre.cells.get_right()[0])
        )
        for i in range(len(BEATS)):
            getattr(self, f"_beat{i}")()

    # ------------------------------------------------------------------------- utilities
    def _step(self, v: float) -> int:
        return max(0, min(len(NUMS), int(round(v))))

    def _seen_pairs(self, st: int):
        """Every distinct earlier prefix and how many times it has been seen, by step `st`."""
        counts, order = {}, []
        for j in range(st + 1):
            v = PREFIX[j]
            if v not in counts:
                counts[v] = 0
                order.append(v)
            counts[v] += 1
        return [(v, counts[v]) for v in order]

    def _seen_rows(self, pairs):
        rows = hash_buckets(
            [f"{v} : {c}" for v, c in pairs], bucket_w=1.52, row_h=0.42, buff=0.12
        )
        rows.move_to([3.3, 1.68, 0], aligned_edge=UP + LEFT)
        return rows

    def _seen_header(self):
        return Text("seen", font=MONO, font_size=SMALL_FS, color=MUTED).move_to(
            [3.3, 2.04, 0], aligned_edge=LEFT
        )

    def _head_at(self, v: float):
        """The reading head: where the walk currently is, above the element being read."""
        i = self._step(v)
        i = max(0, min(len(NUMS) - 1, i - 1 if i > 0 else 0))
        tip = self.nums.cell(i).get_top()
        return Arrow(
            tip + UP * 0.52,
            tip + UP * 0.1,
            buff=0,
            color=ACCENT,
            stroke_width=3.4,
            max_tip_length_to_length_ratio=0.3,
        )

    def _running_text(self, v: float):
        return Text(
            f"running = {PREFIX[self._step(v)]}", font=MONO, font_size=BODY_FS, color=ACCENT
        ).move_to([-5.0, -1.3, 0], aligned_edge=LEFT)

    def _need_text(self, v: float):
        i = self._step(v)
        key = PREFIX[i] - K
        hit = key in PREFIX[:i]
        return Text(
            f"need {PREFIX[i]} - {K} = {key}",
            font=MONO,
            font_size=SMALL_FS,
            color=GOOD if hit else MUTED,
        ).move_to([-5.0, -1.95, 0], aligned_edge=LEFT)

    def _count_chip(self, v: float):
        return chip(f"count = {COUNT_AT[self._step(v)]}", color=GOOD, fs=BODY_FS).move_to(
            [4.15, -1.8, 0]
        )

    def _fade(self, *mobs, run_time: float = 0.3):
        live = [m for m in mobs if m is not None]
        if live:
            self.play(*[FadeOut(m, run_time=run_time) for m in live])

    # ---------------------------------------------------------------------------- beats
    def _beat0(self):
        """Hook: name the trade in one claim, then put the two costs side by side."""
        with self.voiceover(text=BEATS[0]) as tr:
            swap_rails(
                self, headline("A range sum is two totals subtracted."), caption("prefix sums")
            )
            bad = chip("every slice: n^2", color=GONE, fs=BODY_FS)
            good = chip("running total: n", color=GOOD, fs=BODY_FS)
            row = VGroup(bad, good).arrange(RIGHT, buff=0.7).move_to(stage_center(-0.2))
            self.play(FadeIn(bad, shift=UP * 0.2), run_time=0.5)
            self.wait(0.25)
            self.play(FadeIn(good, shift=UP * 0.2), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._hook = row

    def _beat1(self):
        """The job: the array and k, so every later beat has a persistent anchor."""
        with self.voiceover(text=BEATS[1]) as tr:
            swap_rails(
                self, headline("Count the slices that add to seven."), caption("subarray sum = k")
            )
            self._fade(self._hook)
            self.kchip = chip(f"k = {K}", color=ACCENT, fs=BODY_FS).move_to([0.55, 2.3, 0])
            self.count_chip = self._count_chip(0)
            self.play(
                FadeIn(self.nums.cells, shift=UP * 0.25),
                FadeIn(self.nums.idx),
                run_time=min(1.2, max(0.6, tr.duration * 0.3)),
            )
            self.play(FadeIn(self.kchip, scale=0.92), FadeIn(self.count_chip), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat2(self):
        """Brute force, in the shape the audience already knows: every start, every end."""
        with self.voiceover(text=BEATS[2]) as tr:
            swap_rails(
                self, headline("The obvious way tries every slice."), caption("nested loops = quadratic")
            )
            code = VGroup(
                Text("for a in range(n):", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("    for b in range(a, n):", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("        sum(nums[a:b+1])", font=MONO, font_size=SMALL_FS, color=GONE),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
            box = card(code.width + 0.9, code.height + 0.6, color=STROKE, fill=PANEL)
            box.move_to([-1.9, -1.5, 0])
            code.move_to(box.get_center())
            tag = Text("n x n slices", font=MONO, font_size=SMALL_FS, color=GONE)
            tag.next_to(box, DOWN, buff=0.18)
            self.play(FadeIn(box), run_time=0.35)
            self.play(Write(code), run_time=min(1.1, max(0.5, tr.duration * 0.3)))
            self.play(FadeIn(tag, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._brute = VGroup(box, code, tag)

    def _beat3(self):
        """The running total: the prefix row appears, aligned under the elements."""
        with self.voiceover(text=BEATS[3]) as tr:
            swap_rails(
                self, headline("Walk once, keeping a running total."), caption("the sum behind you")
            )
            self._fade(self._brute, run_time=0.35)
            self.lab_nums = Text("nums", font=MONO, font_size=SMALL_FS, color=MUTED)
            self.lab_nums.next_to(self.nums.cells, LEFT, buff=0.28)
            self.lab_pre = Text("prefix", font=MONO, font_size=SMALL_FS, color=MUTED)
            self.lab_pre.next_to(self.pre.cells, LEFT, buff=0.28)
            self.play(FadeIn(self.lab_nums), run_time=0.3)
            self.play(
                FadeIn(self.pre.cells, shift=UP * 0.3),
                FadeIn(self.pre.idx),
                FadeIn(self.lab_pre),
                run_time=min(1.3, max(0.7, tr.duration * 0.35)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat4(self):
        """The empty prefix, and why it has to exist."""
        with self.voiceover(text=BEATS[4]) as tr:
            swap_rails(
                self, headline("The zero in front is the empty prefix."), caption("pre[0] = 0")
            )
            note = Text("the empty prefix", font=MONO, font_size=SMALL_FS, color=ACCENT)
            note.move_to([-3.05, -1.5, 0])
            link = Arrow(
                note.get_top() + UP * 0.05,
                self.pre.cell(0).get_bottom() + DOWN * 0.06,
                buff=0,
                color=ACCENT,
                stroke_width=3.0,
                max_tip_length_to_length_ratio=0.3,
            )
            self.play(FadeIn(note), run_time=0.35)
            self.play(*self.pre.focus(0, color=ACCENT), GrowArrow(link), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._empty = VGroup(note, link)

    def _beat5(self):
        """The identity the whole pattern rests on, drawn on the two rows."""
        with self.voiceover(text=BEATS[5]) as tr:
            swap_rails(
                self, headline("Slice sum equals two totals subtracted."), caption("pre[b+1] - pre[a]")
            )
            self._fade(self._empty)
            self._slice_win = window_over(self.nums, 0, 1, color=WINDOW, label="the slice")
            eq = Text("pre[2] - pre[0] = 7 - 0 = 7", font=MONO, font_size=BODY_FS, color=WINDOW)
            eq.move_to([-1.7, -1.6, 0])
            self.play(FadeIn(self._slice_win), run_time=0.4)
            self.play(
                *self.pre.focus(0, color=WINDOW),
                *self.pre.focus(2, color=WINDOW),
                run_time=0.45,
            )
            self.play(Write(eq), run_time=min(1.1, max(0.5, tr.duration * 0.3)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._slice_eq = eq

    def _beat6(self):
        """Every subarray question becomes a pair question."""
        with self.voiceover(text=BEATS[6]) as tr:
            swap_rails(
                self, headline("A slice sum becomes a pair question."), caption("two totals differing by k")
            )
            self._fade(self._slice_eq, self._slice_win)
            left = chip("slice sum = k", color=ACCENT, fs=BODY_FS)
            right = chip("two totals differ by k", color=GOOD, fs=BODY_FS)
            arrow = Text("->", font=MONO, font_size=38, color=MUTED)
            row = VGroup(left, arrow, right).arrange(RIGHT, buff=0.35)
            row.move_to([-0.9, -1.6, 0])
            self.play(FadeIn(left, shift=UP * 0.15), run_time=0.4)
            self.play(FadeIn(arrow), run_time=0.25)
            self.play(FadeIn(right, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._shape = row

    def _beat7(self):
        """The map of totals, and the lookup it buys."""
        with self.voiceover(text=BEATS[7]) as tr:
            swap_rails(
                self, headline("Ask the map what it has seen."), caption("one lookup, O(1)")
            )
            self._fade(self._shape)
            self._panel = self._seen_rows([(0, 1)])
            self._panel[0][0].set_stroke(ACCENT, width=2.2)
            self._panel_head = self._seen_header()
            note = Text(
                "ask the map: have I seen running - k ?",
                font=MONO,
                font_size=SMALL_FS,
                color=MUTED,
            )
            note.move_to([-0.9, -1.6, 0])
            self.play(FadeIn(self._panel_head), FadeIn(self._panel), run_time=0.45)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._map_note = note

    def _beat8(self):
        """The single most common bug in this pattern: the missing zero."""
        with self.voiceover(text=BEATS[8]) as tr:
            swap_rails(
                self, headline("Seed the map with zero, seen once."), caption("or index-0 answers vanish")
            )
            self._fade(self._map_note)
            warn = Text(
                "leave 0 out  ->  answers starting at index 0 vanish",
                font=MONO,
                font_size=SMALL_FS,
                color=GONE,
            )
            warn.move_to([-0.9, -1.7, 0])
            self.play(FadeIn(warn, shift=UP * 0.15), run_time=0.4)
            self.play(Indicate(self._panel[0][0], color=ACCENT, scale_factor=1.12), run_time=0.7)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._warn = warn

    def _beat9(self):
        """Count, not flag: several earlier totals can be the same total."""
        with self.voiceover(text=BEATS[9]) as tr:
            swap_rails(
                self, headline("Add the count, never set a flag."), caption("each match is its own slice")
            )
            self._fade(self._warn)
            extra = self._seen_rows([(0, 1), (7, 1)])
            extra[1][0].set_stroke(ACCENT, width=2.2)
            self.play(FadeOut(self._panel), run_time=0.25)
            self.play(FadeIn(extra), run_time=0.4)
            note = Text(
                "two earlier totals, two slices  ->  count += 2",
                font=MONO,
                font_size=SMALL_FS,
                color=GOOD,
            )
            note.move_to([-0.9, -1.7, 0])
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._panel = extra
            self._add_note = note

    def _beat10(self):
        """The heart: the walk, driven by computed state so nothing is hand-keyframed."""
        with self.voiceover(text=BEATS[10]) as tr:
            swap_rails(
                self, headline("Watch the count land on three."), caption("one pass, no rescanning")
            )
            self._fade(self._add_note, self._panel, self._panel_head)
            t = ValueTracker(0)
            self.add(t)
            head = always_redraw(lambda: self._head_at(t.get_value()))
            run = always_redraw(lambda: self._running_text(t.get_value()))
            need = always_redraw(lambda: self._need_text(t.get_value()))
            cnt = always_redraw(lambda: self._count_chip(t.get_value()))
            live = always_redraw(lambda: self._seen_rows(self._seen_pairs(self._step(t.get_value()))))
            header = self._seen_header()
            self.add(head, run, need, cnt, live, header)
            self.play(
                t.animate.set_value(len(NUMS)),
                run_time=min(3.2, max(1.8, tr.duration * 0.6)),
                rate_func=lambda x: x,
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            for m in (head, run, need, cnt, live):
                m.clear_updaters()
            self.remove(t)
            self._walk = VGroup(head, run, need, cnt, live, header)

    def _beat11(self):
        """Complexity, stated cold."""
        with self.voiceover(text=BEATS[11]) as tr:
            swap_rails(
                self, headline("Linear time, linear space."), caption("the map is the space")
            )
            self._fade(self._walk, run_time=0.35)
            brute = VGroup(
                Text("every slice", font=MONO, font_size=BODY_FS, color=GONE),
                MathTex(r"O(n^2)", color=GONE).scale(1.2),
            ).arrange(DOWN, buff=0.18)
            fast = VGroup(
                Text("prefix + map", font=MONO, font_size=BODY_FS, color=GOOD),
                MathTex(r"O(n)", color=GOOD).scale(1.2),
            ).arrange(DOWN, buff=0.18)
            arrow = Text("->", font=MONO, font_size=40, color=MUTED)
            both = VGroup(brute, arrow, fast).arrange(RIGHT, buff=0.9).move_to([-0.6, -1.5, 0])
            self.play(FadeIn(brute), run_time=0.4)
            self.play(FadeIn(arrow), run_time=0.25)
            self.play(FadeIn(fast), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._complexity = both

    def _beat12(self):
        """The space is the honest cost of the pattern."""
        with self.voiceover(text=BEATS[12]) as tr:
            swap_rails(
                self, headline("The map is the space you pay."), caption("memory buys the lookup")
            )
            self._fade(self._complexity)
            a = chip("O(n) memory", color=GOOD, fs=BODY_FS)
            b = chip("O(1) questions about the past", color=PRIMARY, fs=BODY_FS)
            row = VGroup(a, b).arrange(DOWN, buff=0.45).move_to([-0.6, -1.55, 0])
            self.play(FadeIn(a, shift=UP * 0.15), run_time=0.4)
            self.play(FadeIn(b, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._cost = row

    def _beat13(self):
        """Why it's correct: the camera goes into the two totals and their difference."""
        with self.voiceover(text=BEATS[13]) as tr:
            swap_rails(
                self, headline("Every total we passed is stored."), caption("so any slice is a difference")
            )
            self._fade(self._cost, self.kchip, self.count_chip)
            self._slice_win = window_over(self.nums, 0, 1, color=WINDOW, label="the slice")
            eq = Text(
                "pre[b+1] - pre[a] = the slice", font=MONO, font_size=BODY_FS, color=GOOD
            )
            eq.move_to([-1.27, -1.45, 0])
            self.play(FadeIn(self._slice_win), run_time=0.35)
            self.play(
                *self.pre.focus(0, color=WINDOW),
                *self.pre.focus(2, color=WINDOW),
                run_time=0.4,
            )
            self.camera.frame.save_state()  # bare: stores, doesn't animate
            self.play(
                self.camera.auto_zoom(
                    [self.nums.group, self.pre.group, self.lab_nums, self.lab_pre, eq],
                    margin=0.7,
                ),
                Write(eq),
                run_time=min(1.4, max(0.8, tr.duration * 0.35)),
            )
            self.play(Circumscribe(self.pre.cells[0], color=ACCENT), run_time=0.7)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.5)))
            self._why_eq = eq

    def _beat14(self):
        """Variation one: transform the values until the question is equality."""
        with self.voiceover(text=BEATS[14]) as tr:
            swap_rails(
                self, headline("Change the values, then ask equality."), caption("key on the remainder")
            )
            self.play(Restore(self.camera.frame), run_time=0.6)
            self.play(
                FadeOut(self.nums.group),
                FadeOut(self.pre.group),
                FadeOut(self.lab_nums),
                FadeOut(self.lab_pre),
                FadeOut(self._why_eq),
                FadeOut(self._slice_win),
                run_time=0.4,
            )
            r1 = ArrayRow(PREFIX, cell=0.62, fs=22, show_index=False)
            r2 = ArrayRow(MOD, cell=0.62, fs=22, show_index=False)
            r1.group.move_to([0.55, 0.5, 0])
            r2.group.move_to([0.55, -0.3, 0])
            l1 = Text("prefix", font=MONO, font_size=SMALL_FS, color=MUTED)
            l1.next_to(r1.cells, LEFT, buff=0.3)
            l2 = Text("prefix % k", font=MONO, font_size=SMALL_FS, color=MUTED)
            l2.next_to(r2.cells, LEFT, buff=0.3)
            self.play(FadeIn(r1.cells), FadeIn(l1), run_time=0.45)
            self.play(
                FadeIn(r2.cells, shift=UP * 0.2), FadeIn(l2),
                run_time=min(1.2, max(0.7, tr.duration * 0.35)),
            )
            self.play(
                *[Indicate(r2.cell(i), color=GOOD, scale_factor=1.12) for i in (0, 2, 3, 6)],
                run_time=min(1.3, max(0.7, tr.duration * 0.35)),
            )
            note = Text(
                "equal remainders  ->  difference is a multiple of k",
                font=MONO,
                font_size=SMALL_FS,
                color=GOOD,
            )
            note.move_to([-0.4, -1.5, 0])
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._mod_rows = VGroup(r1.cells, r2.cells, l1, l2, note)

    def _beat15(self):
        """Divisibility, answered by a map instead of by arithmetic."""
        with self.voiceover(text=BEATS[15]) as tr:
            swap_rails(
                self, headline("Same remainder means divisible by k."), caption("divisibility as equality")
            )
            tag = Text("14 - 0 = 14, a multiple of 7", font=MONO, font_size=BODY_FS, color=GOOD)
            tag.move_to([-0.4, -2.1, 0])
            self.play(FadeIn(tag, shift=UP * 0.15), run_time=0.45)
            self.play(Circumscribe(self._mod_rows[1][2], color=ACCENT), run_time=0.7)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._div = tag

    def _beat16(self):
        """Variation two: the map value depends on the question being asked."""
        with self.voiceover(text=BEATS[16]) as tr:
            swap_rails(
                self, headline("Store a count, or the first index."), caption("never both")
            )
            self._fade(self._mod_rows, self._div, run_time=0.35)
            left = VGroup(
                Text("how many", font=MONO, font_size=BODY_FS, color=PRIMARY),
                Text("value: a count", font=MONO, font_size=SMALL_FS, color=INK),
                Text("repeat key: increment", font=MONO, font_size=SMALL_FS, color=GOOD),
            ).arrange(DOWN, buff=0.28)
            right = VGroup(
                Text("the longest", font=MONO, font_size=BODY_FS, color=ACCENT),
                Text("value: the first index", font=MONO, font_size=SMALL_FS, color=INK),
                Text("repeat key: leave it", font=MONO, font_size=SMALL_FS, color=GOOD),
            ).arrange(DOWN, buff=0.28)
            bl = card(left.width + 0.9, left.height + 0.8, color=PRIMARY, fill=PANEL)
            bl.move_to([-3.15, 0.2, 0])
            left.move_to(bl.get_center())
            br = card(right.width + 0.9, right.height + 0.8, color=ACCENT, fill=PANEL)
            br.move_to([3.15, 0.2, 0])
            right.move_to(br.get_center())
            self.play(FadeIn(bl), FadeIn(br), run_time=0.4)
            self.play(FadeIn(left, shift=UP * 0.15), run_time=0.45)
            self.play(FadeIn(right, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._table = VGroup(bl, left, br, right)

    def _beat17(self):
        """The overwrite bug: a wrong answer, not a crash."""
        with self.voiceover(text=BEATS[17]) as tr:
            swap_rails(
                self, headline("Overwrite the index and you lose length."), caption("a shorter window")
            )
            self._fade(self._table, run_time=0.35)
            r = ArrayRow(list(range(7)), cell=0.5, fs=SMALL_FS, show_index=False)
            r.group.move_to([0.3, 0.8, 0])
            keep = Line(
                r.cell(0).get_left() + LEFT * 0.05,
                r.cell(6).get_right() + RIGHT * 0.05,
                color=GOOD,
                stroke_width=6,
            ).shift(DOWN * 0.42)
            lose = Line(
                r.cell(3).get_left() + LEFT * 0.05,
                r.cell(6).get_right() + RIGHT * 0.05,
                color=GONE,
                stroke_width=6,
            ).shift(DOWN * 1.06)
            k1 = Text("earliest index: 0 -> 6", font=MONO, font_size=SMALL_FS, color=GOOD)
            k1.next_to(keep, RIGHT, buff=0.25)
            k2 = Text("overwritten: 3 -> 6", font=MONO, font_size=SMALL_FS, color=GONE)
            k2.next_to(lose, RIGHT, buff=0.25)
            self.play(FadeIn(r.cells), run_time=0.4)
            self.play(
                *[Indicate(r.cell(i), color=ACCENT, scale_factor=1.12) for i in (3, 6)],
                run_time=0.7,
            )
            self.play(FadeIn(keep), FadeIn(k1), run_time=0.45)
            self.play(FadeIn(lose), FadeIn(k2), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._bug = VGroup(r.cells, keep, lose, k1, k2)

    def _beat18(self):
        """Variation three: the honest boundary of the pattern."""
        with self.voiceover(text=BEATS[18]) as tr:
            swap_rails(
                self, headline("A range question is not a lookup."), caption("a map only knows exact keys")
            )
            self._fade(self._bug, run_time=0.35)
            q = Text("is there an earlier total at most p - k ?", font=MONO, font_size=BODY_FS, color=ACCENT)
            q.move_to([-0.4, 0.6, 0])
            bad = chip("hash map: exact keys only", color=GONE, fs=BODY_FS)
            bad.move_to([-0.4, -0.5, 0])
            good = Text("that is a range query - it needs order", font=MONO, font_size=SMALL_FS, color=GOOD)
            good.move_to([-0.4, -1.5, 0])
            self.play(FadeIn(q, shift=UP * 0.15), run_time=0.45)
            self.play(FadeIn(bad, shift=UP * 0.15), run_time=0.4)
            self.play(FadeIn(good, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._range = VGroup(q, bad, good)

    def _beat19(self):
        """Upgrade the lookup: same prefix insight, an ordered structure."""
        with self.voiceover(text=BEATS[19]) as tr:
            swap_rails(
                self, headline("Upgrade the lookup when order matters."), caption("deque, BIT, merge sort")
            )
            self._fade(self._range, run_time=0.35)
            a = chip("monotonic deque", color=PRIMARY, fs=SMALL_FS)
            b = chip("sorted structure / BIT", color=PRIMARY, fs=SMALL_FS)
            c = chip("merge sort", color=PRIMARY, fs=SMALL_FS)
            row = VGroup(a, b, c).arrange(RIGHT, buff=0.45).move_to([-0.4, 0.5, 0])
            cost = MathTex(r"O(n \log n)", color=ACCENT).scale(1.25)
            cost.move_to([-0.4, -0.7, 0])
            note = Text("the prefix insight survives; only the lookup changes", font=MONO,
                        font_size=SMALL_FS, color=MUTED)
            note.move_to([-0.4, -1.7, 0])
            self.play(FadeIn(row, shift=UP * 0.15), run_time=0.5)
            self.play(Write(cost), run_time=0.5)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._upgrade = VGroup(row, cost, note)

    def _beat20(self):
        """Recognition signals."""
        with self.voiceover(text=BEATS[20]) as tr:
            swap_rails(
                self, headline("When to reach for prefix sums."), caption("counting, longest, ranges")
            )
            self._fade(self._upgrade, run_time=0.3)
            yes = VGroup(
                Text("how many subarrays sum to ...", font=MONO, font_size=SMALL_FS, color=GOOD),
                Text("the longest subarray such that ...", font=MONO, font_size=SMALL_FS, color=GOOD),
                Text("divisibility, remainders, mod k", font=MONO, font_size=SMALL_FS, color=GOOD),
                Text("repeated range sums, or negatives", font=MONO, font_size=SMALL_FS, color=GOOD),
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
            swap_rails(
                self, headline("Know what breaks it."), caption("ranges, the zero, the flag")
            )
            self._fade(self._yes)
            no = VGroup(
                Text("x  a range question, not an exact key", font=MONO, font_size=SMALL_FS, color=GONE),
                Text("x  forgetting the empty prefix, 0", font=MONO, font_size=SMALL_FS, color=GONE),
                Text("x  flagging instead of adding counts", font=MONO, font_size=SMALL_FS, color=GONE),
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
        """Recall card: one line the viewer leaves with."""
        with self.voiceover(text=BEATS[22]) as tr:
            swap_rails(
                self, headline("Running total plus a map."), caption("count, longest, ranges")
            )
            self._fade(self._no)
            box = card(8.6, 1.5, color=ACCENT, fill=PANEL)
            box.move_to(stage_center(-0.1))
            top = Text("Prefix Sum", font=MONO, font_size=32, color=ACCENT)
            sub = Text("O(n) time  .  O(n) space  .  seed {0: 1}",
                       font=MONO, font_size=SMALL_FS, color=MUTED)
            VGroup(top, sub).arrange(DOWN, buff=0.22).move_to(box.get_center())
            self.play(FadeIn(box, scale=0.96), run_time=0.45)
            self.play(Write(top), run_time=0.5)
            self.play(FadeIn(sub), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
