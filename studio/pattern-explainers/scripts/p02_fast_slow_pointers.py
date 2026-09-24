"""
Pattern 02 — Fast & Slow Pointers (Floyd's tortoise and hare).

The film follows the card's own argument: hook -> the job (does this list loop?) -> two
runners on a track -> why a meeting is unavoidable -> the straight track -> the midpoint
you get for free -> the two-link guard -> complexity -> Floyd's phase two (where the cycle
starts) -> the proof -> first-or-second middle -> the implicit list -> Happy Number ->
Find the Duplicate -> circular arrays -> how to recognise it -> the counter-tell -> what
breaks it -> the recall card.

Narration lives in BEATS and every animation is sized against `tracker.duration`, so the
picture and the voice cannot drift. Runner motion is computed state — a ValueTracker the
geometry reads each frame — never a hand-tuned keyframe.
"""

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    TAU,
    UP,
    Arrow,
    Circle,
    Circumscribe,
    Dot,
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
from shots import chip, node_chain

PATTERN_SLUG = "fast-slow"
TITLE = "Fast & Slow Pointers"
SUMMARY = "Two pointers at different speeds find cycles and midpoints in O(1) space."
SCENE_CLASS = "FastSlowPointers"
POSTER_AT = 25.0

BEATS = [
    # 0 hook
    "What if you could detect a loop in a linked list without spending any extra memory?",
    # 1 the job
    "Here's the job. A list whose last node points back into the middle of itself. Is there a cycle?",
    # 2 ELI5
    "Picture two runners on a circular track. One jogs. One sprints at double speed.",
    # 3 the race
    "Both start together. Every tick, the sprinter gains exactly one step on the jogger.",
    # 4 why a meeting is unavoidable
    "So the distance left to close shrinks by one each tick. A gap shrinking by one "
    "can never jump past zero. They must meet.",
    # 5 the straight track
    "On a straight track the sprinter simply falls off the end. No meeting, so no cycle.",
    # 6 the answer
    "So one question answers everything: did they meet? Yes means a cycle. No means none.",
    # 7 midpoint for free
    "And when the sprinter reaches the end, the jogger is standing exactly halfway. Midpoint, free.",
    # 8 the guard
    "One guard. Check that fast, and fast dot next, both exist before you take two steps.",
    # 9 complexity
    "Time is linear. Space is constant. The hash set you are replacing costs linear space.",
    # 10 shape one / shape two
    "That's shape one, detecting the cycle. Shape two finds where the cycle begins.",
    # 11 Floyd's phase two
    "After they meet, reset one pointer to the head, then walk both at the same speed. "
    "They collide at the entrance.",
    # 12 the proof
    "The proof: the distance from head to entrance equals the cycle length minus "
    "the meeting offset.",
    # 13 shape three
    "Shape three: finding the middle node. For an even list, decide whether you want the "
    "first middle or the second.",
    # 14 the hidden list
    "The hidden version has no linked list at all. Any rule from a value to a next "
    "value is a list.",
    # 15 Happy Number
    "Happy Number: replace the number by the sum of its squared digits. Every path ends "
    "in a cycle.",
    # 16 Find the Duplicate
    "Find the Duplicate: index into value, value into index. That mapping is a list "
    "in disguise.",
    # 17 circular arrays
    "The hardest variant is a circular array, where direction rules and a fresh start index "
    "complicate the walk.",
    # 18 recognise
    "Reach for it when the problem says linked list, cycle, or middle, or when it demands "
    "constant space.",
    # 19 the counter-tell
    "The tell: the naive answer is a hash set of visited nodes. Constant space rules that out.",
    # 20 what breaks it
    "What breaks it: writing while fast instead of while fast and fast dot next. That "
    "dereferences two links.",
    # 21 recall
    "Two runners, two speeds, one single pass, and no extra memory.",
]

CHAPTERS = {
    0: "The hook",
    1: "The job",
    2: "Two runners",
    4: "Why they must meet",
    5: "The straight track",
    7: "Midpoint, free",
    8: "The guard",
    9: "Complexity",
    10: "Where the cycle starts",
    12: "The proof",
    13: "First or second middle",
    14: "The hidden list",
    18: "How to recognise it",
    20: "What breaks it",
    21: "Recall",
}


