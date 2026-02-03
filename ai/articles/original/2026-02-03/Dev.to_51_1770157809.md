---
title: "Claude Code: Personal Practical Notes"
url: "https://dev.to/shusukedev/claude-code-personal-practical-notes-2o5h"
source: "Dev.to AI"
date: 2026-02-03
score: 51
---

# Claude Code: Personal Practical Notes

**来源**: [Dev.to AI](https://dev.to/shusukedev/claude-code-personal-practical-notes-2o5h) | **热度**: 51

## 原文内容

Title: Claude Code: Personal Practical Notes

URL Source: http://dev.to/shusukedev/claude-code-personal-practical-notes-2o5h

Published Time: 2026-02-02T23:38:22Z

Markdown Content:
[](http://dev.to/shusukedev/claude-code-personal-practical-notes-2o5h#introduction) Introduction
------------------------------------------------------------------------------------------------

Claude Code is a CLI tool provided by Anthropic that lets you delegate coding tasks to Claude directly from the terminal.

### [](http://dev.to/shusukedev/claude-code-personal-practical-notes-2o5h#how-much-code-can-it-write) How Much Code Can It Write?

In my experience, if your codebase and design are solid, Claude Code generates code at a satisfying level.

Transformers generate the next token based on existing context (the codebase and CLAUDE.md). If the existing codebase is poorly written, it generates poorly written code. If you prepare a well-organized codebase and clear rules, you get quality that matches.

It's a tool that excels at obediently and rapidly propagating patterns, which means the weight of human knowledge and every small decision becomes amplified. If you leave a sloppy codebase unattended, the mess spreads rapidly.

Human engineers have an innate drive toward maintainability and a professional ethic of "not cutting corners." LLMs don't have that intrinsic motivation. Ownership of quality must remain with the human.

In my recent personal projects, 99% of code is written through Claude Code. By combining rule enforcement via CLAUDE.md with design through plan mode, I can develop at high speed while maintaining architectural consistency.

[](http://dev.to/shusukedev/claude-code-personal-practical-notes-2o5h#development-flow) Development Flow
--------------------------------------------------------------------------------------------------------

### [](http://dev.to/shusukedev/claude-code-personal-practical-notes-2o5h#typical-workflow) Typical Workflow

```
1. Maintain CLAUDE.md
2. For major features or design decisions, create a discussion doc in docs/todo
3. Request design in plan mode
4. Review and approve the plan, then let it implement
5. Iterate: review -> fix
6. Sync documentation with /sync-docs
7. Git commit
```

### [](http://dev.to/shusukedev/claude-code-personal-practical-notes-2o5h#1-maintain-claudemd) 1. Maintain CLAUDE.md

Before starting a new project or feature, I make sure CLAUDE.md is up to date. This helps Claude correctly understand the project's structure and conventions.

### [](http://dev.to/shusukedev/claude-code-personal-practical-notes-2o5h#2-create-discussion-documents-for-major-changes) 2. Create Discussion Documents (for Major Changes)

When design decisions involve trade-offs or require comparing multiple options, I create a discussion document in `docs/todo/` before proceeding.

```
# Prompt example
"I want to discuss state management strategy. Summarize the options and comparisons in docs/todo/state-management.md"
```

By organizing thoughts in a document before entering plan mode, design rationale is preserved and easier to review later.

### [](http://dev.to/shusukedev/claude-code-personal-practical-notes-2o5h#3-request-design-in-plan-mode) 3. Request Design in Plan Mode

Rather than jumping straight into implementation, having Claude design first in plan mode tends to produce better results.

```
# Prompt example
"I want to add XXX feature. Please make a plan first."
```

In plan mode, Claude explores the codebase and proposes an implementation approach.

### [](http://dev.to/shusukedev/claude-code-personal-practical-notes-2o5h#4-review-and-approve-the-plan) 4. Review and Approve the Plan

Review the proposed plan and approve it if it looks good. Provide feedback if changes are needed. After approval, Claude writes the code. It may ask questions along the way, which you answer as needed.

### [](http://dev.to/shusukedev/claude-code-personal-practical-notes-2o5h#5-review-and-fix-iterations) 5. Review and Fix Iterations

I don't stop at a single review. I iterate multiple times until I'm satisfied.

```
# Claude review
/review-diff

# Request fixes if issues are found
"Fix the XXX part"

# Review again
/review-diff
```

I also check diffs visually in my editor. It's safer to combine Claude's review with a human eye check.

If the implementation feels off, it's often faster to `git checkout .` and start fresh rather than patching. Since regeneration cost is low with Claude Code, I find it's better to discard aggressively than to cling to a mediocre implementation.

### [](http://dev.to/shusukedev/claude-code-personal-practical-notes-2o5h#6-sync-documentation) 6. Sync Documentation

Once the implementation is stable and ready to commit, I update the documentation.

```
/sync-docs
```

This keeps related documentation in sync with code changes.

### [](http://dev.to/shusukedev/claude-code-personal-practical-notes-2o5h#7-commit) 7. Commit

I commit with regular `git commit`. You can ask C

---
*自动采集于 2026-02-03*
