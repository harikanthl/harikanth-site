"""
Pattern 09 — Hash Maps.

The film follows the card's own argument: hook -> the job -> the rescanning cost -> count
once into a dictionary -> what key and value mean -> the counting pass -> every question is
now about the piles -> the frequency budget (and the divisor bug) -> complexity and the O(1)
space answer -> order matters, so a second pass -> the walk that finds the first singleton ->
pairs plus at most one odd centre -> multiset containment -> the three things that go wrong
-> the anti-signals -> recognition -> what breaks it -> the recall card.

Narration lives in BEATS and the animation is written against `tracker.duration`, so the
picture and the voice cannot drift: one file is the single source of truth for both.
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
    bg,
    card,
    caption,
    headline,
    stage_center,
    swap_rails,
)
from prebaked_voice import PrebakedVoiceMovingCameraScene
from shots import ArrayRow, chip, hash_buckets

PATTERN_SLUG = "hash-maps"
TITLE = "Hash Maps"
SUMMARY = "When the question is how many of each thing, count once and interrogate the counts."
SCENE_CLASS = "HashMaps"
POSTER_AT = 38.0

SOURCE = "loonbalxballpoon"
WORD = "balloon"
# (letter, how many the word needs) for the letters that matter, in first-seen order.
PILES = [("a", 1), ("b", 1), ("l", 2), ("o", 2), ("n", 1), ("x", 0)]

TABLE_X = [-3.25, -1.83, -0.41, 1.01]
TABLE_Y0 = 1.25
TABLE_DY = 0.54
CELL_W, CELL_H = 1.3, 0.46

BEATS = [
    # 0 hook
    "Stop rescanning the bag for every single bead.",
    # 1 the job
    "Here's the job: how many times can I spell balloon from these letters?",
    # 2 the slow way
    "The slow way picks up each letter and rummages through everything for its twins.",
    # 3 count once
    "The fast way counts everything once into a dictionary, then asks the dictionary.",
    # 4 key and value
    "The key is what you counted. The value is how many so far. Say that before you type.",
    # 5 the counting pass
    "One pass fills the piles: a two, b two, l four, o four, n two, x one.",
    # 6 every question is about the piles
    "Now every question is about the piles, not about the beads.",
    # 7 the need column
    "One balloon needs a one, b one, l two, o two, n one. Write that down as a second pile.",
    # 8 the bottleneck
    "The bottleneck letter decides, so divide each pile by what it needs and take the minimum. Two.",
    # 9 the divisor bug
    "Forget that divisor of two for l and o, and you'd answer four instead of two.",
    # 10 linear time
    "One pass to count, one pass to answer. That's linear time.",
    # 11 constant space
    "The map holds one entry per distinct key, and the alphabet is fixed at twenty-six, so that's constant space.",
    # 12 order matters
    "But order can matter. The first letter that appears exactly once needs a second pass.",
    # 13 the walk
    "Count first, then walk the original string and stop at the first pile holding one.",
    # 14 why two passes
    "It has to be two passes: you can't know a letter never repeats until you've read the whole string.",
    # 15 pairs
    "Every pile contributes its pairs, and if any pile is odd, one single letter sits in the middle.",
    # 16 only one centre
    "Only one, no matter how many odd piles there were. Writing a sum there is a bug.",
    # 17 letters, not pairs
    "And the answer counts letters, not pairs: floor each pile to even first.",
    # 18 containment
    "Containment is subtraction: take the note's letters out of the magazine and nothing should remain.",
    # 19 the missing key
    "What breaks it: a missing key. A plain dictionary raises; a counter reads zero.",
    # 20 the order trap
    "Don't iterate the dictionary and call that order. Walk the input, and say why.",
    # 21 the anti-signals
    "Know the anti-signals: a contiguous run wants a window, and a pair wants value to index.",
    # 22 recognise
    "Reach for it on counts, frequencies, anagrams, and can I build this from that.",
    # 23 recall
    "Count once, then ask the piles.",
]

CHAPTERS = {
    0: "The hook",
    1: "The job",
    2: "The slow way",
    3: "Count once",
    4: "Key and value",
    5: "The counting pass",
    6: "The questions move",
    7: "The budget",
    8: "The bottleneck",
    10: "Complexity",
    12: "Order can matter",
    13: "The walk",
    15: "Pairs and one centre",
    18: "Containment",
    19: "What goes wrong",
    21: "The anti-signals",
    23: "Recall",
}


class HashMaps(PrebakedVoiceMovingCameraScene):
    # ---------------------------------------------------------------------------- setup
    def construct(self):
        bg(self)
        self.boxes = {}
        for c in range(4):
            for r in range(6):
                b = card(CELL_W, CELL_H, color=STROKE, fill=PANEL)
                b.move_to(self._cell_center(r, c))
                self.boxes[(r, c)] = b
        for i in range(len(BEATS)):
            getattr(self, f"_beat{i}")()

    # ------------------------------------------------------------------------- utilities
    def _cell_center(self, r, c):
        return [TABLE_X[c], TABLE_Y0 - r * TABLE_DY, 0]

    def _col(self, c, rows=range(6)):
        return VGroup(*[self.boxes[(r, c)] for r in rows])

    def _put(self, r, c, text, color=INK):
        t = Text(str(text), font=MONO, font_size=SMALL_FS, color=color)
        t.move_to(self.boxes[(r, c)].get_center())
        self.boxes[(r, c)].add(t)
        return t

    def _header(self, c, text, color=MUTED):
        t = Text(text, font=MONO, font_size=SMALL_FS, color=color)
        t.move_to([TABLE_X[c], 1.68, 0])
        return t

    def _row_text(self, y, text, color=MUTED, fs=SMALL_FS, x=-0.6):
        return Text(text, font=MONO, font_size=fs, color=color).move_to([x, y, 0])

    def _have_texts(self, n_read):
        """The 'have' column as a pure function of how many letters have been read."""
        g = VGroup()
        for r, (ch, _) in enumerate(PILES):
            v = SOURCE[:n_read].count(ch)
            t = Text(str(v), font=MONO, font_size=SMALL_FS, color=INK if v else MUTED)
            t.move_to(self.boxes[(r, 1)].get_center())
            g.add(t)
        return g

    def _paint_read(self, row, t):
        """Move the reading head: the cell being read is the accent, the rest are plain."""
        j = max(0, min(len(SOURCE) - 1, int(t.get_value())))
        for k, box in enumerate(row.boxes):
            if k == j:
                box.set_stroke(ACCENT, width=2.6).set_fill(ACCENT, opacity=0.32)
            else:
                box.set_stroke(STROKE, width=1.6).set_fill(PANEL, opacity=1.0)

    def _readout(self, t, total, label="read"):
        return Text(
            f"{label} {max(0, min(total, int(t.get_value())))} of {total}",
            font=MONO,
            font_size=BODY_FS,
            color=ACCENT,
        ).move_to([3.5, 0.9, 0])

    def _verdict(self, t):
        i = max(0, min(len("aabbcde") - 1, int(t.get_value())))
        ch = "aabbcde"[i]
        return Text(
            f"counts['{ch}'] = {'aabbcde'.count(ch)}",
            font=MONO,
            font_size=SMALL_FS,
            color=MUTED,
        ).move_to([-0.4, -0.8, 0])

    def _fade(self, *mobs, run_time: float = 0.3):
        live = [m for m in mobs if m is not None]
        if live:
            self.play(*[FadeOut(m, run_time=run_time) for m in live])

    def _letter_card(self, ch, *, color=INK, w=0.5):
        b = card(w, w, color=color, fill=PANEL)
        t = Text(ch, font=MONO, font_size=SMALL_FS, color=color)
        t.move_to(b.get_center())
        return VGroup(b, t)

    # ---------------------------------------------------------------------------- beats
    def _beat0(self):
        """Hook: counting beats rescanning."""
        with self.voiceover(text=BEATS[0]) as tr:
            swap_rails(
                self, headline("Stop rescanning for every element."), caption("count once")
            )
            bad = chip("rescan for each: n^2", color=GONE, fs=BODY_FS)
            good = chip("count once: n", color=GOOD, fs=BODY_FS)
            row = VGroup(bad, good).arrange(RIGHT, buff=0.7).move_to(stage_center(-0.2))
            self.play(FadeIn(bad, shift=UP * 0.2), run_time=0.5)
            self.wait(0.25)
            self.play(FadeIn(good, shift=UP * 0.2), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._hook = row

    def _beat1(self):
        """The job: the source letters, as cells, and the word to build."""
        with self.voiceover(text=BEATS[1]) as tr:
            swap_rails(
                self, headline("How many times can I spell it?"), caption("count the letters")
            )
            self._fade(self._hook)
            self.src = ArrayRow(list(SOURCE), cell=0.38, buff=0.05, fs=16, show_index=False)
            self.src.cells.move_to([-2.2, 2.25, 0])
            self.target = chip(f'spell "{WORD}"', color=ACCENT, fs=BODY_FS)
            self.target.move_to([4.3, 2.25, 0])
            note = self._row_text(0.4, "one string of letters, one word to build", x=-1.2)
            self.play(
                FadeIn(self.src.cells, shift=UP * 0.2),
                FadeIn(self.target, scale=0.92),
                run_time=min(1.3, max(0.7, tr.duration * 0.32)),
            )
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._job_note = note

    def _beat2(self):
        """The slow way: for every letter, scan everything again."""
        with self.voiceover(text=BEATS[2]) as tr:
            swap_rails(
                self, headline("The slow way rescans the whole bag."), caption("n^2 comparisons")
            )
            code = VGroup(
                Text("for ch in s:", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("    rescan s for ch", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("        tally it", font=MONO, font_size=SMALL_FS, color=GONE),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
            box = card(code.width + 0.9, code.height + 0.6, color=STROKE, fill=PANEL)
            box.move_to([-1.2, -1.5, 0])
            code.move_to(box.get_center())
            tag = chip("n x n", color=GONE, fs=SMALL_FS)
            tag.next_to(box, RIGHT, buff=0.8)
            self.play(FadeIn(box), run_time=0.35)
            self.play(Write(code), run_time=min(1.1, max(0.5, tr.duration * 0.3)))
            self.play(FadeIn(tag, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._brute = VGroup(box, code, tag)

    def _beat3(self):
        """Count once: the key column, and the count column waiting to be filled."""
        with self.voiceover(text=BEATS[3]) as tr:
            swap_rails(
                self, headline("Count once into a dictionary."), caption("then ask the dictionary")
            )
            self._fade(self._brute, self._job_note, run_time=0.35)
            self.play(
                FadeIn(self._col(0)),
                FadeIn(self._col(1)),
                run_time=min(1.3, max(0.7, tr.duration * 0.35)),
            )
            letters = VGroup(
                *[
                    self._put(r, 0, ch)
                    for r, (ch, _) in enumerate(PILES)
                ]
            )
            self.play(
                *[FadeIn(t, shift=RIGHT * 0.15) for t in letters],
                lag_ratio=0.28,
                run_time=min(1.4, max(0.7, tr.duration * 0.35)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._letters = letters

    def _beat4(self):
        """Key and value, named out loud before any code."""
        with self.voiceover(text=BEATS[4]) as tr:
            swap_rails(
                self, headline("The key is the thing counted."), caption("the value is how many")
            )
            key_lb = self._header(0, "key", color=ACCENT)
            val_lb = self._header(1, "value", color=ACCENT)
            self.play(FadeIn(key_lb, scale=0.92), run_time=0.4)
            self.play(FadeIn(val_lb, scale=0.92), run_time=0.4)
            note = self._row_text(-2.35, "key = what you counted    value = how many so far", x=-0.6)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._kv = VGroup(key_lb, val_lb, note)

    def _beat5(self):
        """The counting pass, driven by computed state so the piles really fill."""
        with self.voiceover(text=BEATS[5]) as tr:
            swap_rails(
                self, headline("One pass fills every pile."), caption("no rescans")
            )
            self._fade(self._kv, run_time=0.3)
            t = ValueTracker(0)
            self.add(t)
            self.src.cells.add_updater(lambda m: self._paint_read(self.src, t))
            have = always_redraw(lambda: self._have_texts(int(t.get_value())))
            read = always_redraw(lambda: self._readout(t, len(SOURCE)))
            self.add(have, read)
            self.play(
                t.animate.set_value(len(SOURCE)),
                run_time=min(2.8, max(1.6, tr.duration * 0.55)),
                rate_func=lambda x: x,
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self.src.cells.clear_updaters()
            for box in self.src.boxes:
                box.set_stroke(STROKE, width=1.6).set_fill(PANEL, opacity=1.0)
            have.clear_updaters()
            read.clear_updaters()
            self.remove(t)
            # the filled count column stays: it is the spine of every later beat.
            self._have_final = have
            self._readout_live = read

    def _beat6(self):
        """The questions move from the beads to the piles."""
        with self.voiceover(text=BEATS[6]) as tr:
            swap_rails(
                self, headline("Every question is about the piles."), caption("not about the beads")
            )
            self._fade(self._readout_live, run_time=0.3)
            need_h = self._header(2, "need")
            self.play(self.src.cells.animate.set_opacity(0.3), run_time=0.5)
            self.play(FadeIn(self._col(2)), FadeIn(need_h), run_time=0.45)
            note = self._row_text(-2.35, "the input is now just evidence; the counts are the subject",
                                 x=-0.6)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._piles_note = note
            self._head_need = need_h

    def _beat7(self):
        """The budget: one word needs these many of each letter."""
        with self.voiceover(text=BEATS[7]) as tr:
            swap_rails(
                self, headline("One word needs a budget."), caption("need: 1, 1, 2, 2, 1")
            )
            self._fade(self._piles_note, run_time=0.3)
            needs = VGroup()
            for r, (ch, n) in enumerate(PILES):
                needs.add(self._put(r, 2, n if n else "-", color=INK if n else MUTED))
            self.play(
                *[FadeIn(t, shift=RIGHT * 0.15) for t in needs],
                lag_ratio=0.25,
                run_time=min(1.4, max(0.7, tr.duration * 0.35)),
            )
            note = self._row_text(-2.35, "l and o are needed twice per word", color=MUTED, x=-0.6)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._needs_row = needs
            self._need_note = note

    def _beat8(self):
        """The bottleneck letter decides: min over have // need."""
        with self.voiceover(text=BEATS[8]) as tr:
            swap_rails(
                self, headline("The bottleneck letter decides."), caption("min of have // need")
            )
            self._fade(self._need_note, run_time=0.3)
            quot_h = self._header(3, "// need", color=ACCENT)
            quots = VGroup()
            for r, (ch, n) in enumerate(PILES):
                if n:
                    quots.add(self._put(r, 3, SOURCE.count(ch) // n, color=ACCENT))
                else:
                    quots.add(self._put(r, 3, "-", color=MUTED))
            self.play(FadeIn(self._col(3)), FadeIn(quot_h), run_time=0.45)
            self.play(
                *[FadeIn(t, scale=0.94) for t in quots],
                lag_ratio=0.25,
                run_time=min(1.4, max(0.8, tr.duration * 0.35)),
            )
            self.play(
                Indicate(self.boxes[(2, 1)], color=ACCENT, scale_factor=1.06),
                Indicate(self.boxes[(3, 1)], color=ACCENT, scale_factor=1.06),
                run_time=0.7,
            )
            answer = chip("2 balloons", color=GOOD, fs=BODY_FS)
            answer.move_to([3.2, -0.4, 0])
            self.play(FadeIn(answer, scale=0.94), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._table = VGroup(self._col(0), self._col(1), self._col(2), self._col(3),
                                 quot_h, self._head_need)
            self._quot_row = quots
            self._answer = answer

    def _beat9(self):
        """The divisor bug: the letter that appears twice in the target."""
        with self.voiceover(text=BEATS[9]) as tr:
            swap_rails(
                self, headline("The divisor is not one."), caption("forget it and you answer four")
            )
            wrong = chip("without // need  ->  4", color=GONE, fs=SMALL_FS)
            wrong.move_to([3.2, -1.2, 0])
            right = Text("4 // 2 = 2", font=MONO, font_size=SMALL_FS, color=GOOD)
            right.move_to([3.2, -1.9, 0])
            self.play(FadeIn(wrong, shift=UP * 0.15), run_time=0.45)
            self.play(Indicate(self.boxes[(2, 3)], color=ACCENT, scale_factor=1.12), run_time=0.6)
            self.play(FadeIn(right, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._divisor = VGroup(wrong, right)

    def _beat10(self):
        """Complexity, time first."""
        with self.voiceover(text=BEATS[10]) as tr:
            swap_rails(
                self, headline("Two passes, both linear."), caption("O(n) time")
            )
            self._fade(self._divisor, self._answer, self._table, self._have_final, run_time=0.35)
            brute = Text("rescan for each element", font=MONO, font_size=BODY_FS, color=GONE)
            brute.move_to([-3.0, -1.0, 0])
            fast = Text("count, then ask", font=MONO, font_size=BODY_FS, color=GOOD)
            fast.move_to([2.6, -1.0, 0])
            arrow = Text("->", font=MONO, font_size=36, color=MUTED)
            arrow.move_to([-0.2, -1.0, 0])
            cost = MathTex(r"O(n^2)  \rightarrow  O(n)", color=GOOD).scale(1.15)
            cost.move_to([-0.3, -2.05, 0])
            self.play(FadeIn(brute), run_time=0.4)
            self.play(FadeIn(arrow), run_time=0.25)
            self.play(FadeIn(fast), run_time=0.4)
            self.play(Write(cost), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._time = VGroup(brute, fast, arrow, cost)

    def _beat11(self):
        """The space answer, said before they ask."""
        with self.voiceover(text=BEATS[11]) as tr:
            swap_rails(
                self, headline("The space is one entry per key."), caption("26 letters = O(1)")
            )
            self._fade(self._time, run_time=0.4)
            a = chip("one entry per distinct key", color=PRIMARY, fs=SMALL_FS)
            b = chip("alphabet fixed at 26  ->  O(1)", color=GOOD, fs=SMALL_FS)
            row = VGroup(a, b).arrange(DOWN, buff=0.45).move_to([-0.4, 0.3, 0])
            note = self._row_text(-1.6, "say it before the interviewer asks", x=-0.4)
            self.play(FadeIn(a, shift=UP * 0.15), run_time=0.45)
            self.play(FadeIn(b, shift=UP * 0.15), run_time=0.45)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._space = VGroup(row, note)

    def _beat12(self):
        """Shape B: the answer needs the input's order."""
        with self.voiceover(text=BEATS[12]) as tr:
            swap_rails(
                self, headline("But order can matter."), caption("the first singleton")
            )
            self._fade(self._space, self.src.cells, self.target, run_time=0.35)
            self.arr = ArrayRow(list("aabbcde"), cell=0.62, fs=22)
            self.arr.group.move_to([-0.4, 0.7, 0])
            counts = VGroup()
            for i, ch in enumerate("aabbcde"):
                t = Text(str("aabbcde".count(ch)), font=MONO, font_size=SMALL_FS,
                         color=GOOD if "aabbcde".count(ch) == 1 else MUTED)
                t.next_to(self.arr.cell(i), DOWN, buff=0.62)
                counts.add(t)
            note = self._row_text(-1.5, "count first, then walk the input for position", x=-0.4)
            self.play(FadeIn(self.arr.cells), FadeIn(self.arr.idx), run_time=0.45)
            self.play(FadeIn(counts, shift=UP * 0.15), run_time=0.5)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._arr_note = note
            self._counts_row = counts

    def _beat13(self):
        """The walk: stop at the first pile holding one."""
        with self.voiceover(text=BEATS[13]) as tr:
            swap_rails(
                self, headline("Stop at the first pile holding one."), caption("index 4 is 'c'")
            )
            self._fade(self._arr_note, run_time=0.25)
            t = ValueTracker(0)
            self.add(t)
            self.arr.cells.add_updater(lambda m: self._paint_read(self.arr, t))
            verdict = always_redraw(lambda: self._verdict(t))
            self.add(verdict)
            self.play(
                t.animate.set_value(4),
                run_time=min(2.4, max(1.4, tr.duration * 0.5)),
                rate_func=lambda x: x,
            )
            self.arr.cells.clear_updaters()
            verdict.clear_updaters()
            self.remove(t)
            self.play(
                self.arr.boxes[4].animate.set_stroke(GOOD, width=2.6).set_fill(GOOD, opacity=0.32),
                run_time=0.4,
            )
            hit = Text("first non-repeating: 'c'", font=MONO, font_size=BODY_FS, color=GOOD)
            hit.move_to([-0.4, -1.9, 0])
            self.play(FadeIn(hit, scale=0.95), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._walk2 = VGroup(verdict, hit)

    def _beat14(self):
        """Why the second pass cannot be merged into the first."""
        with self.voiceover(text=BEATS[14]) as tr:
            swap_rails(
                self, headline("You can't know until you've read it all."), caption("so two passes")
            )
            self._fade(self.arr.group, self._counts_row, self._walk2, run_time=0.35)
            row1 = VGroup(
                chip("pass 1: count every letter", color=PRIMARY, fs=SMALL_FS),
                Text("counts[ch] += 1", font=MONO, font_size=SMALL_FS, color=MUTED),
            ).arrange(RIGHT, buff=0.4)
            row2 = VGroup(
                chip("pass 2: walk the input for order", color=ACCENT, fs=SMALL_FS),
                Text("for i, ch in enumerate(s)", font=MONO, font_size=SMALL_FS, color=MUTED),
            ).arrange(RIGHT, buff=0.4)
            both = VGroup(row1, row2).arrange(DOWN, buff=0.5).move_to([-0.5, 0.7, 0])
            note = self._row_text(-1.3, "a letter is non-repeating only once the string ends", x=-0.4)
            self.play(FadeIn(row1, shift=UP * 0.15), run_time=0.5)
            self.play(FadeIn(row2, shift=UP * 0.15), run_time=0.5)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._passes = VGroup(both, note)

    def _beat15(self):
        """Pairs, plus at most one letter in the middle."""
        with self.voiceover(text=BEATS[15]) as tr:
            swap_rails(
                self, headline("Piles give you pairs."), caption("plus one odd centre")
            )
            self._fade(self._passes, run_time=0.35)
            piles = VGroup(
                *[
                    chip(f"{ch} x {n}", color=PRIMARY, fs=SMALL_FS)
                    for ch, n in (("a", 2), ("b", 3), ("c", 2))
                ]
            ).arrange(RIGHT, buff=0.5).move_to([-0.4, 1.3, 0])
            tokens = VGroup(*[self._letter_card(ch, color=GOOD) for ch in "aabbcc"])
            tokens.arrange(RIGHT, buff=0.12)
            centre = self._letter_card("b", color=ACCENT)
            plus = Text("+", font=MONO, font_size=BODY_FS, color=MUTED)
            row = VGroup(tokens, plus, centre).arrange(RIGHT, buff=0.3).move_to([-0.4, 0.0, 0])
            note = self._row_text(-1.4, "every pile hands over its pairs", x=-0.4)
            self.play(FadeIn(piles, shift=UP * 0.15), run_time=0.5)
            self.play(FadeIn(tokens), run_time=0.45)
            self.play(FadeIn(plus), FadeIn(centre, scale=0.9), run_time=0.45)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._piles_row = piles
            self._token_row = VGroup(tokens, plus, centre)
            self._pairs_note = note

    def _beat16(self):
        """At most one centre, no matter how many odd piles."""
        with self.voiceover(text=BEATS[16]) as tr:
            swap_rails(
                self, headline("At most one letter in the middle."), caption("any() not sum()")
            )
            warn = Text("x  several odd piles, still ONE centre", font=MONO, font_size=SMALL_FS,
                        color=GONE).move_to([-0.4, -2.1, 0])
            total = chip("6 + 1 = 7 letters", color=GOOD, fs=BODY_FS)
            total.move_to([-0.4, 2.0, 0])
            self.play(FadeIn(warn, shift=UP * 0.15), run_time=0.45)
            self.play(Indicate(self._token_row[2], color=ACCENT, scale_factor=1.25), run_time=0.7)
            self.play(FadeIn(total, scale=0.94), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._centre = VGroup(warn, total)

    def _beat17(self):
        """Letters, not pairs: floor each pile to even."""
        with self.voiceover(text=BEATS[17]) as tr:
            swap_rails(
                self, headline("Count letters, not pairs."), caption("v // 2 * 2")
            )
            self._fade(self._piles_row, self._token_row, self._pairs_note, self._centre,
                       run_time=0.3)
            good = Text("v // 2 * 2   ->  letters kept", font=MONO, font_size=BODY_FS, color=GOOD)
            good.move_to([-0.4, 0.9, 0])
            bad = Text("v // 2       ->  that's pairs, not letters", font=MONO,
                       font_size=SMALL_FS, color=GONE).move_to([-0.4, -0.1, 0])
            self.play(FadeIn(good, shift=UP * 0.15), run_time=0.45)
            self.play(FadeIn(bad, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._floor = VGroup(good, bad)

    def _beat18(self):
        """Containment is subtraction."""
        with self.voiceover(text=BEATS[18]) as tr:
            swap_rails(
                self, headline("Containment is subtraction."), caption("nothing should remain")
            )
            self._fade(self._floor, run_time=0.3)
            note_b = hash_buckets(["a : 1", "b : 1"], bucket_w=1.5, row_h=0.46, buff=0.14)
            note_b.move_to([-3.6, 0.5, 0])
            mag_b = hash_buckets(["a : 2", "b : 1"], bucket_w=1.5, row_h=0.46, buff=0.14)
            mag_b.move_to([-0.9, 0.5, 0])
            lb1 = Text("note", font=MONO, font_size=SMALL_FS, color=PRIMARY)
            lb1.next_to(note_b, UP, buff=0.16)
            lb2 = Text("magazine", font=MONO, font_size=SMALL_FS, color=PRIMARY)
            lb2.next_to(mag_b, UP, buff=0.16)
            minus = Text("-", font=MONO, font_size=40, color=MUTED)
            minus.move_to([-2.25, 0.5, 0])
            eq = Text("=", font=MONO, font_size=34, color=MUTED)
            eq.move_to([0.15, 0.5, 0])
            empty = chip("nothing left -> buildable", color=GOOD, fs=SMALL_FS)
            empty.move_to([3.2, 0.5, 0])
            note = self._row_text(-1.1, "a Counter subtraction drops non-positive entries", x=-0.6)
            self.play(FadeIn(note_b), FadeIn(lb1), run_time=0.4)
            self.play(FadeIn(minus), FadeIn(mag_b), FadeIn(lb2), run_time=0.45)
            self.play(FadeIn(eq), FadeIn(empty), run_time=0.45)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._contain = VGroup(note_b, mag_b, lb1, lb2, minus, eq, empty, note)

    def _beat19(self):
        """The missing key: a crash or a zero."""
        with self.voiceover(text=BEATS[19]) as tr:
            swap_rails(
                self, headline("Know what a missing key does."), caption("Counter: 0, dict: KeyError")
            )
            self._fade(self._contain, run_time=0.3)
            good = chip("Counter[key]  ->  0", color=GOOD, fs=BODY_FS)
            good.move_to([-0.4, 0.9, 0])
            bad = chip("dict[key]  ->  KeyError", color=GONE, fs=BODY_FS)
            bad.move_to([-0.4, -0.3, 0])
            note = self._row_text(-1.5, "or d.get(key, 0) on a plain dictionary", x=-0.4)
            self.play(FadeIn(good, shift=UP * 0.15), run_time=0.45)
            self.play(FadeIn(bad, shift=UP * 0.15), run_time=0.45)
            self.play(Indicate(bad, color=GONE, scale_factor=1.06), run_time=0.6)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._keyerr = VGroup(good, bad, note)

    def _beat20(self):
        """The order trap: the dict is not the input."""
        with self.voiceover(text=BEATS[20]) as tr:
            swap_rails(
                self, headline("Don't call the dict an order."), caption("walk the input instead")
            )
            self._fade(self._keyerr, run_time=0.3)
            d = Text("for ch, n in counts.items()", font=MONO, font_size=SMALL_FS, color=GONE)
            d.move_to([-0.4, 0.9, 0])
            s = Text("for i, ch in enumerate(s)", font=MONO, font_size=SMALL_FS, color=GOOD)
            s.move_to([-0.4, -0.1, 0])
            note = self._row_text(-1.2, "the dict knows how many; the string knows where", x=-0.4)
            self.play(FadeIn(d, shift=RIGHT * 0.15), run_time=0.45)
            self.play(Indicate(d, color=GONE, scale_factor=1.05), run_time=0.6)
            self.play(FadeIn(s, shift=RIGHT * 0.15), run_time=0.45)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._order = VGroup(d, s, note)

    def _beat21(self):
        """The anti-signals."""
        with self.voiceover(text=BEATS[21]) as tr:
            swap_rails(
                self, headline("The anti-signals."), caption("windows, and value to index")
            )
            self._fade(self._order, run_time=0.3)
            a = Text("x  a contiguous run  ->  sliding window", font=MONO, font_size=SMALL_FS,
                     color=GONE).move_to([-0.4, 0.7, 0])
            b = Text("x  pair summing to a target  ->  value to index", font=MONO,
                     font_size=SMALL_FS, color=GONE).move_to([-0.4, -0.3, 0])
            note = self._row_text(-1.4, "counting alone loses adjacency and position", x=-0.4)
            self.play(FadeIn(a, shift=RIGHT * 0.15), run_time=0.45)
            self.play(FadeIn(b, shift=RIGHT * 0.15), run_time=0.45)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._anti = VGroup(a, b, note)

    def _beat22(self):
        """Recognition signals."""
        with self.voiceover(text=BEATS[22]) as tr:
            swap_rails(
                self, headline("When to reach for a map."), caption("counts, not positions")
            )
            self._fade(self._anti, run_time=0.3)
            yes = VGroup(
                Text("count, frequency, occurrences, anagram", font=MONO, font_size=SMALL_FS,
                     color=GOOD),
                Text("first or any character that appears once", font=MONO, font_size=SMALL_FS,
                     color=GOOD),
                Text("how many times can you form or spell X", font=MONO, font_size=SMALL_FS,
                     color=GOOD),
                Text("can A be built from B, a multiset check", font=MONO, font_size=SMALL_FS,
                     color=GOOD),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.26)
            yes.move_to(stage_center(0.0))
            self.play(
                *[FadeIn(t, shift=RIGHT * 0.2) for t in yes],
                lag_ratio=0.32,
                run_time=min(1.7, max(0.9, tr.duration * 0.4)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._yes = yes

    def _beat23(self):
        """Recall card, and the camera pushes into it."""
        with self.voiceover(text=BEATS[23]) as tr:
            swap_rails(
                self, headline("Count once, then ask the piles."), caption("the whole pattern")
            )
            self._fade(self._yes)
            box = card(8.6, 1.5, color=ACCENT, fill=PANEL)
            box.move_to(stage_center(-0.1))
            top = Text("Hash Maps", font=MONO, font_size=32, color=ACCENT)
            sub = Text("O(n) time  .  O(k) space  .  count, then interrogate",
                       font=MONO, font_size=SMALL_FS, color=MUTED)
            VGroup(top, sub).arrange(DOWN, buff=0.22).move_to(box.get_center())
            self.play(FadeIn(box, scale=0.96), run_time=0.45)
            self.play(Write(top), run_time=0.5)
            self.play(FadeIn(sub), run_time=0.35)
            self.camera.frame.save_state()  # bare: stores, doesn't animate
            self.play(
                self.camera.auto_zoom([box], margin=1.0),
                run_time=min(1.4, max(0.8, tr.duration * 0.32)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=1.0)))
            self.play(Restore(self.camera.frame), run_time=0.6)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