# --------------------------------------------------------------------------------------
# local primitives (defined here, not in the shared shot library)
# --------------------------------------------------------------------------------------
def live_text(builder, anchor, *, color=INK, fs=SMALL_FS):
    """A Text whose string comes from computed state — never a keyframe.

    The anchor is applied to every rebuild, so an always_redraw readout keeps its place
    even though its width changes as the numbers change.
    """
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


def chevron(tip, color, label, *, above=True, fs=SMALL_FS, standoff=0.62):
    """A labelled arrow aimed at `tip`.

    Deliberately not a dot parked on the node: a filled marker hides the node's own digit,
    and a label belongs BESIDE a shape, never on top of it.
    """
    sign = UP if above else DOWN
    ar = Arrow(tip + sign * (standoff + 0.10), tip + sign * 0.10, buff=0.0, color=color,
               stroke_width=3.2, max_tip_length_to_length_ratio=0.3)
    lb = Text(label, font=MONO, font_size=fs, color=color)
    lb.next_to(ar, sign, buff=0.1)
    return VGroup(ar, lb)


def flat_chain(labels, *, y=0.6, node=0.72, buff=0.7, fs=SMALL_FS):
    """A left-to-right node chain placed as one unit, so it always sits on the safe box."""
    g = node_chain(labels, node=node, buff=buff)
    g.move_to([0, y, 0])
    return g


