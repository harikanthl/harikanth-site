"""
Pattern 07 — In-place Reversal of a LinkedList.

The film follows the pattern card's own argument: the hook -> the chain -> why flipping a link
strands you -> the four lines in their fixed order -> return prev (and the line people get
wrong) -> why it is correct -> complexity stated cold -> the block shape with its four nodes
and two rewires -> the tail trap -> the dummy node -> every-k marching -> the cycle bug ->
rotation -> recognition -> the counter-tell -> the recall card.

The spine is the three-pointer walk: `prev`, `cur` and `nxt` are tags that ride the node row
while the forward arrows are rewritten into back-arrows underneath it, one node per beat. The
last beat of the walk lands on `prev`, which is the new head.

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
    MathTex,
    Restore,
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
from shots import chip, graph_viz, node_chain

PATTERN_SLUG = "linkedlist-reversal"
TITLE = "In-place Reversal of a LinkedList"
SUMMARY = "Three pointers, four lines in one fixed order: save, flip, step, and return prev."
SCENE_CLASS = "LinkedListReversal"
POSTER_AT = 38.0

NODES = [1, 2, 3, 4, 5]
ROW_Y = 0.62
CODE = ["nxt = cur.next", "cur.next = prev", "prev = cur", "cur = nxt"]

BEATS = [
    # 0 hook
    "Reversing a linked list is three pointers and four lines, in one fixed order.",
    # 1 the job
    "The job: every node points forward, and we want them all pointing backwards.",
    # 2 the ELI5
    "Picture a chain where each link only knows the link in front of it.",
    # 3 the trap
    "Flip one link by hand, and you destroy your only way forward.",
    # 4 save
    "So first you save the next node. That line is what keeps you from being stranded.",
    # 5 flip
    "Second, point the current link at prev. For the first node, prev is nothing, so it points at null.",
    # 6 step
    "Third, prev becomes the current node. Fourth, cur becomes the node you saved.",
    # 7 the loop
    "Now run those four lines down the list. Every node gets flipped once.",
    # 8 return prev
    "When cur falls off the end, prev stands on the last node flipped. That is the new head.",
    # 9 the classic bug
    "Return prev, not head. Head is the tail now, and returning it gives you a list of one.",
    # 10 why correct
    "Every link now points backwards, nothing was allocated, and no node was touched twice.",
    # 11 complexity
    "Linear time, constant space. The array version is also linear time, but it costs linear space.",
    # 12 the block shape
    "Every harder problem here reverses a block in the middle of a list.",
    # 13 four nodes
    "That needs the node before the block, the block's ends, and the node after it.",
    # 14 reverse the block
    "Reverse the block with the same four lines. The loop is unchanged.",
    # 15 the two rewires
    "Then two rewires. Before points at the block's new head, and the old first node points at what followed.",
    # 16 the tail trap
    "That old first node is the new tail. So save the node after the block before the flip destroys it.",
    # 17 the dummy node
    "A dummy node in front of the real head is not decoration. It deletes every first-node special case.",
    # 18 every-k
    "For every-k problems, march down the list: before advances to that block's new tail.",
    # 19 the cycle bug
    "Get that wrong and it does not crash. It silently drops the rest, or builds a cycle.",
    # 20 rotation
    "One episode reverses nothing. Rotation closes the list into a ring, walks to the new tail, and cuts.",
    # 21 recognise
    "Reach for this on reverse, on in pairs or every k, or when in-place is stated.",
    # 22 counter-tell
    "If linear extra space is allowed, copy into an array. Say that out loud, then say why not.",
    # 23 recall
    "Save next, flip, step, return prev.",
]

CHAPTERS = {
    0: "The hook",
    1: "The chain",
    3: "The trap",
    4: "The four lines",
    7: "The walk",
    8: "Prev is the new head",
    11: "Complexity",
    12: "The block shape",
    15: "The danger zone",
    17: "The dummy node",
    18: "Every k blocks",
    19: "The cycle bug",
    20: "Rotation",
    21: "How to recognise it",
    23: "Recall",
}


class LinkedListReversal(PrebakedVoiceMovingCameraScene):
    # ---------------------------------------------------------------------------- setup
    def construct(self):
        bg(self)
        self.chain = node_chain(NODES, node=0.78, buff=0.72).move_to([0, ROW_Y, 0])
        self.nodes = self.chain[0]
        self.fwd = self.chain[1]
        self.back = []
        self.tags = {}
        self._tag_at = {}
        self.code = None
        self.null_right = None
        for i in range(len(BEATS)):
            getattr(self, f"_beat{i}")()

    # ------------------------------------------------------------------------- utilities
    def _stage_mobjects(self):
        """Everything currently drawn except the rails and the hairline — the shot's content.

        The rule() hairline spans the whole frame, so including it would turn a zoom into a
        zoom-out; it is design furniture, not content.
        """
        skip = {id(m) for m in rails_of(self)}
        if getattr(self, "rule_line", None) is not None:
            skip.add(id(self.rule_line))
        return [
            m
            for m in self.mobjects
            if id(m) not in skip
            and (len(getattr(m, "points", [])) or len(getattr(m, "submobjects", [])))
        ]

    def _tag_above(self, node, text, color, fs=SMALL_FS):
        arrow = Arrow(
            node.get_top() + UP * 0.5,
            node.get_top() + UP * 0.06,
            buff=0,
            color=color,
            stroke_width=2.8,
            max_tip_length_to_length_ratio=0.3,
        )
        lb = Text(text, font=MONO, font_size=fs, color=color)
        lb.next_to(arrow, UP, buff=0.08)
        return VGroup(arrow, lb)

    def _tag(self, i, name, color):
        self.tags[name] = self._tag_above(self.nodes[i], name, color)
        self._tag_at[name] = i
        return self.tags[name]

    def _move(self, name, i):
        """Slide an existing pointer tag to node i — computed from node centres, not keyframed."""
        delta = self.nodes[i].get_center() - self.nodes[self._tag_at[name]].get_center()
        self._tag_at[name] = i
        return self.tags[name].animate.shift(delta)

    def _back_arrow(self, i, j):
        """The rewritten `next` link: node i now points back at node j, arcing under the row."""
        a = self.nodes[i].get_bottom() + DOWN * 0.06
        b = self.nodes[j].get_bottom() + DOWN * 0.06
        return Arrow(
            a,
            b,
            buff=0,
            color=GOOD,
            stroke_width=3.0,
            path_arc=-1.6,
            tip_length=0.15,
            max_tip_length_to_length_ratio=0.22,
        )

    def _null_below(self, i):
        """The first flip points at nothing: draw the terminator under node i."""
        node = self.nodes[i]
        arrow = Arrow(
            node.get_bottom() + DOWN * 0.06,
            node.get_bottom() + DOWN * 0.55,
            buff=0,
            color=GOOD,
            stroke_width=3.0,
            max_tip_length_to_length_ratio=0.3,
        )
        c = chip("null", color=MUTED, fs=SMALL_FS)
        c.next_to(arrow, DOWN, buff=0.1)
        return VGroup(arrow, c)

    def _code_strip(self, active=None):
        parts = VGroup()
        for i, line in enumerate(CODE):
            parts.add(
                Text(
                    line,
                    font=MONO,
                    font_size=16,
                    color=ACCENT if i == active else MUTED,
                )
            )
        parts.arrange(RIGHT, buff=0.35)
        parts.move_to([0, -1.85, 0])
        return parts

    def _hl(self, k):
        """Move the highlight along the four lines — in place, never a second copy."""
        return [self.code[i].animate.set_color(ACCENT if i == k else MUTED) for i in range(len(CODE))]

    # ---------------------------------------------------------------------------- beats
    def _beat0(self):
        """Hook: name the trade, then show the two costs as objects."""
        with self.voiceover(text=BEATS[0]) as tr:
            swap_rails(
                self,
                headline("Three pointers, four lines, one order."),
                caption("O(n) time  ·  O(1) space"),
            )
            self.rule_line = rule()
            self.play(FadeIn(self.rule_line), run_time=0.3)
            worse = chip("copy to array: O(n) space", color=GONE, fs=BODY_FS)
            better = chip("rewire in place: O(1) space", color=GOOD, fs=BODY_FS)
            pair = VGroup(worse, better).arrange(DOWN, buff=0.5).move_to(stage_center(0.15))
            self.play(FadeIn(worse, shift=UP * 0.2), run_time=0.45)
            self.wait(0.25)
            self.play(
                FadeIn(better, shift=UP * 0.2),
                run_time=min(0.9, max(0.5, tr.duration * 0.25)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._hook = pair

    def _beat1(self):
        """The object of the whole film: the chain, with its forward links and its null end."""
        with self.voiceover(text=BEATS[1]) as tr:
            swap_rails(
                self,
                headline("Flip every link to point backwards."),
                caption("1 → 2 → 3 → 4 → 5 → null"),
            )
            self.play(FadeOut(self._hook, run_time=0.3))
            self.play(
                FadeIn(self.nodes, scale=0.96),
                FadeIn(self.fwd),
                run_time=min(1.2, max(0.6, tr.duration * 0.3)),
            )
            last = self.nodes[-1]
            arr = Arrow(
                last.get_right() + RIGHT * 0.05,
                last.get_right() + RIGHT * 0.5,
                buff=0,
                color=MUTED,
                stroke_width=2.6,
                max_tip_length_to_length_ratio=0.3,
            )
            lb = Text("null", font=MONO, font_size=SMALL_FS, color=MUTED)
            lb.next_to(arr, RIGHT, buff=0.1)
            self.null_right = VGroup(arr, lb)
            self.play(FadeIn(self.null_right, shift=RIGHT * 0.2), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat2(self):
        """ELI5: the chain only knows forward — sweep the links so the audience sees it."""
        with self.voiceover(text=BEATS[2]) as tr:
            swap_rails(
                self,
                headline("Each node only knows its next node."),
                caption("every link points forward"),
            )
            self.play(
                *[Indicate(a, color=PRIMARY, scale_factor=1.12) for a in self.fwd],
                lag_ratio=0.35,
                run_time=min(1.8, max(0.9, tr.duration * 0.4)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat3(self):
        """The trap that motivates the whole order: flipping the link cuts you off."""
        with self.voiceover(text=BEATS[3]) as tr:
            swap_rails(
                self,
                headline("Flip one link and you're stranded."),
                caption("the way forward is gone"),
            )
            self.play(FadeIn(self._tag(0, "cur", ACCENT)), run_time=0.4)
            self.play(Indicate(self.fwd[0], color=GONE, scale_factor=1.1), run_time=0.55)
            self.play(
                *[self.nodes[k].animate.set_opacity(0.22) for k in (1, 2, 3, 4)],
                self.null_right.animate.set_opacity(0.22),
                run_time=min(1.2, max(0.6, tr.duration * 0.3)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat4(self):
        """Line one: save the way forward before it is destroyed."""
        with self.voiceover(text=BEATS[4]) as tr:
            swap_rails(
                self,
                headline("First, save the next node."),
                caption("nxt = cur.next"),
            )
            self.play(
                *[self.nodes[k].animate.set_opacity(1.0) for k in (1, 2, 3, 4)],
                self.null_right.animate.set_opacity(1.0),
                run_time=0.4,
            )
            self.play(FadeIn(self._tag(1, "nxt", WINDOW), shift=UP * 0.15), run_time=0.45)
            self.code = self._code_strip(0)
            self.play(FadeIn(self.code, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat5(self):
        """Line two: the flip itself — and the very first node points at null."""
        with self.voiceover(text=BEATS[5]) as tr:
            swap_rails(
                self,
                headline("Then flip the current link."),
                caption("cur.next = prev"),
            )
            self.play(*self._hl(1), run_time=0.35)
            term = self._null_below(0)
            self.play(
                FadeOut(self.fwd[0]),
                FadeIn(term, shift=DOWN * 0.2),
                run_time=min(1.1, max(0.55, tr.duration * 0.28)),
            )
            self.back.append(term)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat6(self):
        """Lines three and four: step prev, then step cur onto the saved node."""
        with self.voiceover(text=BEATS[6]) as tr:
            swap_rails(
                self,
                headline("Then step prev, and step cur."),
                caption("prev = cur, cur = nxt"),
            )
            self.play(*self._hl(2), run_time=0.3)
            self.play(
                FadeIn(self._tag(0, "prev", PRIMARY)),
                self._move("cur", 1),
                self._move("nxt", 2),
                run_time=min(1.1, max(0.6, tr.duration * 0.3)),
            )
            self.play(*self._hl(3), run_time=0.3)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat7(self):
        """The loop runs: every remaining forward link is rewritten into a back arrow."""
        with self.voiceover(text=BEATS[7]) as tr:
            swap_rails(
                self,
                headline("Run those four lines down the list."),
                caption("each node flipped once"),
            )
            self.play(*self._hl(0), run_time=0.3)
            per = min(0.5, max(0.3, tr.duration * 0.11))
            for i in range(1, len(NODES)):
                arc = self._back_arrow(i, i - 1)
                self.back.append(arc)
                if i < len(NODES) - 1:
                    anims = [FadeOut(self.fwd[i]), GrowArrow(arc)]
                else:
                    anims = [FadeOut(self.null_right), GrowArrow(arc)]
                self.play(*anims, run_time=per)
                if i < 3:
                    self.play(
                        self._move("prev", i),
                        self._move("cur", i + 1),
                        self._move("nxt", i + 2),
                        run_time=per * 0.7,
                    )
                elif i == 3:
                    self.play(
                        self._move("prev", i),
                        self._move("cur", i + 1),
                        FadeOut(self.tags["nxt"], shift=RIGHT * 0.3),
                        run_time=per * 0.7,
                    )
                else:
                    self.play(
                        self._move("prev", 4),
                        FadeOut(self.tags["cur"], shift=RIGHT * 0.3),
                        run_time=per * 0.8,
                    )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat8(self):
        """The reveal: zoom the rewritten chain, because prev is standing on the new head."""
        with self.voiceover(text=BEATS[8]) as tr:
            swap_rails(
                self,
                headline("Cur falls off the end. Prev is the head."),
                caption("return prev"),
            )
            head = Text("new head", font=MONO, font_size=SMALL_FS, color=GOOD)
            head.next_to(self.tags["prev"], RIGHT, buff=0.3)
            self.play(
                *self._hl(-1),
                Indicate(self.nodes[4], color=GOOD, scale_factor=1.12),
                run_time=0.5,
            )
            self.play(FadeIn(head, shift=RIGHT * 0.2), run_time=0.4)
            self._head_lbl = head
            self.camera.frame.save_state()  # bare: stores, doesn't animate
            self.play(
                self.camera.auto_zoom(self._stage_mobjects(), margin=1.0),
                run_time=min(1.3, max(0.7, tr.duration * 0.3)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.5)))

    def _beat9(self):
        """The line people get wrong: head is now the tail."""
        with self.voiceover(text=BEATS[9]) as tr:
            swap_rails(
                self,
                headline("Return prev, not head."),
                caption("head is now the tail"),
            )
            self.play(Restore(self.camera.frame), run_time=0.8)
            self.play(FadeOut(self.code, run_time=0.3), FadeOut(self._head_lbl, run_time=0.3))
            old = self._tag_above(self.nodes[0], "old head = tail", GONE)
            self.play(FadeIn(old, shift=UP * 0.15), run_time=0.45)
            note = chip("return head  →  list of one", color=GONE, fs=SMALL_FS)
            note.move_to([0, -1.85, 0])
            self.play(FadeIn(note, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._tail_note = VGroup(old, note)

    def _beat10(self):
        """Why it is correct: every link points back, and nothing was allocated."""
        with self.voiceover(text=BEATS[10]) as tr:
            swap_rails(
                self,
                headline("Every link points backwards."),
                caption("nothing was allocated"),
            )
            self.play(FadeOut(self.tags["prev"]), run_time=0.3)
            self.play(
                *[Indicate(a, color=GOOD, scale_factor=1.1) for a in self.back],
                lag_ratio=0.4,
                run_time=min(1.5, max(0.8, tr.duration * 0.35)),
            )
            good = chip("each node visited once", color=GOOD, fs=SMALL_FS)
            good.move_to([0, -1.85, 0])
            self.play(FadeIn(good, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._correct = good

    def _beat11(self):
        """Complexity, stated cold."""
        with self.voiceover(text=BEATS[11]) as tr:
            swap_rails(
                self,
                headline("Linear time, constant space."),
                caption("the array version costs O(n) space"),
            )
            self.play(
                FadeOut(self.chain),
                *[FadeOut(a) for a in self.back],
                FadeOut(self._tail_note),
                FadeOut(self._correct),
                run_time=0.4,
            )
            slow = VGroup(
                Text("copy to array", font=MONO, font_size=BODY_FS, color=GONE),
                MathTex(r"O(n)\ \mathrm{time}", color=GONE).scale(0.8),
                MathTex(r"O(n)\ \mathrm{space}", color=GONE).scale(0.8),
            ).arrange(DOWN, buff=0.2)
            fast = VGroup(
                Text("in place", font=MONO, font_size=BODY_FS, color=GOOD),
                MathTex(r"O(n)\ \mathrm{time}", color=GOOD).scale(0.8),
                MathTex(r"O(1)\ \mathrm{space}", color=GOOD).scale(0.8),
            ).arrange(DOWN, buff=0.2)
            pair = VGroup(slow, fast).arrange(RIGHT, buff=1.7).move_to(stage_center(-0.1))
            arrow = Text("→", font=MONO, font_size=40, color=MUTED)
            arrow.move_to((slow.get_right() + fast.get_left()) / 2)
            self.play(FadeIn(slow), run_time=0.45)
            self.play(FadeIn(arrow), run_time=0.25)
            self.play(FadeIn(fast), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._cost = VGroup(pair, arrow)

    # ------------------------------------------------------------------ the block shape
    def _build_block(self):
        chain = node_chain(["b", "1", "2", "3", "a"], node=0.7, buff=0.62)
        chain.move_to([0, 0.95, 0])
        nodes, arrows = chain[0], chain[1]
        left = nodes[1].get_left()[0] - 0.12
        right = nodes[3].get_right()[0] + 0.12
        rect = card(right - left, 1.0, color=WINDOW, fill=PANEL, fill_opacity=0.0)
        rect.move_to([(left + right) / 2, 0.95, 0])
        label = Text("block", font=MONO, font_size=SMALL_FS, color=WINDOW)
        label.next_to(rect, DOWN, buff=0.14)
        self.blk_chain, self.blk_nodes, self.blk_fwd = chain, nodes, arrows
        self.blk_rect, self.blk_label = rect, label
        return chain, nodes, arrows, rect, label

    def _beat12(self):
        """The shape that covers every harder problem: a block in the middle."""
        with self.voiceover(text=BEATS[12]) as tr:
            swap_rails(
                self,
                headline("Now reverse a block in the middle."),
                caption("before → [block] → after"),
            )
            self.play(FadeOut(self._cost, run_time=0.3))
            chain, nodes, arrows, rect, label = self._build_block()
            self.play(FadeIn(nodes, scale=0.96), FadeIn(arrows), run_time=0.5)
            self.play(FadeIn(rect), FadeIn(label), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat13(self):
        """Four nodes matter, not two."""
        with self.voiceover(text=BEATS[13]) as tr:
            swap_rails(
                self,
                headline("Four nodes matter, not two."),
                caption("before, first, last, after"),
            )
            t0 = self._tag_above(self.blk_nodes[0], "before", PRIMARY)
            t1 = self._tag_above(self.blk_nodes[1], "first", ACCENT)
            t3 = self._tag_above(self.blk_nodes[3], "last", ACCENT)
            t4 = self._tag_above(self.blk_nodes[4], "after", WINDOW)
            self.blk_tags = [t0, t1, t3, t4]
            self.play(
                *[FadeIn(t, shift=UP * 0.15) for t in self.blk_tags],
                lag_ratio=0.35,
                run_time=min(1.6, max(0.8, tr.duration * 0.4)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _beat14(self):
        """The block reverses with the same four lines."""
        with self.voiceover(text=BEATS[14]) as tr:
            swap_rails(
                self,
                headline("Reverse the block with the same loop."),
                caption("the four lines are unchanged"),
            )
            a21 = self._blk_back(2, 1)
            a32 = self._blk_back(3, 2)
            self.blk_back = [a21, a32]
            self.play(
                FadeOut(self.blk_fwd[1]),
                FadeOut(self.blk_fwd[2]),
                GrowArrow(a21),
                GrowArrow(a32),
                run_time=min(1.3, max(0.7, tr.duration * 0.32)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))

    def _blk_back(self, i, j):
        a = self.blk_nodes[i].get_bottom() + DOWN * 0.05
        b = self.blk_nodes[j].get_bottom() + DOWN * 0.05
        return Arrow(
            a,
            b,
            buff=0,
            color=GOOD,
            stroke_width=2.8,
            path_arc=-1.6,
            tip_length=0.14,
            max_tip_length_to_length_ratio=0.22,
        )

    def _beat15(self):
        """The two rewires that stitch the reversed block back into the list."""
        with self.voiceover(text=BEATS[15]) as tr:
            swap_rails(
                self,
                headline("Then two rewires finish the job."),
                caption("before → new head, old first → after"),
            )
            x_before = self.blk_nodes[0].get_center()[0]
            x_first = self.blk_nodes[1].get_center()[0]
            x_last = self.blk_nodes[3].get_center()[0]
            x_after = self.blk_nodes[4].get_center()[0]
            r1 = Arrow(
                [x_before, -0.2, 0],
                [x_last, -0.2, 0],
                buff=0,
                color=GOOD,
                stroke_width=2.8,
                max_tip_length_to_length_ratio=0.06,
            )
            l1 = Text("before → new head", font=MONO, font_size=15, color=GOOD)
            l1.next_to(r1, RIGHT, buff=0.16)
            r2 = Arrow(
                [x_first, -0.95, 0],
                [x_after, -0.95, 0],
                buff=0,
                color=ACCENT,
                stroke_width=2.8,
                max_tip_length_to_length_ratio=0.06,
            )
            l2 = Text("old first → after", font=MONO, font_size=15, color=ACCENT)
            l2.next_to(r2, RIGHT, buff=0.16)
            self.play(FadeOut(self.blk_fwd[0]), FadeOut(self.blk_fwd[3]), run_time=0.3)
            self.play(GrowArrow(r1), FadeIn(l1), run_time=0.5)
            self.play(GrowArrow(r2), FadeIn(l2), run_time=0.5)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self.blk_rewire = VGroup(r1, l1, r2, l2)

    def _beat16(self):
        """The tail trap: the old first node is the new tail, so save `after` first."""
        with self.voiceover(text=BEATS[16]) as tr:
            swap_rails(
                self,
                headline("The old first node is the new tail."),
                caption("save after before you flip"),
            )
            tail = Text("new tail", font=MONO, font_size=15, color=ACCENT)
            tail.next_to(self.blk_nodes[1], DOWN, buff=0.95)
            self.play(
                Indicate(self.blk_nodes[1], color=ACCENT, scale_factor=1.15),
                run_time=0.6,
            )
            self.play(FadeIn(tail, shift=UP * 0.12), run_time=0.4)
            warn = chip("flip first, save later  →  link lost", color=GONE, fs=SMALL_FS)
            warn.move_to([0, -1.95, 0])
            self.play(FadeIn(warn, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._tail_warn = VGroup(tail, warn)

    def _beat17(self):
        """The dummy node deletes every head special case."""
        with self.voiceover(text=BEATS[17]) as tr:
            swap_rails(
                self,
                headline("A dummy node deletes special cases."),
                caption("dummy.next = head"),
            )
            self.play(FadeOut(self._tail_warn, run_time=0.3))
            moving = VGroup(
                self.blk_chain, self.blk_rect, self.blk_label, self.blk_rewire, *self.blk_tags
            )
            self.play(moving.animate.shift(RIGHT * 1.32), run_time=0.7)
            dummy = node_chain(["0"], node=0.7)[0]
            dummy.move_to([-3.96, 0.95, 0])
            link = Arrow(
                dummy.get_right() + RIGHT * 0.04,
                self.blk_nodes[0].get_left() + LEFT * 0.04,
                buff=0,
                color=MUTED,
                stroke_width=2.4,
                max_tip_length_to_length_ratio=0.3,
            )
            tag = Text("dummy", font=MONO, font_size=SMALL_FS, color=PRIMARY)
            tag.next_to(dummy, UP, buff=0.5)
            self.play(FadeIn(dummy, scale=0.9), run_time=0.4)
            self.play(GrowArrow(link), FadeIn(tag), run_time=0.45)
            no_case = chip("no is-this-the-first-node case", color=GOOD, fs=SMALL_FS)
            no_case.move_to([0, -1.95, 0])
            self.play(FadeIn(no_case, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._dummy_set = VGroup(dummy, link, tag, no_case)

    def _beat18(self):
        """Every-k: the same loop, run block after block, marching down the list."""
        with self.voiceover(text=BEATS[18]) as tr:
            swap_rails(
                self,
                headline("Every-k blocks: before hugs the tail."),
                caption("before = the block's new tail"),
            )
            self.play(
                FadeOut(self.blk_chain),
                FadeOut(self.blk_rect),
                FadeOut(self.blk_label),
                FadeOut(self.blk_rewire),
                FadeOut(self._dummy_set),
                *[FadeOut(t) for t in self.blk_tags],
                *[FadeOut(a) for a in self.blk_back],
                run_time=0.4,
            )
            chain = node_chain([1, 2, 3, 4, 5, 6], node=0.66, buff=0.55).move_to([0, 0.9, 0])
            nodes, arrows = chain[0], chain[1]
            rects = VGroup()
            for lo, hi in ((0, 1), (2, 3), (4, 5)):
                left = nodes[lo].get_left()[0] - 0.09
                right = nodes[hi].get_right()[0] + 0.09
                r = card(right - left, 0.92, color=WINDOW, fill=PANEL, fill_opacity=0.0)
                r.move_to([(left + right) / 2, 0.9, 0])
                rects.add(r)
            self.play(FadeIn(nodes), FadeIn(arrows), run_time=0.45)
            self.play(FadeIn(rects), run_time=0.4)
            tag = self._tag_above(nodes[0], "before", PRIMARY)
            self.play(FadeIn(tag), run_time=0.35)
            arc = Arrow(
                nodes[1].get_bottom() + DOWN * 0.05,
                nodes[0].get_bottom() + DOWN * 0.05,
                buff=0,
                color=GOOD,
                stroke_width=2.8,
                path_arc=-1.6,
                tip_length=0.14,
                max_tip_length_to_length_ratio=0.22,
            )
            self.play(FadeOut(arrows[0]), GrowArrow(arc), run_time=0.4)
            delta = nodes[1].get_center() - nodes[0].get_center()
            self.play(tag.animate.shift(delta), run_time=0.5)
            note = Text("the new tail", font=MONO, font_size=15, color=GOOD)
            note.next_to(tag, RIGHT, buff=0.35)
            self.play(FadeIn(note), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._everyk = VGroup(chain, rects, tag, arc, note)

    def _beat19(self):
        """What getting it wrong actually does: silently lose the rest, or build a cycle."""
        with self.voiceover(text=BEATS[19]) as tr:
            swap_rails(
                self,
                headline("Get it wrong and you lose the list."),
                caption("or build a cycle"),
            )
            self.play(FadeOut(self._everyk, run_time=0.35))
            ring = graph_viz(
                {"a": (-1.5, 0.75), "b": (1.5, 0.75), "c": (0.0, -0.75)},
                [("a", "b"), ("b", "c"), ("c", "a")],
                directed=True,
            )
            drops = chip("the rest of the list is gone", color=GONE, fs=SMALL_FS)
            drops.move_to([0, -1.95, 0])
            self.play(FadeIn(ring), run_time=min(1.1, max(0.6, tr.duration * 0.3)))
            self.play(FadeIn(drops, shift=UP * 0.12), run_time=0.4)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._cycle = VGroup(ring, drops)

    def _beat20(self):
        """Rotation is in this pattern but reverses nothing."""
        with self.voiceover(text=BEATS[20]) as tr:
            swap_rails(
                self,
                headline("Rotation reverses nothing at all."),
                caption("close the ring, walk, cut"),
            )
            self.play(FadeOut(self._cycle, run_time=0.3))
            coords = {
                "1": (0.0, 1.15),
                "2": (1.35, 0.35),
                "3": (0.85, -1.1),
                "4": (-0.85, -1.1),
                "5": (-1.35, 0.35),
            }
            ring = graph_viz(
                coords,
                [("1", "2"), ("2", "3"), ("3", "4"), ("4", "5"), ("5", "1")],
                directed=True,
            )
            note = Text("k %= n, then walk n - k steps, then cut", font=MONO,
                        font_size=SMALL_FS, color=MUTED)
            note.move_to([0, -1.95, 0])
            self.play(FadeIn(ring), run_time=min(1.0, max(0.6, tr.duration * 0.3)))
            self.play(FadeIn(note, shift=RIGHT * 0.2), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._rotate = VGroup(ring, note)

    def _beat21(self):
        """Recognition signals — the checklist."""
        with self.voiceover(text=BEATS[21]) as tr:
            swap_rails(
                self,
                headline("Reach for it on 'in-place'."),
                caption("reverse, in pairs, every k"),
            )
            self.play(FadeOut(self._rotate, run_time=0.3))
            yes = VGroup(
                Text("✓  reverse a linked list", font=MONO, font_size=BODY_FS, color=GOOD),
                Text("✓  reverse part, given positions", font=MONO, font_size=BODY_FS, color=GOOD),
                Text("✓  in pairs, every k, in groups", font=MONO, font_size=BODY_FS, color=GOOD),
                Text("✓  in-place, or O(1) extra space", font=MONO, font_size=BODY_FS, color=GOOD),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            yes.move_to(stage_center(0.05))
            self.play(
                *[FadeIn(t, shift=RIGHT * 0.2) for t in yes],
                lag_ratio=0.32,
                run_time=min(1.7, max(0.9, tr.duration * 0.4)),
            )
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.35)))
            self._recognise = yes

    def _beat22(self):
        """The counter-tell: the card insists you name the easy version out loud."""
        with self.voiceover(text=BEATS[22]) as tr:
            swap_rails(
                self,
                headline("Allowed linear space? Copy to an array."),
                caption("say it out loud first"),
            )
            self.play(FadeOut(self._recognise, run_time=0.3))
            alt = Text("✗  O(n) space allowed  →  array copy", font=MONO, font_size=BODY_FS,
                       color=GONE)
            reason = Text("shorter, easier, and the question is not asking for it",
                          font=MONO, font_size=SMALL_FS, color=MUTED)
            VGroup(alt, reason).arrange(DOWN, buff=0.42).move_to(stage_center(-0.05))
            self.play(FadeIn(alt, shift=UP * 0.2), run_time=0.5)
            self.play(FadeIn(reason, shift=UP * 0.15), run_time=0.45)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
            self._counter = VGroup(alt, reason)

    def _beat23(self):
        """Recall card: one line the viewer leaves with."""
        with self.voiceover(text=BEATS[23]) as tr:
            swap_rails(
                self,
                headline("Save next, flip, step, return prev."),
                caption("three pointers, one order"),
            )
            self.play(FadeOut(self._counter, run_time=0.3))
            box = card(8.6, 1.5, color=ACCENT, fill=PANEL)
            box.move_to(stage_center(-0.1))
            top = Text("Linked List Reversal", font=MONO, font_size=30, color=ACCENT)
            sub = Text("O(n) time  ·  O(1) space  ·  no new nodes",
                       font=MONO, font_size=SMALL_FS, color=MUTED)
            VGroup(top, sub).arrange(DOWN, buff=0.22).move_to(box.get_center())
            self.play(FadeIn(box, scale=0.96), run_time=0.45)
            self.play(Write(top), run_time=0.5)
            self.play(FadeIn(sub), run_time=0.35)
            self.wait(max(0.1, tr.get_remaining_duration(buff=0.4)))
