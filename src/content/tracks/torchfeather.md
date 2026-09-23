---
title: Distributed Training from First Principles
description: Umar Jamil's 19-hour build of a distributed training framework in PyTorch (RoPE, MLA, pipeline / data / tensor / context / expert parallelism, MoE), followed chapter by chapter.
order: 3
status: planned
source: https://github.com/hkproj/torchfeather
sourceLabel: hkproj/torchfeather
---

The derivations are done on paper first, then coded. Every chapter below becomes a
note with the maths and the code diff.

Prerequisites the author names, done first:

- [ ] Flash Attention derived and coded from first principles
- [ ] Coding a Transformer from scratch in PyTorch

## Chapters

- [ ] 00:00 · Introduction
- [ ] 00:16 · Model architecture, parameters and training FLOPs
- [ ] 00:51 · RoPE from first principles
- [ ] 01:11 · Implementing RoPE and YaRN
- [ ] 01:50 · Building the transformer and weight initialization
- [ ] 02:19 · Attention, the KV cache and arithmetic intensity
- [ ] 03:02 · Coding Multi-head Latent Attention (MLA)
- [ ] 03:15 · Block matrix multiplication and MLA internals
- [ ] 03:34 · Deriving MLA and decoupled RoPE
- [ ] 04:10 · MLA weight absorption
- [ ] 04:32 · Autograd and the mathematics of distributed training
- [ ] 05:04 · Distributed computation graphs and DDP
- [ ] 05:10 · Building the training loop
- [ ] 06:06 · Pipeline parallelism from first principles
- [ ] 06:26 · Pipeline schedules: GPipe, 1F1B and Zero Bubble
- [ ] 07:10 · Datasets, tokenization and data parallelism
- [ ] 07:42 · Coding pipeline parallelism
- [ ] 08:37 · Device meshes and combining PP with DP
- [ ] 09:48 · Distributed communication collectives
- [ ] 10:49 · Implementing device meshes, DDP and FSDP
- [ ] 12:13 · Tensor parallelism from first principles
- [ ] 13:44 · Coding tensor parallelism
- [ ] 14:47 · Context parallelism and ring attention
- [ ] 15:41 · Metrics, optimizers, schedulers and checkpointing
- [ ] 16:00 · Combining parallelism in the training loop
- [ ] 16:49 · Mixture of Experts from first principles
- [ ] 18:02 · Tensor parallelism for MoE
- [ ] 18:36 · Expert parallelism
- [ ] 19:01 · All-to-all token dispatch and combine
- [ ] 19:27 · Expert tensor parallelism
