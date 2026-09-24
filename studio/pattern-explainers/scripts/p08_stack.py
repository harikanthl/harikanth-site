"""
Pattern 08 — Stack.

The film follows the pattern card's own argument: the pile of plates -> the top is the most
recent unfinished business -> the cancelling shape on brackets (push, match-and-pop, what is
left is the answer, and the two ways to be invalid) -> the monotonic shape on next-greater
(push what is waiting, the pop is where the answer is written, leftovers take the default) ->
why the nested while is still O(n) -> the four decisions -> ties and empty pops -> which pile
is the answer -> the counter-tell -> the recall card.

The spine is one locally-defined stack of plates: it grows as items are pushed, the top plate
is the thing the narration is talking about, and the pop is the beat where the answer gets
written down.

Narration lives in BEATS and every animation is written against `tracker.duration`, so the
picture and the voice cannot drift: one file is the source of truth for both.
"""

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    FadeIn,
    FadeOut,
    GrowArrow,
    Indicate,
    Line,
    MathTex,
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
    MUTED,
    PANEL,
    PRIMARY,
    SMALL_FS,
    STROKE,
    WINDOW,
    bg,
    caption,
    card,
    headline,
    rails_of,
    rule,
    stage_center,
    swap_rails,
)
from prebaked_voice import PrebakedVoiceMovingCameraScene
from shots import ArrayRow, chip

PATTERN_SLUG = "stack"
TITLE = "Stack"
SUMMARY = "Hold what is still unresolved, most recent on top: O(n), even with a loop inside a loop."
SCENE_CLASS = "StackPattern"
POSTER_AT = 26.0

TOKENS = ["(", "[", "{", "}", "]", ")"]
NUMS = [3, 1, 4, 1, 5]
TEMPS = [73, 74, 75, 71, 69, 72, 76, 73]
DAYS = [1, 1, 4, 2, 1, 1, 0, 0]

BEATS = [
    # 0 hook
    "A stack holds the things that are still unresolved, most recent on top.",
    # 1 the one-sentence version
    "Any question about the nearest unfinished item is a stack question.",
    # 2 ELI5
    "Picture a pile of plates. You can only touch the top one.",
    # 3 the feature
    "That restriction is the feature. The top of the pile is always the most recent unfinished business.",
    # 4 push
    "So an opening bracket goes on the stack. It is unresolved, and it waits.",
    # 5 match and pop
    "A closing bracket can only close the one on top. Match it, and it comes off.",
    # 6 cancelling
    "That is the cancelling shape. Pairs destroy each other, and whatever is left is the answer.",
    # 7 invalid on empty
    "A closing bracket on an empty stack is not an error to guard. It is the answer: invalid.",
    # 8 leftovers
    "Leftover openers at the end mean the same thing.",
    # 9 the second shape
    "The second shape is not cancelling. It is waiting for something bigger.",
    # 10 next greater
    "Next greater element: for each value, the first value to its right that beats it.",
    # 11 brute force
    "The obvious way is a nested loop, and that is quadratic.",
    # 12 what waits
    "The stack holds the values still waiting, and they stay in decreasing order.",
    # 13 the pop
    "When a bigger value arrives, it is exactly what the top was waiting for. Pop it, and write the answer.",
    # 14 push the new one
    "Then push the new value. Everything still waiting is bigger than it.",
    # 15 leftovers
    "Whatever never gets popped never found its answer, so it takes the default answer instead.",
    # 16 four decisions
    "Four decisions: increasing or decreasing, index or value, what the pop writes, and what the leftovers mean.",
    # 17 index or value
    "Store indices whenever the answer is a distance, like days until a warmer day.",
    # 18 why O(n)
    "Each element is pushed once and popped at most once, so the inner loop does at most n work in total.",
    # 19 amortised
    "That is amortised constant per element. Say amortised out loud; it is the follow-up question, every time.",
    # 20 what breaks it
    "Two things break it: ties and empty pops. Strictly less keeps equals waiting; less-or-equal pops them.",
    # 21 which pile
    "Never index an empty stack. And know which pile is the answer: cancelling is the survivors, monotonic is what was popped.",
    # 22 counter-tell
    "A stack reverses a string fine, but two pointers do it in constant space.",
    # 23 recall
    "Still unresolved? Most recent goes on top.",
]