class FastSlowPointers(PrebakedVoiceMovingCameraScene):
    # ---------------------------------------------------------------------------- setup
    def construct(self):
        bg(self)
        self._hook = None
        self._ring = None
        for i in range(len(BEATS)):
            getattr(self, f"_beat{i}")()

    # ------------------------------------------------------------------------- ring maths
    RING_N = 6
    RING_C = np.array([0.0, 0.15, 0.0])
    RING_R = 1.35
    SLOW_LANE = 0.93
    FAST_LANE = 1.77

    def _ring_angle(self, u: float) -> float:
        """Node 0 at the top; the track runs clockwise, one unit per node."""
        return np.deg2rad(90.0) - TAU * u / self.RING_N

    def _lane_point(self, lane: float, u: float):
        a = self._ring_angle(u)
        return self.RING_C + np.array([lane * np.cos(a), lane * np.sin(a), 0.0])

    def _build_ring(self):
        nodes = VGroup()
        pts = []
        for i in range(self.RING_N):
            p = self._lane_point(self.RING_R, i)
            pts.append(p)
            c = Circle(radius=0.29, stroke_color=PRIMARY, stroke_width=2.2,
                       fill_color=PANEL, fill_opacity=1.0).move_to(p)
            t = Text(str(i + 1), font=MONO, font_size=SMALL_FS, color=INK).move_to(p)
            nodes.add(VGroup(c, t))
        edges = VGroup()
        for i in range(self.RING_N):
            edges.add(
                Arrow(pts[i], pts[(i + 1) % self.RING_N], buff=0.33, color=MUTED,
                      stroke_width=2.6, max_tip_length_to_length_ratio=0.24)
            )
        self._ring = VGroup(edges, nodes)

    def _runner(self, mult: float, lane: float, color):
        def _make():
            return Dot(self._lane_point(lane, self.t.get_value() * mult),
                       radius=0.155, color=color).set_stroke(BG, width=2.2)

        return always_redraw(_make)

    # --------------------------------------------------------------------- rho (phase two)
    RHO_TAIL_X = (-4.5, -3.3, -2.1)
    RHO_C = np.array([1.55, -0.35, 0.0])
    RHO_R = 1.15

    def _rho_point(self, u: float):
        if u <= 3.0:
            x = self.RHO_TAIL_X[0] + 1.2 * u
            return np.array([x, -0.35, 0.0])
        a = np.pi - (np.pi / 2.0) * (u - 3.0)
        return self.RHO_C + np.array([self.RHO_R * np.cos(a), self.RHO_R * np.sin(a), 0.0])

    def _rho_nodes(self):
        pts = [self._rho_point(float(i)) for i in range(7)]
        nodes = VGroup()
        for i, p in enumerate(pts):
            c = Circle(radius=0.30, stroke_color=PRIMARY, stroke_width=2.2,
                       fill_color=PANEL, fill_opacity=1.0).move_to(p)
            t = Text(str(i + 1), font=MONO, font_size=SMALL_FS, color=INK).move_to(p)
            nodes.add(VGroup(c, t))
        edges = VGroup()
        for i in range(7):
            j = (i + 1) % 7
            if i == 6:
                j = 3
            edges.add(
                Arrow(pts[i], pts[j], buff=0.34, color=MUTED, stroke_width=2.6,
                      max_tip_length_to_length_ratio=0.22)
            )
        return VGroup(edges, nodes), pts

    # ---------------------------------------------------------------------------- beats
    def _beat0(self):
        """Hook: the trade, named plainly before any notation appears."""
        with self.voiceover(text=BEATS[0]) as tr:
            swap_rails(self, headline("Detect a loop with no extra memory."),
                       caption("no hash set, just two speeds"))
            jog = chip("jog:  +1 step", color=ACCENT, fs=BODY_FS)
            sprint = chip("sprint:  +2 steps", color=PRIMARY, fs=BODY_FS)
            row = VGroup(jog, sprint).arrange(RIGHT, buff=0.7).move_to(stage_center(0.1))
            note = Text("the naive answer keeps a set of visited nodes",
                        font=MONO, font_size=SMALL_FS, color=MUTED)
            note.move_to([0, -1.5, 0])
            self.play(FadeIn(jog, shift=UP * 0.2), run_time=0.5)
            self.wait(0.25)
            self.play(FadeIn(sprint, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._hook = VGroup(row, note)

    def _beat1(self):
        """The job, as the shape the audience already knows: a chain that loops back."""
        with self.voiceover(text=BEATS[1]) as tr:
            swap_rails(self, headline("A list whose last node loops back."),
                       caption("is there a cycle?"))
            self.play(FadeOut(self._hook, run_time=0.3))
            chain = flat_chain([1, 2, 3, 4, 5], y=0.75)
            nodes = chain[0]
            back = Arrow(
                nodes[4].get_bottom() + DOWN * 0.12,
                nodes[2].get_bottom() + DOWN * 0.12,
                path_arc=-1.15, buff=0.06, color=GONE, stroke_width=3.0,
                max_tip_length_to_length_ratio=0.18,
            )
            tag = Text("last node points back into the middle", font=MONO,
                       font_size=SMALL_FS, color=GONE)
            tag.move_to([0, -1.85, 0])
            self.play(FadeIn(chain, shift=UP * 0.2), run_time=min(1.1, max(0.5, tr.duration * 0.3)))
            self.play(Write(back), run_time=0.6)
            self.play(FadeIn(tag, shift=UP * 0.15), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._job = VGroup(chain, back, tag)

    def _beat2(self):
        """ELI5: the ring and the two runners — the film's persistent spine."""
        with self.voiceover(text=BEATS[2]) as tr:
            swap_rails(self, headline("Two runners, one circular track."),
                       caption("one jogs, one sprints at double speed"))
            self.play(FadeOut(self._job, run_time=0.3))
            self._build_ring()
            self.t = ValueTracker(0.0)
            self.slow_dot = self._runner(1.0, self.SLOW_LANE, ACCENT)
            self.fast_dot = self._runner(2.0, self.FAST_LANE, PRIMARY)
            legend = VGroup(
                Text("slow: +1", font=MONO, font_size=SMALL_FS, color=ACCENT),
                Text("fast: +2", font=MONO, font_size=SMALL_FS, color=PRIMARY),
            ).arrange(RIGHT, buff=1.1)
            legend.move_to([0, -2.05, 0])
            self.add(self.t)
            self.play(FadeIn(self._ring), run_time=min(1.1, max(0.5, tr.duration * 0.3)))
            self.play(FadeIn(legend), FadeIn(self.slow_dot), FadeIn(self.fast_dot), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._legend = legend

    def _beat3(self):
        """The race begins: the gap still to close, read live off the tracker."""
        with self.voiceover(text=BEATS[3]) as tr:
            swap_rails(self, headline("The sprinter gains one step every tick."),
                       caption("the gap closes by exactly one"))
            self.gap = live_text(
                lambda: f"steps left to close = {max(0, int(round(self.RING_N - self.t.get_value())))}",
                [0, -2.55, 0], color=WINDOW,
            )
            self.add(self.gap)
            self.play(self.t.animate.set_value(3.0),
                      run_time=min(2.4, max(1.2, tr.duration * 0.55)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat4(self):
        """The heart: they must meet, and the camera moves in on the collision."""
        with self.voiceover(text=BEATS[4]) as tr:
            swap_rails(self, headline("They must meet."),
                       caption("a gap of one can never jump past zero"))
            self.play(self.t.animate.set_value(float(self.RING_N)),
                      run_time=min(2.0, max(1.0, tr.duration * 0.4)))
            met = Text("met  →  there is a cycle", font=MONO, font_size=BODY_FS, color=GOOD)
            met.move_to([0, -2.55, 0])
            self.play(FadeOut(self.gap), FadeIn(met, shift=UP * 0.15), run_time=0.4)
            self.gap = None
            self.camera.frame.save_state()  # bare: stores, does not animate
            self.play(
                self.camera.auto_zoom(
                    [self._ring, self.slow_dot, self.fast_dot], margin=0.55
                ),
                run_time=min(1.1, max(0.6, tr.duration * 0.22)),
            )
            self.play(Circumscribe(self._ring[1][0], color=GOOD), run_time=0.6)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.5)))
            self._met = met

    def _beat5(self):
        """The straight track: no loop, so the sprinter simply runs out of list."""
        with self.voiceover(text=BEATS[5]) as tr:
            swap_rails(self, headline("A straight track has no meeting."),
                       caption("fast falls off the end"))
            self.play(Restore(self.camera.frame),
                      FadeOut(self._met), FadeOut(self._legend), run_time=0.5)
            kill(self, self.slow_dot, self.fast_dot, self.gap)
            self.play(FadeOut(self._ring), run_time=0.35)

            chain = flat_chain([1, 2, 3, 4, 5], y=0.45)
            nodes = chain[0]
            slow = chevron(nodes[2].get_top(), ACCENT, "slow", above=True)
            gone_at = nodes[4].get_center() + RIGHT * 1.25
            fast = chevron(gone_at + UP * 0.34, GONE, "fast", above=True)
            off = Text("off the end: None", font=MONO, font_size=SMALL_FS, color=GONE)
            off.next_to(gone_at, DOWN, buff=0.4)
            self.play(FadeIn(chain, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(slow), FadeIn(fast), run_time=0.5)
            self.play(FadeIn(off, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._straight = VGroup(chain, slow, fast, off)

    def _beat6(self):
        """One question, two answers."""
        with self.voiceover(text=BEATS[6]) as tr:
            swap_rails(self, headline("Did they meet? That is the whole test."),
                       caption("yes = cycle, no = no cycle"))
            self.play(FadeOut(self._straight, run_time=0.3))
            yes = chip("met      →  cycle", color=GOOD, fs=BODY_FS)
            no = chip("no met  →  no cycle", color=GONE, fs=BODY_FS)
            both = VGroup(yes, no).arrange(DOWN, buff=0.55).move_to(stage_center(0.0))
            self.play(FadeIn(yes, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(no, shift=UP * 0.2), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._answer = both

    def _beat7(self):
        """The second free gift: the midpoint, read straight off the same walk."""
        with self.voiceover(text=BEATS[7]) as tr:
            swap_rails(self, headline("The jogger stops exactly halfway."),
                       caption("midpoint, in the same pass"))
            self.play(FadeOut(self._answer, run_time=0.3))
            chain = flat_chain([1, 2, 3, 4, 5], y=0.35)
            nodes = chain[0]
            slow = chevron(nodes[2].get_top(), ACCENT, "slow", above=True)
            fast = chevron(nodes[4].get_top(), PRIMARY, "fast", above=True)
            brace = Text("|------ half ------|", font=MONO, font_size=SMALL_FS, color=WINDOW)
            brace.move_to([0, -1.7, 0])
            self.play(FadeIn(chain, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(slow), FadeIn(fast), run_time=0.45)
            self.play(FadeIn(brace, shift=UP * 0.12), run_time=0.4)
            self.play(Indicate(nodes[2], color=ACCENT, scale_factor=1.12), run_time=0.6)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._midpoint = VGroup(chain, slow, fast, brace)

    def _beat8(self):
        """The guard, drawn as the two links it dereferences."""
        with self.voiceover(text=BEATS[8]) as tr:
            swap_rails(self, headline("Check two links before you sprint."),
                       caption("while fast and fast.next"))
            self.play(FadeOut(self._midpoint, run_time=0.3), run_time=0.3)
            chain = flat_chain([1, 2], y=1.35, node=0.66, buff=0.85)
            nodes = chain[0]
            tail = Text("None", font=MONO, font_size=SMALL_FS, color=GONE)
            tail.next_to(nodes[1], RIGHT, buff=0.5)
            dash = Arrow(nodes[1].get_right() + RIGHT * 0.05, tail.get_left() + LEFT * 0.05,
                         buff=0.02, color=GONE, stroke_width=2.4)
            code = VGroup(
                Text("while fast and fast.next:", font=MONO, font_size=SMALL_FS, color=GOOD),
                Text("slow = slow.next", font=MONO, font_size=SMALL_FS, color=MUTED),
                Text("fast = fast.next.next", font=MONO, font_size=SMALL_FS, color=MUTED),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
            box = card(code.width + 0.9, code.height + 0.7, color=STROKE, fill=PANEL)
            box.move_to([0, -0.95, 0])
            code.move_to(box.get_center())
            self.play(FadeIn(chain), FadeIn(tail), FadeIn(dash), run_time=0.5)
            self.play(FadeIn(box), run_time=0.35)
            self.play(Write(code), run_time=min(1.3, max(0.6, tr.duration * 0.3)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._guard = VGroup(chain, tail, dash, box, code)

    def _beat9(self):
        """Complexity, stated cold, against the thing it beats."""
        with self.voiceover(text=BEATS[9]) as tr:
            swap_rails(self, headline("Linear time, constant space."),
                       caption("the hash set costs linear space"))
            self.play(FadeOut(self._guard, run_time=0.3))
            setc = VGroup(
                Text("hash set", font=MONO, font_size=BODY_FS, color=GONE),
                MathTex(r"O(n)\ \mathrm{space}", color=GONE).scale(1.15),
            ).arrange(DOWN, buff=0.28)
            floyd = VGroup(
                Text("two runners", font=MONO, font_size=BODY_FS, color=GOOD),
                MathTex(r"O(1)\ \mathrm{space}", color=GOOD).scale(1.15),
            ).arrange(DOWN, buff=0.28)
            both = VGroup(setc, floyd).arrange(RIGHT, buff=2.0).move_to(stage_center(-0.05))
            arrow = Text("→", font=MONO, font_size=44, color=MUTED)
            arrow.move_to((setc.get_right() + floyd.get_left()) / 2)
            time = Text("both are O(n) time — space is the whole point",
                        font=MONO, font_size=SMALL_FS, color=MUTED)
            time.move_to([0, -2.15, 0])
            self.play(FadeIn(setc), run_time=0.45)
            self.play(FadeIn(arrow), run_time=0.3)
            self.play(FadeIn(floyd), run_time=0.45)
            self.play(FadeIn(time, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._cost = VGroup(both, arrow, time)

    def _beat10(self):
        """Floyd's phase two, on the rho shape where the geometry is visible."""
        with self.voiceover(text=BEATS[10]) as tr:
            swap_rails(self, headline("Phase two finds where the cycle starts."),
                       caption("this shape is called a rho"))
            self.play(FadeOut(self._cost, run_time=0.3))
            rho, pts = self._rho_nodes()
            head = Text("head", font=MONO, font_size=SMALL_FS, color=INK)
            head.next_to(rho[1][0], DOWN, buff=0.3)
            entry = Text("entrance", font=MONO, font_size=SMALL_FS, color=GOOD)
            entry.next_to(rho[1][3], UP, buff=0.34)
            meet = Text("they met here", font=MONO, font_size=SMALL_FS, color=GONE)
            meet.next_to(rho[1][4], UP, buff=0.3)
            self.play(FadeIn(rho), run_time=min(1.2, max(0.6, tr.duration * 0.3)))
            self.play(FadeIn(head), FadeIn(entry), FadeIn(meet), run_time=0.55)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._rho = VGroup(rho, head, entry, meet)

    def _beat11(self):
        """The two walkers, both at speed one, arriving together — computed state."""
        with self.voiceover(text=BEATS[11]) as tr:
            swap_rails(self, headline("Reset one to the head, then walk both at speed one."),
                       caption("they collide at the entrance"))
            self.w = ValueTracker(0.0)
            self.add(self.w)

            def _walker(offset, color):
                return always_redraw(
                    lambda: Dot(self._rho_point(offset + 3.0 * self.w.get_value()),
                                radius=0.135, color=color).set_stroke(BG, width=2.2)
                )

            from_head = _walker(0.0, ACCENT)
            from_meet = _walker(4.0, GONE)
            self.play(FadeIn(from_head), FadeIn(from_meet), run_time=0.4)
            self.play(self.w.animate.set_value(1.0),
                      run_time=min(2.6, max(1.2, tr.duration * 0.5)))
            self.play(Circumscribe(self._rho[0][1][3], color=GOOD), run_time=0.7)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._walkers = VGroup(from_head, from_meet)

    def _beat12(self):
        """The proof, as the algebra the card says to know cold."""
        with self.voiceover(text=BEATS[12]) as tr:
            swap_rails(self, headline("Why the head walk lands on the entrance."),
                       caption("head to entrance = cycle minus offset"))
            kill(self, *self._walkers, run_time=0.3)
            self.play(FadeOut(self._rho, run_time=0.3))
            eq1 = MathTex(r"2(F + a) = F + a + nC", color=INK).scale(1.15)
            eq2 = MathTex(r"F = nC - a", color=GOOD).scale(1.3)
            word = Text("same steps from the head, and from the meeting point",
                        font=MONO, font_size=SMALL_FS, color=MUTED)
            stack = VGroup(eq1, eq2, word).arrange(DOWN, buff=0.5).move_to(stage_center(-0.05))
            self.play(Write(eq1), run_time=min(1.2, max(0.6, tr.duration * 0.3)))
            self.play(Write(eq2), run_time=min(1.1, max(0.5, tr.duration * 0.25)))
            self.play(FadeIn(word, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._proof = stack

    def _beat13(self):
        """Shape three: the midpoint, and the off-by-one you decide on purpose."""
        with self.voiceover(text=BEATS[13]) as tr:
            swap_rails(self, headline("Even list: pick your middle on purpose."),
                       caption("first middle or second middle"))
            self.play(FadeOut(self._proof, run_time=0.3))
            chain = flat_chain([1, 2, 3, 4], y=0.55)
            nodes = chain[0]
            slow = chevron(nodes[2].get_top(), ACCENT, "slow", above=True)
            fast = chevron(nodes[3].get_center() + RIGHT * 1.25 + UP * 0.34, GONE,
                           "fast", above=True)
            second = Text("fast = head  →  second middle, the 3", font=MONO,
                          font_size=SMALL_FS, color=ACCENT)
            first = Text("fast = head.next  →  first middle, the 2", font=MONO,
                         font_size=SMALL_FS, color=GOOD)
            VGroup(second, first).arrange(DOWN, buff=0.34).move_to([0, -1.75, 0])
            self.play(FadeIn(chain, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(slow), FadeIn(fast), run_time=0.5)
            self.play(FadeIn(second, shift=UP * 0.12), run_time=0.4)
            self.play(FadeIn(first, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._middle = VGroup(chain, slow, fast, second, first)

    def _beat14(self):
        """The hidden list: a function you iterate is a list."""
        with self.voiceover(text=BEATS[14]) as tr:
            swap_rails(self, headline("No linked list? You can still have one."),
                       caption("a rule value → next value is a list"))
            self.play(FadeOut(self._middle, run_time=0.3))
            chain = flat_chain(["x", "f(x)", "f(f(x))", "…"], y=0.7, node=0.8, buff=0.72)
            note = VGroup(
                Text("a finite set plus a next-value rule", font=MONO,
                     font_size=SMALL_FS, color=WINDOW),
                Text("must repeat eventually", font=MONO, font_size=SMALL_FS, color=WINDOW),
            ).arrange(DOWN, buff=0.3).move_to([0, -1.75, 0])
            self.play(FadeIn(chain, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.45)
            self.camera.frame.save_state()  # bare: stores, does not animate
            self.play(
                self.camera.auto_zoom([chain, note], margin=0.5),
                run_time=min(1.2, max(0.6, tr.duration * 0.25)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._hidden = VGroup(chain, note)

    def _beat15(self):
        """Happy Number: the implicit list, made concrete."""
        with self.voiceover(text=BEATS[15]) as tr:
            swap_rails(self, headline("Happy Number is a list in disguise."),
                       caption("square the digits, add, repeat"))
            self.play(Restore(self.camera.frame), FadeOut(self._hidden, run_time=0.3))
            chain = flat_chain(["19", "82", "68", "100", "1"], y=0.7,
                               node=0.74, buff=0.6)
            nodes = chain[0]
            loop = Arrow(nodes[4].get_right() + RIGHT * 0.02,
                         nodes[4].get_left() + LEFT * 0.02,
                         path_arc=-2.6, buff=0.04, color=GONE, stroke_width=2.6,
                         max_tip_length_to_length_ratio=0.22)
            note = Text("1 squared is 1 — the walk repeats forever", font=MONO,
                        font_size=SMALL_FS, color=GONE)
            note.move_to([0, -1.75, 0])
            self.play(FadeIn(chain, shift=UP * 0.2), run_time=min(1.1, max(0.5, tr.duration * 0.3)))
            self.play(Write(loop), run_time=0.6)
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._happy = VGroup(chain, loop, note)

    def _beat16(self):
        """Find the Duplicate: index to value is the next pointer."""
        with self.voiceover(text=BEATS[16]) as tr:
            swap_rails(self, headline("Find the Duplicate walks index to value."),
                       caption("i → nums[i] is a next pointer"))
            self.play(FadeOut(self._happy, run_time=0.3))
            vals = [1, 3, 4, 2, 2]
            top = VGroup()
            for i, v in enumerate(vals):
                box = card(0.62, 0.62, color=STROKE, fill=PANEL)
                lb = Text(str(v), font=MONO, font_size=SMALL_FS, color=INK).move_to(box)
                top.add(VGroup(box, lb))
            top.arrange(RIGHT, buff=0.07).move_to([0, 0.95, 0])
            idx = VGroup()
            for i in range(len(vals)):
                lb = Text(str(i), font=MONO, font_size=SMALL_FS, color=MUTED)
                lb.next_to(top[i], DOWN, buff=0.16)
                idx.add(lb)
            rule = Text("start at index 0:  0 → 1 → 3 → 2 → 4 → 2 …",
                        font=MONO, font_size=BODY_FS, color=WINDOW)
            rule.move_to([0, -1.15, 0])
            hit = Text("2 repeats  →  that repeat is the duplicate", font=MONO,
                       font_size=SMALL_FS, color=GOOD)
            hit.move_to([0, -1.95, 0])
            self.play(FadeIn(top), FadeIn(idx), run_time=0.5)
            self.play(FadeIn(rule, shift=UP * 0.12), run_time=min(1.1, max(0.5, tr.duration * 0.3)))
            self.play(FadeIn(hit, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._dup = VGroup(top, idx, rule, hit)

    def _beat17(self):
        """The hardest variant: direction rules on a circular array."""
        with self.voiceover(text=BEATS[17]) as tr:
            swap_rails(self, headline("Circular arrays add two complications."),
                       caption("direction rules, and a fresh start"))
            self.play(FadeOut(self._dup, run_time=0.3))
            a = chip("every step has a direction", color=ACCENT, fs=BODY_FS)
            b = chip("each start index is its own walk", color=PRIMARY, fs=BODY_FS)
            both = VGroup(a, b).arrange(DOWN, buff=0.5).move_to(stage_center(0.05))
            warn = Text("a cycle must keep one direction the whole way round",
                        font=MONO, font_size=SMALL_FS, color=GONE)
            warn.move_to([0, -2.05, 0])
            self.play(FadeIn(a, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(b, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(warn, shift=UP * 0.12), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._circular = VGroup(both, warn)

    def _beat18(self):
        """Recognition signals, as a checklist."""
        with self.voiceover(text=BEATS[18]) as tr:
            swap_rails(self, headline("When to reach for it."),
                       caption("list, cycle, middle, constant space"))
            self.play(FadeOut(self._circular, run_time=0.3))
            yes = VGroup(
                Text("✓  a linked list and a cycle question", font=MONO,
                     font_size=BODY_FS, color=GOOD),
                Text("✓  the middle node, in one pass", font=MONO,
                     font_size=BODY_FS, color=GOOD),
                Text("✓  a next-value rule on a finite set", font=MONO,
                     font_size=BODY_FS, color=GOOD),
                Text("✓  the words constant extra space", font=MONO,
                     font_size=BODY_FS, color=GOOD),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            yes.move_to(stage_center(0.0))
            self.play(*[FadeIn(t, shift=RIGHT * 0.2) for t in yes],
                      lag_ratio=0.32, run_time=min(1.8, max(0.9, tr.duration * 0.45)))
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._recognise = yes

    def _beat19(self):
        """The counter-tell, in the card's own words."""
        with self.voiceover(text=BEATS[19]) as tr:
            swap_rails(self, headline("The counter-tell is a hash set."),
                       caption("visited nodes = linear space"))
            self.play(FadeOut(self._recognise, run_time=0.3))
            naive = chip("naive: a set of visited nodes  →  O(n) space", color=GONE, fs=BODY_FS)
            naive.move_to(stage_center(0.35))
            tell = Text("the constraint says constant space  →  this pattern",
                        font=MONO, font_size=BODY_FS, color=GOOD)
            tell.move_to([0, -1.15, 0])
            self.play(FadeIn(naive, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(tell, shift=UP * 0.2), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._counter = VGroup(naive, tell)

    def _beat20(self):
        """What breaks it: the guard, and the middle you did not choose."""
        with self.voiceover(text=BEATS[20]) as tr:
            swap_rails(self, headline("What breaks it."),
                       caption("while fast dereferences two links"))
            self.play(FadeOut(self._counter, run_time=0.3))
            bad = Text("✗  while fast:", font=MONO, font_size=BODY_FS, color=GONE)
            good = Text("✓  while fast and fast.next:", font=MONO, font_size=BODY_FS, color=GOOD)
            mix = Text("✗  mixing first and second middle", font=MONO,
                       font_size=BODY_FS, color=GONE)
            stack = VGroup(bad, good, mix).arrange(DOWN, aligned_edge=LEFT, buff=0.42)
            stack.move_to(stage_center(0.0))
            self.play(FadeIn(bad, shift=RIGHT * 0.2), run_time=0.45)
            self.play(FadeIn(good, shift=RIGHT * 0.2), run_time=0.45)
            self.play(FadeIn(mix, shift=RIGHT * 0.2), run_time=0.45)
            self.play(Indicate(good, color=GOOD, scale_factor=1.06), run_time=0.6)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._breaks = stack

    def _beat21(self):
        """Recall card: one line the viewer can leave with."""
        with self.voiceover(text=BEATS[21]) as tr:
            swap_rails(self, headline("Two runners, two speeds, one pass."),
                       caption("cycle or middle  →  fast and slow"))
            self.play(FadeOut(self._breaks, run_time=0.3))
            box = card(8.8, 1.55, color=ACCENT, fill=PANEL)
            box.move_to(stage_center(-0.05))
            top = Text("Fast & Slow Pointers", font=MONO, font_size=32, color=ACCENT)
            sub = Text("O(n) time  ·  O(1) space  ·  no hash set",
                       font=MONO, font_size=SMALL_FS, color=MUTED)
            VGroup(top, sub).arrange(DOWN, buff=0.24).move_to(box.get_center())
            self.play(FadeIn(box, scale=0.96), run_time=0.45)
            self.play(Write(top), run_time=0.5)
            self.play(FadeIn(sub), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))


__all__ = [
    "PATTERN_SLUG", "TITLE", "SUMMARY", "SCENE_CLASS", "POSTER_AT", "BEATS", "CHAPTERS",
    "FastSlowPointers",
]
