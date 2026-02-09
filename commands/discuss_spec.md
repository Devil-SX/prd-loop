---
name: discuss_spec
description: Discuss and review a spec document before converting it to PRD. Analyzes the spec for completeness, identifies ambiguities, suggests improvements, and helps refine requirements through interactive discussion.
argument-hint: [spec file path]
---

# Step 1

Read the spec file provided by the user. If no file path is given, search for spec files in the `.prd/specs/` directory and present available options for the user to choose from.

# Step 2

Analyze the spec document and present a structured review covering:

1. **Overview**: Summarize the spec's intent and scope in 2-3 sentences
2. **Completeness Check**: Identify any missing sections or requirements that a PRD would need:
   - Are user stories clearly defined or derivable?
   - Are acceptance criteria specific and verifiable?
   - Are technical constraints and dependencies mentioned?
   - Is the scope well-bounded (not too broad for autonomous implementation)?
3. **Ambiguities**: List any vague or unclear requirements that could lead to incorrect implementation
4. **Story Sizing**: Assess whether the spec can be broken into stories that are each completable in one iteration by an autonomous agent
5. **Suggestions**: Propose concrete improvements to make the spec more actionable

Present findings to the user and open a discussion. Ask clarifying questions about any ambiguous areas.

# Step 3

After discussing with the user and reaching agreement on refinements, offer two options:

1. **Update the spec file** with the agreed changes and write it back
2. **Proceed directly to PRD generation** by running `spec-to-prd` with the refined understanding

If the user chooses option 2, run `spec-to-prd` on the spec file with appropriate arguments.
