# Contributing to Enterprise RAG Playbook

Thank you for your interest in contributing to this project. This guide explains how to contribute effectively.

## Philosophy

This repository is a **decision and architecture guide**, not a code library. Contributions should:

1. **Add practical value** - Real-world insights, not theoretical abstractions
2. **Focus on decisions** - Help readers make better choices
3. **Avoid vendor lock-in** - Principles over products
4. **Stay evergreen** - Avoid content that will quickly become outdated

## What We're Looking For

### High-Value Contributions

- **Failure mode documentation** - Real issues teams encounter
- **Decision frameworks** - Structured approaches to choices
- **Production patterns** - Battle-tested solutions
- **Evaluation methodologies** - Measuring RAG quality
- **Security considerations** - Enterprise requirements

### Lower Priority

- Vendor-specific tutorials (quickly outdated)
- UI/demo applications (not our focus)
- Benchmark results (context-dependent)
- Full implementation code (see philosophy below)

## Code Contributions

### Reference Implementation Philosophy

The reference implementation is **intentionally skeletal**:

- **Interfaces over implementations** - Define contracts
- **Examples are minimal** - Just enough to illustrate
- **Agent-improvable zones** - Marked areas for AI coding assistants

### When Adding Code

1. Keep it minimal and illustrative
2. Use clear type hints
3. Add "Production Considerations" comments
4. Mark extensibility points with `AGENT_ZONE` comments

```python
# AGENT_ZONE: Implement X strategy
# Options: A, B, C
# See: relevant-doc.md for guidance
```

## Documentation Contributions

### Structure

Each document should follow this pattern:

```markdown
# Title

Brief introduction (2-3 sentences)

## What/Why Section
Explain the concept

## How Section
Practical guidance

## When to Use / When Not to Use
Decision criteria

## Common Pitfalls
What goes wrong

## Checklist
Actionable items

---
**Navigation links**
```

### Style Guidelines

1. **Be direct** - No fluff, no filler
2. **Use tables** - For comparisons and options
3. **Include diagrams** - ASCII art for architecture
4. **Add code examples** - Illustrative, not exhaustive
5. **Link related content** - Connect concepts

### Formatting

- Use ATX headers (`#`, `##`, `###`)
- Code blocks with language hints
- Tables for structured comparisons
- Bullet points for lists

## Submitting Changes

### Process

1. **Fork** the repository
2. **Create a branch** with a descriptive name
3. **Make your changes** following the guidelines
4. **Test locally** - Ensure links work, formatting is correct
5. **Submit a PR** with a clear description

### PR Description Template

```markdown
## Summary
[Brief description of changes]

## Type of Change
- [ ] Documentation improvement
- [ ] New section/topic
- [ ] Bug fix (broken link, typo)
- [ ] Reference implementation update

## Checklist
- [ ] Follows documentation style guidelines
- [ ] No vendor-specific content
- [ ] Links are valid
- [ ] Adds practical value
```

### Review Process

1. Maintainers review for alignment with philosophy
2. Feedback provided within 1 week
3. Changes merged after approval

## What NOT to Contribute

To keep the repository focused:

1. **Full application code** - This is a guide, not a framework
2. **Vendor tutorials** - They have their own docs
3. **Benchmarks without context** - Results vary by use case
4. **Opinions without evidence** - Back claims with reasoning
5. **Marketing content** - No product promotion

## Reporting Issues

### Documentation Issues

- Outdated information
- Broken links
- Unclear explanations
- Missing topics

### Reference Implementation Issues

- Interface design problems
- Type errors
- Missing examples

### Use the Issue Template

```markdown
## Type
[Documentation / Implementation / Other]

## Description
[What's wrong or missing]

## Suggested Fix
[Your proposed solution, if any]

## Location
[File path or section]
```

## Community Guidelines

1. **Be respectful** - Constructive feedback only
2. **Stay on topic** - RAG systems focus
3. **Share knowledge** - Your experience helps others
4. **Ask questions** - Clarification is welcome

## Recognition

Contributors are acknowledged in:
- Git commit history
- PR descriptions
- Annual contributor recognition (if applicable)

## Questions?

- Open an issue for clarification
- Tag maintainers for guidance
- Check existing issues/PRs first

---

Thank you for helping make RAG systems better for everyone.