CHAPTERS = {
    0: "The hook",
    1: "The one-sentence version",
    2: "Plates",
    4: "Cancelling: brackets",
    7: "The two ways to be invalid",
    9: "Monotonic: next greater",
    13: "The pop writes the answer",
    16: "The four decisions",
    18: "Why it is still O(n)",
    20: "What breaks it",
    22: "The counter-tell",
    23: "Recall",
}


class PlateStack:
    """A stack of plates, defined here because `shots.py` has no stack primitive.

    Plates are laid bottom-up on a fixed baseline, so the pile grows upward as items are
    pushed. Each entry is a VGroup of (plate box, plate label[, value tag]) so a pop removes
    the plate and everything attached to it in one animation.
    """

    def __init__(self, *, x=0.0, base_y=-1.5, w=1.7, h=0.5, buff=0.09, fs=SMALL_FS):
        self.x = x
        self.base_y = base_y
        self.w = w
        self.h = h
        self.buff = buff
        self.fs = fs
        self.plates = []

    def slot(self, i):
        return [self.x, self.base_y + self.h / 2 + i * (self.h + self.buff), 0]

    def group(self):
        return VGroup(*self.plates)

    def make(self, label="", value=None, color=PRIMARY):
        box = card(self.w, self.h, color=color, fill=PANEL)
        entry = VGroup(box)
        if label:
            t = Text(label, font=MONO, font_size=self.fs, color=color)
            if t.width > box.width - 0.14:
                t.scale_to_fit_width(box.width - 0.14)
            t.move_to(box.get_center())
            entry.add(t)
        entry.move_to(self.slot(len(self.plates)))
        if value is not None:
            vt = Text(str(value), font=MONO, font_size=16, color=MUTED)
            vt.next_to(box, RIGHT, buff=0.22)
            entry.add(vt)
        self.plates.append(entry)
        return entry

    def take(self):
        return self.plates.pop()

    def top(self):
        return self.plates[-1] if self.plates else None

    def base_label(self, text):
        lb = Text(text, font=MONO, font_size=SMALL_FS, color=MUTED)
        lb.move_to([self.x, self.base_y - 0.3, 0])
        return lb


