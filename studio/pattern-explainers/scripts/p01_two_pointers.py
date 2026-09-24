"""
Pattern 01 — Two Pointers.

The film follows the pattern card's own argument: hook -> the job -> the brute-force cost ->
the sorted-order insight -> the converging walk (the heart) -> why it's correct -> complexity
-> the three shapes -> duplicates -> what breaks it -> recognition -> the recall card.

Narration lives in BEATS and the animation is written against `tracker.duration`, so the
picture and the voice cannot drift: one file is the single source of truth for both.
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
    GrowArrow,
    Indicate,
    Line,
    MathTex,
    Rectangle,
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
    MONO_FS,
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

PATTERN_SLUG = "two-pointers"
TITLE = "Two Pointers"
SUMMARY = "Sorted order turns an O(n^2) pair search into one O(n) pass."
SCENE_CLASS = "TwoPointers"
POSTER_AT = 30.0

ARR = [1, 4, 5, 6, 8, 11]
TARGET = 11

BEATS = [
    # 0 hook
    "Two pointers turns a nested loop into one walk down a sorted array.",
    # 1 the job
    "Here's the job: find two numbers in this sorted array that add to eleven.",
    # 2 brute force
    "The obvious way checks every pair. A nested loop, and that's quadratic.",
    # 3 insight
    "But the array is sorted, and that order is information we didn't pay for. We get to spend it.",
    # 4 two fingers
    "So put one finger on the smallest value, and one on the largest.",
    # 5 first sum
    "One plus eleven is twelve. Too big — we need eleven.",
    # 6 why the largest only grows
    "The right finger holds the largest value, so paired with anything else, the sum only grows.",
    # 7 eliminate right
    "So eleven can never be in the answer. Delete it, and step the right finger left.",
    # 8 too small
    "One plus eight is nine. Too small — and by the same argument, the smallest can't help either.",
    # 9 eliminate left
    "Delete the one, step the left finger right. Notice we never moved backwards.",
    # 10 too big again
    "Four plus eight is twelve. Too big again, so the eight is eliminated.",
    # 11 too small again
    "Four plus six is ten. Too small, so the four goes too.",
    # 12 found
    "Five plus six is eleven. Found it — in one pass, re-examining nothing.",
    # 13 why correct
    "Why is this correct? Each step deletes one element from the row of left values, and one from the column of right values.",
    # 14 linear
    "Each pointer moves at most n times and never backwards, so the work is at most two n steps.",
    # 15 complexity
    "Linear time, constant extra space. The nested loop was quadratic. That gap is the whole point.",
    # 16 shape A
    "This converging shape covers pair sums, palindromes, container with most water, and the three-sum family.",
    # 17 shape B
    "A second shape walks both fingers forward: slow marks the finished prefix, fast scans ahead.",
    # 18 shape C
    "A third splits into three regions in one pass. After swapping with high, don't advance mid.",
    # 19 duplicates
    "For three-sum, fix one index and converge on the rest. After a hit, skip duplicates.",
    # 20 what breaks it
    "Know what breaks it: unsorted input, or negatives in a product window, destroys monotonicity.",
    # 21 recognise
    "So reach for it when the input is sorted, or you're matching a pair or triplet.",
    # 22 counter-tell
    "Unsorted, and you need exact values? That's a hash map. Sorting first costs n log n.",
    # 23 recall
    "Two fingers, one pass, no going back.",
]

CHAPTERS = {
    0: "The hook",
    1: "The job",
    2: "Brute force",
    3: "The insight",
    4: "Two fingers",
    12: "Found it",
    13: "Why it's correct",
    15: "Complexity",
    16: "The three shapes",
    19: "Duplicates and traps",
    21: "How to recognise it",
    23: "Recall",
}


class TwoPointers(PrebakedVoiceMovingCameraScene):
    # ---------------------------------------------------------------------------- setup
    def construct(self):
        bg(self)
        self.row = ArrayRow(ARR, cell=0.66, fs=26, index_fs=SMALL_FS)
        self.row.group.move_to([0, 0.5, 0])
        self.lo_ptr = None
        self.hi_ptr = None
        for i in range(24):
            getattr(self, f"_beat{i}")()

    # ------------------------------------------------------------------------- utilities
    def _target_chip(self, reached: bool = False):
        return chip(f"target = {TARGET}", color=GOOD if reached else ACCENT, fs=BODY_FS).move_to(
            [0, 2.32, 0]
        )

    def _sum_line(self, a: int, b: int, verdict: str, color):
        eq = Text(f"{a} + {b} = {a + b}", font=MONO, font_size=34, color=color)
        eq.move_to([0, -1.35, 0])
        note = Text(verdict, font=MONO, font_size=SMALL_FS, color=color)
        note.next_to(eq, RIGHT, buff=0.4)
        return VGroup(eq, note)

    def _show_sum(self, tracker, a, b, verdict, color, *, settle: float = 0.55):
        line = self._sum_line(a, b, verdict, color)
        self.play(Write(line), run_time=min(1.0, max(0.5, tracker.duration * 0.25)))
        self.wait(max(0.1, tracker.get_remaining_duration(buff=settle)))
        return line

    # ---------------------------------------------------------------------------- beats
    def _beat0(self):
        """Hook: name the trade in one claim, then show the two costs as objects."""
        with self.voiceover(text=BEATS[0]) as tr:
            swap_rails(self, headline("A nested loop becomes one walk."),
                       caption("O(n^2)  →  O(n)"))
            self.play(FadeIn(rule()), run_time=0.3)
            bad = chip("every pair: n^2", color=GONE, fs=BODY_FS)
            good = chip("two pointers: n", color=GOOD, fs=BODY_FS)
            row = VGroup(bad, good).arrange(RIGHT, buff=0.6).move_to(stage_center(-0.2))
            self.play(FadeIn(bad, shift=UP * 0.2), run_time=0.5)
            self.wait(0.3)
            self.play(FadeIn(good, shift=UP * 0.2), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._hook = row

    def _beat1(self):
        """The job: array + target, so every later beat has a persistent anchor."""
        with self.voiceover(text=BEATS[1]) as tr:
            swap_rails(self, headline("Find two numbers that add to eleven."),
                       caption("sorted array, one target"))
            self.play(FadeOut(self._hook, run_time=0.3))
            tchip = self._target_chip()
            self.play(
                FadeIn(self.row.cells, shift=UP * 0.25),
                FadeIn(self.row.idx),
                run_time=min(1.2, max(0.6, tr.duration * 0.3)),
            )
            self.play(FadeIn(tchip, scale=0.9), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self.tchip = tchip

    def _beat2(self):
        """Brute force, in the shape the audience already knows: nested loops."""
        with self.voiceover(text=BEATS[2]) as tr:
            swap_rails(self, headline("The obvious way checks every pair."),
                       caption("nested loop = quadratic"))
            code = VGroup(
                Text("for i in range(n):", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("    for j in range(i+1, n):", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("        check(pair)", font=MONO, font_size=SMALL_FS, color=GONE),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
            box = card(code.width + 0.9, code.height + 0.6, color=STROKE, fill=PANEL)
            box.move_to([0, -1.42, 0])
            code.move_to(box.get_center())
            tag = Text("n x n comparisons", font=MONO, font_size=SMALL_FS, color=GONE)
            tag.next_to(box, DOWN, buff=0.2)
            self.play(FadeIn(box), run_time=0.35)
            self.play(Write(code), run_time=min(1.1, max(0.5, tr.duration * 0.3)))
            self.play(FadeIn(tag, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._brute = VGroup(box, code, tag)

    def _beat3(self):
        """The insight: sortedness is information. A sweep shows the order."""
        with self.voiceover(text=BEATS[3]) as tr:
            swap_rails(self, headline("Sorted order is free information."),
                       caption("we get to spend it"))
            self.play(FadeOut(self._brute, run_time=0.35))
            sweep = Line(
                self.row.cells.get_left() + LEFT * 0.3,
                self.row.cells.get_right() + RIGHT * 0.3,
                color=WINDOW, stroke_width=6,
            ).move_to(self.row.cells.get_center())
            mark = Text("sorted", font=MONO, font_size=SMALL_FS, color=GOOD)
            mark.next_to(self.row.cells, DOWN, buff=0.62)
            self.play(FadeIn(mark), run_time=0.3)
            self.play(
                ShowPassingFlash(sweep, time_width=0.55),
                run_time=min(1.6, max(0.8, tr.duration * 0.4)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._sorted_mark = mark

    def _beat4(self):
        """Two fingers land. This is the persistent anchor for the rest of the walk."""
        with self.voiceover(text=BEATS[4]) as tr:
            swap_rails(self, headline("One finger smallest, one largest."),
                       caption("lo = 0, hi = n - 1"))
            self.play(FadeOut(self._sorted_mark, run_time=0.25))
            self.lo_ptr = pointer(self.row, 0, "lo", color=ACCENT)
            self.hi_ptr = pointer(self.row, len(ARR) - 1, "hi", color=PRIMARY)
            self.play(GrowArrow(self.lo_ptr[0]), FadeIn(self.lo_ptr[1]), run_time=0.45)
            self.play(GrowArrow(self.hi_ptr[0]), FadeIn(self.hi_ptr[1]), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat5(self):
        """First sum, and the verdict that drives the first elimination."""
        with self.voiceover(text=BEATS[5]) as tr:
            swap_rails(self, headline("One plus eleven is twelve."), caption("too big"))
            self.play(*self.row.focus(0, color=ACCENT), *self.row.focus(5, color=PRIMARY),
                      run_time=0.5)
            line = self._show_sum(tr, 1, 11, "> 11", GONE)
            self.play(line.animate.set_color(GONE), run_time=0.3)
            self._sum5 = line

    def _beat6(self):
        """Why the largest can't participate: every partner is still too big."""
        with self.voiceover(text=BEATS[6]) as tr:
            swap_rails(self, headline("Paired with anything, the largest only grows."),
                       caption("hi is the ceiling"))
            self.play(FadeOut(self._sum5, run_time=0.25))
            sums = VGroup()
            for a in ARR[:-1]:
                sums.add(Text(f"{a}+11={a + 11}", font=MONO, font_size=SMALL_FS, color=GONE))
            sums.arrange(RIGHT, buff=0.36).move_to([0, -1.5, 0])
            self.play(
                FadeIn(sums, shift=UP * 0.2),
                run_time=min(1.4, max(0.7, tr.duration * 0.35)),
            )
            self.play(Indicate(self.row.cell(5), color=GONE, scale_factor=1.12), run_time=0.6)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._sums6 = sums

    def _beat7(self):
        """Eliminate the largest, step hi left. Cell 5 is gone for good."""
        with self.voiceover(text=BEATS[7]) as tr:
            swap_rails(self, headline("The largest can't be in the answer."),
                       caption("delete it, step left"))
            self.play(FadeOut(self._sums6, run_time=0.3))
            self.play(*self.row.mark_gone(5), run_time=0.45)
            new_hi = pointer(self.row, 4, "hi", color=PRIMARY)
            self.play(
                ReplacementTransform(self.hi_ptr, new_hi),
                run_time=min(0.9, max(0.5, tr.duration * 0.25)),
            )
            self.hi_ptr = new_hi
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat8(self):
        """Now too small — the mirror-image argument for the left pointer."""
        with self.voiceover(text=BEATS[8]) as tr:
            swap_rails(self, headline("One plus eight is nine."), caption("too small"))
            self.play(*self.row.reset(0, color=ACCENT, fill=PANEL), run_time=0.3)
            line = self._show_sum(tr, 1, 8, "< 11", GONE)
            self.play(line.animate.set_color(GONE), run_time=0.3)
            self._sum8 = line

    def _beat9(self):
        """Eliminate the smallest, step lo right."""
        with self.voiceover(text=BEATS[9]) as tr:
            swap_rails(self, headline("The smallest can't help either."),
                       caption("delete it, step right"))
            self.play(FadeOut(self._sum8, run_time=0.25))
            self.play(*self.row.mark_gone(0), run_time=0.45)
            new_lo = pointer(self.row, 1, "lo", color=ACCENT)
            self.play(
                ReplacementTransform(self.lo_ptr, new_lo),
                run_time=min(0.9, max(0.5, tr.duration * 0.25)),
            )
            self.lo_ptr = new_lo
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat10(self):
        """Too big again: eliminate 8."""
        with self.voiceover(text=BEATS[10]) as tr:
            swap_rails(self, headline("Four plus eight is twelve."),
                       caption("too big — the eight goes"))
            line = self._show_sum(tr, 4, 8, "> 11", GONE)
            self.play(*self.row.mark_gone(4), run_time=0.4)
            new_hi = pointer(self.row, 3, "hi", color=PRIMARY)
            self.play(ReplacementTransform(self.hi_ptr, new_hi), run_time=0.6)
            self.hi_ptr = new_hi
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._sum10 = line

    def _beat11(self):
        """Too small again: eliminate 4."""
        with self.voiceover(text=BEATS[11]) as tr:
            swap_rails(self, headline("Four plus six is ten."),
                       caption("too small — the four goes"))
            self.play(FadeOut(self._sum10, run_time=0.25))
            line = self._show_sum(tr, 4, 6, "< 11", GONE)
            self.play(*self.row.mark_gone(1), run_time=0.4)
            new_lo = pointer(self.row, 2, "lo", color=ACCENT)
            self.play(ReplacementTransform(self.lo_ptr, new_lo), run_time=0.6)
            self.lo_ptr = new_lo
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._sum11 = line

    def _beat12(self):
        """Found. Zoom the two surviving cells (charter rule 3), then return."""
        with self.voiceover(text=BEATS[12]) as tr:
            swap_rails(self, headline("Five plus six is eleven."),
                       caption("found, re-examining nothing"))
            self.play(FadeOut(self._sum11, run_time=0.25))
            line = self._sum_line(5, 6, "= 11", GOOD)
            self.camera.frame.save_state()  # bare: stores, doesn't animate
            self.play(
                self.camera.auto_zoom([self.row.cell(2), self.row.cell(3)], margin=1.5),
                Write(line),
                run_time=min(1.2, max(0.6, tr.duration * 0.3)),
            )
            self.play(*self.row.mark_good(2), *self.row.mark_good(3), run_time=0.45)
            self.play(
                Circumscribe(self.row.cells[2], color=GOOD),
                Circumscribe(self.row.cells[3], color=GOOD),
                run_time=0.7,
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.5)))
            self._found = line

    def _beat13(self):
        """Row-and-column: the correctness argument, drawn as the pair triangle."""
        with self.voiceover(text=BEATS[13]) as tr:
            swap_rails(self, headline("Each step deletes a row and a column."),
                       caption("one candidate gone, forever"))
            self.play(Restore(self.camera.frame), FadeOut(self._found, run_time=0.3))
            self.play(FadeOut(self.row.group), FadeOut(self.lo_ptr), FadeOut(self.hi_ptr),
                      FadeOut(self.tchip), run_time=0.45)

            dots = {}
            grid = VGroup()
            for i in range(len(ARR)):
                for j in range(i + 1, len(ARR)):
                    d = Dot(radius=0.075, color=PRIMARY)
                    d.move_to([-2.6 + j * 0.62, 1.2 - i * 0.5, 0])
                    dots[(i, j)] = d
                    grid.add(d)
            gone = [(i, j) for (i, j) in dots if i in (0, 1, 4, 5) or j in (0, 1, 4, 5)]
            self.play(FadeIn(grid), run_time=min(1.0, max(0.5, tr.duration * 0.25)))
            self.play(
                *[dots[k].animate.set_color(GONE).set_opacity(0.22) for k in gone],
                run_time=min(1.4, max(0.7, tr.duration * 0.35)),
            )
            tag = Text("15 pairs  →  1", font=MONO, font_size=BODY_FS, color=GOOD)
            tag.next_to(grid, DOWN, buff=0.32)
            self.play(FadeIn(tag, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._triangle = VGroup(grid, tag)

    def _beat14(self):
        """Linear, because neither pointer ever goes backwards.

        Sweep one pointer at a time (left-to-right, then right-to-left) and tint the cells it
        has visited, so 'never backwards' is something you watch rather than something you're
        told. Sweeping both at once made them cross, which read as an error.
        """
        with self.voiceover(text=BEATS[14]) as tr:
            swap_rails(self, headline("Each pointer moves at most n times."),
                       caption("never backwards"))
            self.play(FadeOut(self._triangle, run_time=0.35))
            rail = ArrayRow(list(range(1, 7)), cell=0.6, fs=SMALL_FS, show_index=False)
            rail.group.move_to([0, 0.35, 0])
            lo_m = Text("lo", font=MONO, font_size=SMALL_FS, color=ACCENT)
            lo_m.next_to(rail.cell(0), DOWN, buff=0.32)
            hi_m = Text("hi", font=MONO, font_size=SMALL_FS, color=PRIMARY)
            hi_m.next_to(rail.cell(0), UP, buff=0.32)
            total = Text("total steps ≤ 2n", font=MONO, font_size=BODY_FS, color=GOOD)
            total.move_to([0, -1.75, 0])
            self.play(FadeIn(rail.group), run_time=0.4)

            # lo walks forward across every cell — one direction only.
            self.play(FadeIn(lo_m), run_time=0.3)
            self.play(
                lo_m.animate.next_to(rail.cell(5), DOWN, buff=0.32),
                *[rail.focus(i, color=ACCENT, fill_opacity=0.16)[0] for i in range(6)],
                run_time=min(1.8, max(1.0, tr.duration * 0.35)),
            )
            # hi walks backward across every cell — again one direction only.
            self.play(
                hi_m.animate.next_to(rail.cell(5), UP, buff=0.32),
                run_time=0.35,
            )
            self.play(
                hi_m.animate.next_to(rail.cell(0), UP, buff=0.32),
                *[rail.focus(i, color=PRIMARY, fill_opacity=0.22)[0] for i in range(6)],
                run_time=min(1.8, max(1.0, tr.duration * 0.35)),
            )
            self.play(FadeIn(total, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._linear = VGroup(rail.group, lo_m, hi_m, total)

    def _beat15(self):
        """Complexity, stated cold — the pair the card says to know in your sleep."""
        with self.voiceover(text=BEATS[15]) as tr:
            swap_rails(self, headline("Linear time, constant extra space."),
                       caption("the nested loop was quadratic"))
            self.play(FadeOut(self._linear, run_time=0.35))
            brute = VGroup(
                Text("brute force", font=MONO, font_size=BODY_FS, color=GONE),
                MathTex(r"O(n^2)", color=GONE).scale(1.3),
            ).arrange(DOWN, buff=0.25)
            fast = VGroup(
                Text("two pointers", font=MONO, font_size=BODY_FS, color=GOOD),
                MathTex(r"O(n)", color=GOOD).scale(1.3),
            ).arrange(DOWN, buff=0.25)
            space = Text("space O(1)", font=MONO, font_size=SMALL_FS, color=GOOD)
            space.next_to(fast, DOWN, buff=0.3)
            both = VGroup(brute, fast).arrange(RIGHT, buff=1.9).move_to(stage_center(-0.15))
            arrow = Text("→", font=MONO, font_size=44, color=MUTED)
            arrow.move_to((brute.get_right() + fast.get_left()) / 2)
            self.play(FadeIn(brute), run_time=0.45)
            self.play(FadeIn(arrow), run_time=0.3)
            self.play(FadeIn(fast), run_time=0.45)
            self.play(FadeIn(space, shift=UP * 0.15), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._complexity = VGroup(both, arrow, space)

    def _beat16(self):
        """Shape A and its family."""
        with self.voiceover(text=BEATS[16]) as tr:
            swap_rails(self, headline("Shape A: converging from both ends."),
                       caption("pair sums, palindromes, most water"))
            self.play(FadeOut(self._complexity, run_time=0.3))
            items = VGroup(
                Text("two sum II", font=MONO, font_size=BODY_FS, color=INK),
                Text("valid palindrome", font=MONO, font_size=BODY_FS, color=INK),
                Text("container with most water", font=MONO, font_size=BODY_FS, color=INK),
                Text("3sum / 4sum", font=MONO, font_size=BODY_FS, color=INK),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
            box = card(items.width + 1.0, items.height + 0.8, color=WINDOW, fill=PANEL)
            box.move_to(stage_center(-0.2))
            items.move_to(box.get_center())
            self.play(FadeIn(box), run_time=0.35)
            self.play(
                *[FadeIn(t, shift=RIGHT * 0.2) for t in items],
                lag_ratio=0.35, run_time=min(1.6, max(0.8, tr.duration * 0.4)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._shapeA = VGroup(box, items)

    def _beat17(self):
        """Shape B: read/write compaction, with the finished-prefix mental model."""
        with self.voiceover(text=BEATS[17]) as tr:
            swap_rails(self, headline("Shape B: slow writes, fast scans."),
                       caption("slow marks the finished prefix"))
            self.play(FadeOut(self._shapeA, run_time=0.3))
            r = ArrayRow([2, 1, 2, 3, 2, 4], cell=0.66, fs=26, show_index=False)
            r.group.move_to([0, 0.5, 0])
            fin = r.cells[0].copy().set_fill(GOOD, opacity=0.28).set_stroke(GOOD, width=2.4)
            slow = Text("slow", font=MONO, font_size=SMALL_FS, color=GOOD)
            slow.next_to(r.cell(0), DOWN, buff=0.3)
            fast = Text("fast", font=MONO, font_size=SMALL_FS, color=ACCENT)
            fast.next_to(r.cell(0), UP, buff=0.3)
            note = Text("everything left of slow is final", font=MONO, font_size=SMALL_FS,
                        color=MUTED).move_to([0, -1.5, 0])
            self.play(FadeIn(r.cells), run_time=0.45)
            self.play(FadeIn(fin), FadeIn(slow), FadeIn(fast), run_time=0.4)
            self.play(
                fast.animate.next_to(r.cell(5), UP, buff=0.3),
                run_time=min(1.5, max(0.8, tr.duration * 0.35)),
            )
            self.play(FadeIn(note), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._shapeB = VGroup(r.cells, fin, slow, fast, note)

    def _beat18(self):
        """Shape C: three regions, plus the trap the card calls out."""
        with self.voiceover(text=BEATS[18]) as tr:
            swap_rails(self, headline("Shape C: three regions, one pass."),
                       caption("after swapping with high, don't move mid"))
            self.play(FadeOut(self._shapeB, run_time=0.3))
            r = ArrayRow([1, 0, 2, 1, 2, 0], cell=0.66, fs=26, show_index=False)
            r.group.move_to([0, 0.45, 0])
            spans = VGroup()
            for lo_i, hi_i, col in ((0, 0, ACCENT), (1, 3, MUTED), (4, 5, PRIMARY)):
                left = r.cell(lo_i).get_left()[0] - 0.05
                right = r.cell(hi_i).get_right()[0] + 0.05
                rect = Rectangle(
                    width=right - left, height=0.86, stroke_color=col, stroke_width=2.2,
                    fill_color=col, fill_opacity=0.18,
                )
                rect.move_to([(left + right) / 2, 0.45, 0])
                spans.add(rect)
            trap = Text("do NOT advance mid", font=MONO, font_size=BODY_FS, color=GONE)
            trap.move_to([0, -1.5, 0])
            self.play(FadeIn(r.cells), run_time=0.4)
            self.play(*[FadeIn(s) for s in spans],
                      run_time=min(1.3, max(0.7, tr.duration * 0.3)))
            self.play(Indicate(r.cell(5), color=GONE, scale_factor=1.15), run_time=0.6)
            self.play(FadeIn(trap, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._shapeC = VGroup(r.cells, spans, trap)

    def _beat19(self):
        """3Sum: fix one index, converge the rest, and skip duplicates after a hit."""
        with self.voiceover(text=BEATS[19]) as tr:
            swap_rails(self, headline("Three-sum: fix one, converge on two."),
                       caption("after a hit, skip duplicates"))
            self.play(FadeOut(self._shapeC, run_time=0.3))
            arr = [-4, -1, -1, 0, 1, 2]
            r = ArrayRow(arr, cell=0.66, fs=26, show_index=False)
            r.group.move_to([0, 0.45, 0])
            fix = Text("fixed i", font=MONO, font_size=SMALL_FS, color=WINDOW)
            fix.next_to(r.cell(1), UP, buff=0.35)
            lo_p = Text("lo", font=MONO, font_size=SMALL_FS, color=ACCENT)
            lo_p.next_to(r.cell(2), DOWN, buff=0.3)
            hi_p = Text("hi", font=MONO, font_size=SMALL_FS, color=PRIMARY)
            hi_p.next_to(r.cell(5), DOWN, buff=0.3)
            note = Text("skip the second -1", font=MONO, font_size=SMALL_FS, color=GONE)
            note.move_to([0, -1.5, 0])
            self.play(FadeIn(r.cells), run_time=0.4)
            self.play(FadeIn(fix), FadeIn(lo_p), FadeIn(hi_p), run_time=0.45)
            self.play(*r.focus(1, color=WINDOW), run_time=0.4)
            self.play(
                Indicate(r.cell(2), color=ACCENT, scale_factor=1.12),
                run_time=min(1.2, max(0.6, tr.duration * 0.3)),
            )
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._threesum = VGroup(r.cells, fix, lo_p, hi_p, note)

    def _beat20(self):
        """What breaks the pattern — the card's fourth 'know it cold' question."""
        with self.voiceover(text=BEATS[20]) as tr:
            swap_rails(self, headline("Know what breaks it."),
                       caption("monotonicity is the load-bearing assumption"))
            self.play(FadeOut(self._threesum, run_time=0.3))
            ok = chip("sorted  →  monotone", color=GOOD, fs=BODY_FS)
            bad = chip("negatives in a product window", color=GONE, fs=BODY_FS)
            both = VGroup(ok, bad).arrange(DOWN, buff=0.55).move_to(stage_center(0.1))
            note = Text("Subarray Product Less Than K needs all-positive input",
                        font=MONO, font_size=SMALL_FS, color=MUTED)
            note.move_to([0, -1.7, 0])
            self.play(FadeIn(ok, shift=UP * 0.2), run_time=0.45)
            self.play(FadeIn(bad, shift=UP * 0.2), run_time=0.45)
            self.play(Indicate(bad, color=GONE, scale_factor=1.08), run_time=0.6)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._breaks = VGroup(both, note)

    def _beat21(self):
        """Recognition signals — the checklist."""
        with self.voiceover(text=BEATS[21]) as tr:
            swap_rails(self, headline("When to reach for it."),
                       caption("sorted, or matching a pair"))
            self.play(FadeOut(self._breaks, run_time=0.3))
            yes = VGroup(
                Text("✓  input is sorted", font=MONO, font_size=BODY_FS, color=GOOD),
                Text("✓  pair / triplet / quadruplet", font=MONO, font_size=BODY_FS, color=GOOD),
                Text("✓  in-place, O(1) extra space", font=MONO, font_size=BODY_FS, color=GOOD),
                Text("✓  compared from both ends", font=MONO, font_size=BODY_FS, color=GOOD),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
            yes.move_to(stage_center(0.1))
            self.play(
                *[FadeIn(t, shift=RIGHT * 0.2) for t in yes],
                lag_ratio=0.32, run_time=min(1.7, max(0.9, tr.duration * 0.4)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._recognise = yes

    def _beat22(self):
        """The counter-tell: unsorted + exact values is a hash map, not this."""
        with self.voiceover(text=BEATS[22]) as tr:
            swap_rails(self, headline("The counter-tell: unsorted input."),
                       caption("that's a hash map instead"))
            self.play(FadeOut(self._recognise, run_time=0.3))
            no = Text("✗  unsorted, need exact values  →  hash map",
                      font=MONO, font_size=BODY_FS, color=GONE)
            cost = Text("sorting first costs n log n", font=MONO, font_size=SMALL_FS, color=MUTED)
            VGroup(no, cost).arrange(DOWN, buff=0.45).move_to(stage_center(0.0))
            self.play(FadeIn(no, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(cost, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._counter = VGroup(no, cost)

    def _beat23(self):
        """Recall card: one line the viewer can leave with."""
        with self.voiceover(text=BEATS[23]) as tr:
            swap_rails(self, headline("Two fingers, one pass, no going back."),
                       caption("sorted + pair  →  two pointers"))
            self.play(FadeOut(self._counter, run_time=0.3))
            box = card(8.6, 1.5, color=ACCENT, fill=PANEL)
            box.move_to(stage_center(-0.1))
            top = Text("Two Pointers", font=MONO, font_size=32, color=ACCENT)
            sub = Text("O(n) time  ·  O(1) space  ·  needs order",
                       font=MONO, font_size=SMALL_FS, color=MUTED)
            VGroup(top, sub).arrange(DOWN, buff=0.22).move_to(box.get_center())
            self.play(FadeIn(box, scale=0.96), run_time=0.45)
            self.play(Write(top), run_time=0.5)
            self.play(FadeIn(sub), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