class StackPattern(PrebakedVoiceMovingCameraScene):
    # ---------------------------------------------------------------------------- setup
    def construct(self):
        bg(self)
        self.stack = None
        self.phase_a = []
        for i in range(len(BEATS)):
            getattr(self, f"_beat{i}")()

    # ------------------------------------------------------------------------- utilities
    def _stage_mobjects(self):
        """Everything drawn except the rails and the hairline — the shot the camera frames."""
        skip = {id(m) for m in rails_of(self)}
        if getattr(self, "rule_line", None) is not None:
            skip.add(id(self.rule_line))
        return [
            m
            for m in self.mobjects
            if id(m) not in skip
            and (len(getattr(m, "points", [])) or len(getattr(m, "submobjects", [])))
        ]

    def _push(self, tracker, label="", value=None, color=PRIMARY, k=0.12, lo=0.32, hi=0.62):
        """Stage a plate above the pile and settle it on top — the push, made visible."""
        entry = self.stack.make(label, value=value, color=color)
        entry.shift(UP * 0.7)
        self.play(
            entry.animate.shift(DOWN * 0.7),
            run_time=min(hi, max(lo, tracker.duration * k)),
        )
        return entry

    def _pop(self, tracker, k=0.1, lo=0.28, hi=0.55):
        entry = self.stack.take()
        self.play(
            entry.animate.shift(UP * 0.6).set_opacity(0.0),
            run_time=min(hi, max(lo, tracker.duration * k)),
        )
        self.remove(entry)
        return entry

    def _verdict(self, text, color):
        c = chip(text, color=color, fs=SMALL_FS)
        c.move_to([3.15, -0.95, 0])
        return c

    # ---------------------------------------------------------------------------- beats
    def _beat0(self):
        """Hook: one claim, and the word that does all the work."""
        with self.voiceover(text=BEATS[0]) as tr:
            swap_rails(
                self,
                headline("A stack holds what's still unresolved."),
                caption("most recent on top"),
            )
            self.rule_line = rule()
            self.play(FadeIn(self.rule_line), run_time=0.3)
            claim = chip("the nearest unfinished item", color=ACCENT, fs=BODY_FS)
            claim.move_to(stage_center(0.55))
            sub = Text("brackets  ·  next greater  ·  undo", font=MONO, font_size=SMALL_FS,
                       color=MUTED)
            sub.move_to(stage_center(-0.45))
            self.play(FadeIn(claim, shift=UP * 0.2), run_time=min(1.0, max(0.5, tr.duration * 0.28)))
            self.play(FadeIn(sub, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._hook = VGroup(claim, sub)

    def _beat1(self):
        """The one-sentence version: the tell is in your own restatement."""
        with self.voiceover(text=BEATS[1]) as tr:
            swap_rails(
                self,
                headline("Nearest unfinished item? Use a stack."),
                caption("the one-sentence version"),
            )
            self.play(FadeOut(self._hook, run_time=0.3))
            tell = Text("the word \"most recent\" in your restatement",
                        font=MONO, font_size=BODY_FS, color=INK)
            tell.move_to(stage_center(0.1))
            cost = VGroup(
                Text("brute force: O(n²)", font=MONO, font_size=BODY_FS, color=GONE),
                Text("stack: O(n)", font=MONO, font_size=BODY_FS, color=GOOD),
            ).arrange(RIGHT, buff=1.2).move_to(stage_center(-1.1))
            self.play(FadeIn(tell, shift=UP * 0.2), run_time=min(1.1, max(0.6, tr.duration * 0.3)))
            self.play(FadeIn(cost, shift=UP * 0.15), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._onesent = VGroup(tell, cost)

    def _beat2(self):
        """ELI5: the pile of plates. This pile is the film's persistent anchor."""
        with self.voiceover(text=BEATS[2]) as tr:
            swap_rails(
                self,
                headline("Think of a pile of plates."),
                caption("you can only touch the top"),
            )
            self.play(FadeOut(self._onesent, run_time=0.3))
            self.stack = PlateStack(x=0.0, base_y=-1.5, w=1.7, h=0.5, buff=0.09)
            base = self.stack.base_label("stack")
            self.play(FadeIn(base), run_time=0.3)
            for _ in range(3):
                self._push(tr, k=0.11, lo=0.3, hi=0.55)
            top = Text("top", font=MONO, font_size=SMALL_FS, color=ACCENT)
            top.next_to(self.stack.top(), LEFT, buff=0.3)
            self.play(FadeIn(top), run_time=0.35)
            self.top_lbl = top
            self.phase_a += [base, top]
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat3(self):
        """The restriction is the feature — the top is the most recent unfinished thing."""
        with self.voiceover(text=BEATS[3]) as tr:
            swap_rails(
                self,
                headline("That restriction is the feature."),
                caption("top = most recent unfinished"),
            )
            self.play(Indicate(self.stack.top(), color=ACCENT, scale_factor=1.08), run_time=0.6)
            why = chip("unfinished business", color=ACCENT, fs=SMALL_FS)
            why.next_to(self.stack.top(), RIGHT, buff=0.45)
            self.play(FadeIn(why, shift=LEFT * 0.2), run_time=0.45)
            self.phase_a.append(why)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat4(self):
        """Push: an opening bracket is unresolved, so it waits on the pile."""
        with self.voiceover(text=BEATS[4]) as tr:
            swap_rails(
                self,
                headline("An opening bracket waits on the stack."),
                caption("push = unresolved"),
            )
            self.play(
                *[FadeOut(e) for e in self.stack.plates], FadeOut(self.top_lbl), run_time=0.35
            )
            self.stack.plates = []
            self.phase_a = [m for m in self.phase_a if m is not self.top_lbl]
            self.tok = ArrayRow(TOKENS, cell=0.62, fs=26, show_index=False)
            self.tok.group.move_to([0, 1.85, 0])
            self.play(FadeIn(self.tok.group, shift=DOWN * 0.2), run_time=0.45)
            self.phase_a.append(self.tok.group)
            for i in range(3):
                self.play(*self.tok.focus(i, color=ACCENT), run_time=0.18)
                self._push(tr, TOKENS[i], color=PRIMARY, k=0.12, lo=0.3, hi=0.6)
                if i < 2:
                    self.play(self.tok.cells[i].animate.set_opacity(0.3), run_time=0.15)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat5(self):
        """Match and pop — and the camera moves into the exact pair being spoken about."""
        with self.voiceover(text=BEATS[5]) as tr:
            swap_rails(
                self,
                headline("A closing bracket closes the top."),
                caption("match the top, then pop"),
            )
            self.play(*self.tok.focus(3, color=ACCENT), run_time=0.3)
            match = Arrow(
                self.tok.cell(3).get_bottom() + DOWN * 0.06,
                self.stack.top().get_top() + UP * 0.06,
                buff=0,
                color=GOOD,
                stroke_width=2.8,
                path_arc=-0.7,
                max_tip_length_to_length_ratio=0.24,
            )
            lbl = Text("matches", font=MONO, font_size=15, color=GOOD)
            lbl.move_to([-0.55, 1.0, 0])
            self.play(GrowArrow(match), FadeIn(lbl), run_time=min(1.0, max(0.5, tr.duration * 0.26)))
            self.phase_a += [match, lbl]
            self.camera.frame.save_state()  # bare: stores, doesn't animate
            self.play(
                self.camera.auto_zoom(self._stage_mobjects(), margin=0.9),
                run_time=min(1.1, max(0.6, tr.duration * 0.28)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.5)))

    def _beat6(self):
        """Cancelling: the pair annihilates, and the survivors ARE the answer."""
        with self.voiceover(text=BEATS[6]) as tr:
            swap_rails(
                self,
                headline("Cancelling: pairs destroy each other."),
                caption("what's left is the answer"),
            )
            self.play(Restore(self.camera.frame), run_time=0.8)
            self.play(
                FadeOut(self.phase_a[-2]),
                FadeOut(self.phase_a[-1]),
                FadeOut(self.phase_a[-4]),
                run_time=0.25,
            )
            self._pop(tr, k=0.1)
            for i in (4, 5):
                self.play(*self.tok.focus(i, color=ACCENT), run_time=0.16)
                self.play(self.tok.cells[i - 1].animate.set_opacity(0.3), run_time=0.12)
                self._pop(tr, k=0.1)
            ok = self._verdict("✓ valid", GOOD)
            self.play(FadeIn(ok, shift=UP * 0.15), run_time=0.4)
            self.phase_a.append(ok)
            self.play(self.tok.cells[3].animate.set_opacity(0.3), run_time=0.12)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat7(self):
        """A closing bracket on an empty stack is not an error — it IS the answer."""
        with self.voiceover(text=BEATS[7]) as tr:
            swap_rails(
                self,
                headline("Closing on an empty stack is invalid."),
                caption("empty stack IS the answer"),
            )
            self.play(*[FadeOut(m) for m in self.phase_a], run_time=0.35)
            self.phase_a = []
            row = ArrayRow([")"], cell=0.7, fs=30, show_index=False)
            row.group.move_to([0, 1.85, 0])
            self.play(FadeIn(row.group, shift=DOWN * 0.2), run_time=0.4)
            self.tok = row
            self.play(*self.tok.focus(0, color=ACCENT), run_time=0.3)
            bad = self._verdict("✗ invalid", GONE)
            note = Text("nothing to pop", font=MONO, font_size=SMALL_FS, color=GONE)
            note.next_to(bad, DOWN, buff=0.3)
            self.play(FadeIn(bad, shift=UP * 0.15), run_time=0.4)
            self.play(FadeIn(note), run_time=0.35)
            self.phase_a += [row.group, bad, note]
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat8(self):
        """Leftovers mean the same thing: unclosed is invalid."""
        with self.voiceover(text=BEATS[8]) as tr:
            swap_rails(
                self,
                headline("Leftover openers mean the same."),
                caption("unclosed = invalid"),
            )
            self.play(*[FadeOut(m) for m in self.phase_a], run_time=0.35)
            self.phase_a = []
            row = ArrayRow(["(", "("], cell=0.7, fs=30, show_index=False)
            row.group.move_to([0, 1.85, 0])
            self.play(FadeIn(row.group, shift=DOWN * 0.2), run_time=0.4)
            self.tok = row
            for i in range(2):
                self.play(*self.tok.focus(i, color=ACCENT), run_time=0.2)
                self._push(tr, "(", color=PRIMARY, k=0.12, lo=0.3, hi=0.55)
            left = self._verdict("✗ invalid", GONE)
            note = Text("these two never closed", font=MONO, font_size=SMALL_FS, color=GONE)
            note.next_to(left, DOWN, buff=0.3)
            self.play(FadeIn(left, shift=UP * 0.15), run_time=0.4)
            self.play(FadeIn(note), run_time=0.35)
            self.phase_a += [row.group, left, note]
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    # ----------------------------------------------------------------- monotonic stack
    def _beat9(self):
        """The second shape is waiting, not cancelling."""
        with self.voiceover(text=BEATS[9]) as tr:
            swap_rails(
                self,
                headline("The second shape waits for bigger."),
                caption("monotonic stack"),
            )
            self.play(
                *[FadeOut(m) for m in self.phase_a],
                *[FadeOut(pl) for pl in self.stack.plates],
                run_time=0.4,
            )
            self.phase_a = []
            self.stack = PlateStack(x=-3.9, base_y=-1.5, w=1.25, h=0.5, buff=0.09, fs=16)
            base = self.stack.base_label("still waiting")
            self.row = ArrayRow(NUMS, cell=0.62, fs=26, show_index=True)
            self.row.group.move_to([0.9, 1.05, 0])
            self.play(FadeIn(self.row.group, shift=DOWN * 0.2), run_time=0.5)
            self.play(FadeIn(base), run_time=0.3)
            self.phase_b = [base]
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat10(self):
        """Next greater element, defined on the row the audience is looking at."""
        with self.voiceover(text=BEATS[10]) as tr:
            swap_rails(
                self,
                headline("Next greater: the first value that beats it."),
                caption("for each value, scan right"),
            )
            self.arc = Arrow(
                self.row.cell(0).get_top() + UP * 0.04,
                self.row.cell(2).get_top() + UP * 0.04,
                buff=0,
                color=ACCENT,
                stroke_width=2.8,
                path_arc=-1.2,
                max_tip_length_to_length_ratio=0.16,
            )
            lbl = Text("the first one bigger", font=MONO, font_size=15, color=ACCENT)
            lbl.move_to([0.21, 2.08, 0])
            self.play(*self.row.focus(0, color=ACCENT), run_time=0.3)
            self.play(GrowArrow(self.arc), run_time=min(0.9, max(0.5, tr.duration * 0.24)))
            self.play(FadeIn(lbl, shift=UP * 0.12), run_time=0.4)
            self.play(*self.row.focus(2, color=GOOD, fill_opacity=0.3), run_time=0.3)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self.phase_b += [self.arc, lbl]

    def _beat11(self):
        """The brute force the stack deletes: the inner loop."""
        with self.voiceover(text=BEATS[11]) as tr:
            swap_rails(
                self,
                headline("The brute force is a nested loop."),
                caption("that's quadratic"),
            )
            code = VGroup(
                Text("for i in range(n):", font=MONO, font_size=15, color=MUTED),
                Text("    scan right for a bigger", font=MONO, font_size=15, color=GONE),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
            box = card(code.width + 0.6, code.height + 0.45, color=STROKE, fill=PANEL)
            box.move_to([0.9, -1.35, 0])
            code.move_to(box.get_center())
            tag = Text("n² comparisons", font=MONO, font_size=15, color=GONE)
            tag.next_to(box, DOWN, buff=0.16)
            self.play(FadeIn(box), FadeIn(code), run_time=min(1.0, max(0.5, tr.duration * 0.26)))
            self.play(FadeIn(tag, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self.phase_b += [box, code, tag]

    def _beat12(self):
        """Push what is waiting: the pile stays decreasing."""
        with self.voiceover(text=BEATS[12]) as tr:
            swap_rails(
                self,
                headline("The stack holds what's still waiting."),
                caption("and it stays decreasing"),
            )
            self.play(FadeOut(self.phase_b[-1]), FadeOut(self.phase_b[-2]),
                      FadeOut(self.phase_b[-3]), FadeOut(self.arc), FadeOut(self.phase_b[-4]),
                      run_time=0.35)
            self.phase_b = self.phase_b[:-5]
            self.play(*self.row.focus(0, color=ACCENT), run_time=0.25)
            self._push(tr, "i=0", value=NUMS[0], color=PRIMARY, k=0.11, lo=0.3, hi=0.55)
            self.play(*self.row.focus(1, color=ACCENT), run_time=0.25)
            self._push(tr, "i=1", value=NUMS[1], color=PRIMARY, k=0.11, lo=0.3, hi=0.55)
            keep = chip("3 then 1: still decreasing", color=PRIMARY, fs=SMALL_FS)
            keep.move_to([0.9, -1.35, 0])
            self.play(FadeIn(keep, shift=UP * 0.12), run_time=0.4)
            self.phase_b.append(keep)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat13(self):
        """The pop is where the answer is written down."""
        with self.voiceover(text=BEATS[13]) as tr:
            swap_rails(
                self,
                headline("A bigger value is the answer it waited for."),
                caption("the pop writes the answer"),
            )
            self.play(FadeOut(self.phase_b[-1]), run_time=0.25)
            self.phase_b.pop()
            self.play(*self.row.focus(2, color=GOOD, fill_opacity=0.34), run_time=0.35)
            hit = Text("4 beats 3, and 4 beats 1", font=MONO, font_size=15, color=GOOD)
            hit.move_to([0.9, -1.35, 0])
            self.play(FadeIn(hit, shift=UP * 0.12), run_time=0.35)
            for i in (1, 0):
                self.play(Indicate(self.stack.top(), color=ACCENT, scale_factor=1.08), run_time=0.3)
                self._pop(tr, k=0.09, lo=0.26, hi=0.45)
                ans = Text(str(NUMS[2]), font=MONO, font_size=16, color=GOOD)
                ans.next_to(self.row.cell(i), UP, buff=0.16)
                self.play(FadeIn(ans, shift=DOWN * 0.1), run_time=0.3)
                self.phase_b.append(ans)
            self.phase_b.append(hit)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat14(self):
        """Push the new value; the invariant holds."""
        with self.voiceover(text=BEATS[14]) as tr:
            swap_rails(
                self,
                headline("Then push the new value."),
                caption("everything waiting is bigger"),
            )
            self.play(FadeOut(self.phase_b[-1]), run_time=0.25)
            self.phase_b.pop()
            self._push(tr, "i=2", value=NUMS[2], color=PRIMARY, k=0.11, lo=0.3, hi=0.55)
            hold = Text("waiting: 4", font=MONO, font_size=15, color=ACCENT)
            hold.move_to([0.9, -1.35, 0])
            self.play(FadeIn(hold, shift=UP * 0.12), run_time=0.4)
            self.phase_b.append(hold)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat15(self):
        """The loop keeps going: leftovers never found their answer, so they default."""
        with self.voiceover(text=BEATS[15]) as tr:
            swap_rails(
                self,
                headline("Leftovers never found their answer."),
                caption("so they take the default"),
            )
            self.play(FadeOut(self.phase_b[-1]), run_time=0.2)
            self.phase_b.pop()
            for i in (3, 4):
                self.play(*self.row.focus(i, color=ACCENT), run_time=0.18)
                if i == 3:
                    self._push(tr, "i=3", value=NUMS[3], color=PRIMARY, k=0.08, lo=0.22, hi=0.4,
                               )
                else:
                    self.play(*self.row.focus(4, color=GOOD, fill_opacity=0.34), run_time=0.15)
                    for j in (3, 2):
                        self._pop(tr, k=0.08, lo=0.22, hi=0.4)
                        ans = Text(str(NUMS[4]), font=MONO, font_size=16, color=GOOD)
                        ans.next_to(self.row.cell(j), UP, buff=0.16)
                        self.play(FadeIn(ans, shift=DOWN * 0.1), run_time=0.22)
                        self.phase_b.append(ans)
                    self._push(tr, "i=4", value=NUMS[4], color=PRIMARY, k=0.08, lo=0.22, hi=0.4)
            default = Text("-1", font=MONO, font_size=16, color=GONE)
            default.next_to(self.row.cell(4), UP, buff=0.16)
            self.play(FadeIn(default, shift=DOWN * 0.1), run_time=0.3)
            note = chip("no answer  →  default", color=GONE, fs=SMALL_FS)
            note.move_to([0.9, -1.35, 0])
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.35)
            self.phase_b += [default, note]
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    # ------------------------------------------------------------------ the decisions
    def _beat16(self):
        """The four decisions the card says to write down before coding."""
        with self.voiceover(text=BEATS[16]) as tr:
            swap_rails(
                self,
                headline("Four decisions before you code."),
                caption("decide, then write the loop"),
            )
            self.play(
                FadeOut(self.row.group),
                FadeOut(self.stack.group()),
                *[FadeOut(m) for m in self.phase_b],
                run_time=0.4,
            )
            self.phase_b = []
            lines = VGroup(
                Text("1  increasing or decreasing?", font=MONO, font_size=BODY_FS, color=INK),
                Text("2  index or value?", font=MONO, font_size=BODY_FS, color=INK),
                Text("3  what does the pop write?", font=MONO, font_size=BODY_FS, color=INK),
                Text("4  what do the leftovers mean?", font=MONO, font_size=BODY_FS, color=INK),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
            box = card(lines.width + 1.0, lines.height + 0.8, color=WINDOW, fill=PANEL)
            box.move_to(stage_center(-0.1))
            lines.move_to(box.get_center())
            self.play(FadeIn(box), run_time=0.35)
            self.play(
                *[FadeIn(t, shift=RIGHT * 0.2) for t in lines],
                lag_ratio=0.3,
                run_time=min(1.7, max(0.9, tr.duration * 0.4)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._decisions = VGroup(box, lines)

    def _beat17(self):
        """Index or value: a distance means you must keep the index."""
        with self.voiceover(text=BEATS[17]) as tr:
            swap_rails(
                self,
                headline("A distance means store the index."),
                caption("days until a warmer day"),
            )
            self.play(FadeOut(self._decisions, run_time=0.3))
            temps = ArrayRow(TEMPS, cell=0.56, fs=18, show_index=False, buff=0.07)
            temps.group.move_to([0, 1.0, 0])
            days = VGroup()
            for i, d in enumerate(DAYS):
                t = Text(str(d), font=MONO, font_size=16, color=ACCENT)
                t.next_to(temps.cell(i), DOWN, buff=0.22)
                days.add(t)
            hint = Text("days", font=MONO, font_size=15, color=MUTED)
            hint.next_to(days, LEFT, buff=0.3)
            note = chip("the answer is a distance  →  keep i", color=GOOD, fs=SMALL_FS)
            note.move_to(stage_center(-1.3))
            self.play(FadeIn(temps.cells), run_time=0.45)
            self.play(
                *[FadeIn(t, shift=DOWN * 0.12) for t in days],
                lag_ratio=0.25,
                run_time=min(1.6, max(0.8, tr.duration * 0.36)),
            )
            self.play(FadeIn(hint), run_time=0.3)
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._distance = VGroup(temps.cells, days, hint, note)

    def _beat18(self):
        """Why the nested while is still linear: one push, at most one pop, per element."""
        with self.voiceover(text=BEATS[18]) as tr:
            swap_rails(
                self,
                headline("Pushed once, popped at most once."),
                caption("so the while costs at most n"),
            )
            self.play(FadeOut(self._distance, run_time=0.35))
            dots = VGroup()
            for k in range(8):
                d = card(0.42, 0.42, color=PRIMARY, fill=PANEL, fill_opacity=0.35)
                d.move_to([-2.17 + k * 0.62, 0.75, 0])
                dots.add(d)
            lane = Line([-2.5, 0.75, 0], [2.5, 0.75, 0], color=WINDOW, stroke_width=6)
            first = chip("pushed once each: n", color=PRIMARY, fs=SMALL_FS)
            first.move_to([0, -0.3, 0])
            second = chip("popped at most once each: ≤ n", color=ACCENT, fs=SMALL_FS)
            second.move_to([0, -1.15, 0])
            self.play(FadeIn(dots), run_time=0.45)
            self.play(
                ShowPassingFlash(lane, time_width=0.6),
                run_time=min(1.2, max(0.6, tr.duration * 0.28)),
            )
            self.play(FadeIn(first, shift=UP * 0.12), run_time=0.35)
            self.play(
                ShowPassingFlash(lane.copy().reverse_points(), time_width=0.6),
                run_time=min(1.2, max(0.6, tr.duration * 0.28)),
            )
            self.play(FadeIn(second, shift=UP * 0.12), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._linear = VGroup(dots, first, second)

    def _beat19(self):
        """Amortised: the word the interviewer is waiting for."""
        with self.voiceover(text=BEATS[19]) as tr:
            swap_rails(
                self,
                headline("That is amortised constant per element."),
                caption("say amortised out loud"),
            )
            total = chip("total inner-loop work ≤ 2n   →   O(n)", color=GOOD, fs=BODY_FS)
            total.move_to(stage_center(-1.15))
            self.play(FadeIn(total, shift=UP * 0.15), run_time=min(1.0, max(0.5, tr.duration * 0.3)))
            self.play(Indicate(total, color=GOOD, scale_factor=1.06), run_time=0.6)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._amort = total

    def _beat20(self):
        """What breaks it: ties, and indexing an empty stack."""
        with self.voiceover(text=BEATS[20]) as tr:
            swap_rails(
                self,
                headline("Ties and empty pops break it."),
                caption("x < top  vs  x <= top"),
            )
            self.play(FadeOut(self._linear), FadeOut(self._amort), run_time=0.3)
            strict = Text("next strictly greater  →  use  <", font=MONO, font_size=BODY_FS,
                          color=GOOD)
            equal = Text("next greater or equal  →  use  ≤", font=MONO, font_size=BODY_FS,
                         color=ACCENT)
            empty = Text("never read an empty stack: if stack and …", font=MONO,
                         font_size=BODY_FS, color=GONE)
            rows = VGroup(strict, equal, empty).arrange(DOWN, aligned_edge=LEFT, buff=0.42)
            rows.move_to(stage_center(0.0))
            self.play(FadeIn(strict, shift=RIGHT * 0.2), run_time=0.45)
            self.play(FadeIn(equal, shift=RIGHT * 0.2), run_time=0.45)
            self.play(FadeIn(empty, shift=RIGHT * 0.2), run_time=0.45)
            self.play(Indicate(empty, color=GONE, scale_factor=1.05), run_time=0.6)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._breaks = rows

    def _beat21(self):
        """Which pile is the answer — the card's last 'know it in your sleep' question."""
        with self.voiceover(text=BEATS[21]) as tr:
            swap_rails(
                self,
                headline("Know which pile is your answer."),
                caption("survivors vs pops"),
            )
            self.play(FadeOut(self._breaks, run_time=0.3))
            left = VGroup(
                Text("cancelling", font=MONO, font_size=BODY_FS, color=GOOD),
                Text("what's left on the stack", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("is the answer", font=MONO, font_size=SMALL_FS, color=MUTED),
            ).arrange(DOWN, buff=0.18)
            right = VGroup(
                Text("monotonic", font=MONO, font_size=BODY_FS, color=ACCENT),
                Text("the pops were the answer", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("the leftovers default", font=MONO, font_size=SMALL_FS, color=MUTED),
            ).arrange(DOWN, buff=0.18)
            boxL = card(left.width + 0.9, left.height + 0.7, color=GOOD, fill=PANEL)
            boxR = card(right.width + 0.9, right.height + 0.7, color=ACCENT, fill=PANEL)
            boxL.move_to([-3.4, -0.2, 0])
            boxR.move_to([3.4, -0.2, 0])
            left.move_to(boxL.get_center())
            right.move_to(boxR.get_center())
            self.play(FadeIn(boxL), FadeIn(left), run_time=0.45)
            self.play(FadeIn(boxR), FadeIn(right), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._piles = VGroup(boxL, left, boxR, right)

    def _beat22(self):
        """The counter-tell: a stack works for reversing a string, and is the wrong tool."""
        with self.voiceover(text=BEATS[22]) as tr:
            swap_rails(
                self,
                headline("No 'most recent'? Skip the stack."),
                caption("two pointers cost O(1) space"),
            )
            self.play(FadeOut(self._piles, run_time=0.3))
            reverse = Text("reverse a string: stack  →  O(n) space", font=MONO, font_size=BODY_FS,
                           color=MUTED)
            cheaper = Text("two pointers  →  O(1) space", font=MONO, font_size=BODY_FS, color=GOOD)
            rule_txt = Text("no unresolved business, no stack", font=MONO, font_size=SMALL_FS,
                            color=MUTED)
            VGroup(reverse, cheaper, rule_txt).arrange(DOWN, buff=0.42).move_to(
                stage_center(0.0)
            )
            self.play(FadeIn(reverse, shift=UP * 0.2), run_time=0.45)
            self.play(FadeIn(cheaper, shift=UP * 0.2), run_time=0.45)
            self.play(FadeIn(rule_txt, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._counter = VGroup(reverse, cheaper, rule_txt)

    def _beat23(self):
        """Recall card: the line the viewer leaves with."""
        with self.voiceover(text=BEATS[23]) as tr:
            swap_rails(
                self,
                headline("Still unresolved? Most recent on top."),
                caption("most recent, first out"),
            )
            self.play(FadeOut(self._counter, run_time=0.3))
            box = card(8.8, 1.5, color=ACCENT, fill=PANEL)
            box.move_to(stage_center(-0.1))
            top = Text("Stack", font=MONO, font_size=32, color=ACCENT)
            sub = Text("unresolved, most recent first  ·  O(n) time  ·  O(n) space",
                       font=MONO, font_size=SMALL_FS, color=MUTED)
            VGroup(top, sub).arrange(DOWN, buff=0.22).move_to(box.get_center())
            self.play(FadeIn(box, scale=0.96), run_time=0.45)
            self.play(Write(top), run_time=0.5)
            self.play(FadeIn(sub), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
