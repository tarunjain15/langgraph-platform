```yaml
task_id: TEMPLATE
phase: MX
type: [Integration | Feature | Migration | Optimization]
status: pending
created: YYYY-MM-DD
```

# Task X.Y: [Type] Task Name

## The Constraint

**Before:** [What constraint blocks this capability]
**After:** [What capability emerges when constraint is removed]

---

## The Witness

**Observable Truth:** [What can ONLY exist if this task succeeded]

**Why This Witness:**
[Explain why this specific observation proves the task's completion]
[What makes this witness unique to this task's success]

---

## Acceptance Criteria

**Must Verify:**
- [ ] [Objective condition 1 - measurable]
- [ ] [Objective condition 2 - measurable]
- [ ] [Objective condition 3 - measurable]

**Cannot Exist Without:**
- The witness outcome must be **impossible** before task completion
- The witness outcome must be **automatic** after task completion
- The witness outcome must be **measurable** objectively

---

## Code Pattern

```python
# The minimal code that unlocks the witness
# This code should be the ONLY thing needed to make the witness observable
```

---

## Execution Protocol

**Prerequisites:**
- [What must exist before this task can begin]

**Execution Steps:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Verification Steps:**
1. [How to verify acceptance criterion 1]
2. [How to verify acceptance criterion 2]
3. [How to verify acceptance criterion 3]

---

## The Completion Signal

**Signal:** [Single sentence describing the final proof]

**Evidence Required:**
- [Artifact 1 that proves completion - file, output, measurement]
- [Artifact 2 that proves completion]
- [Artifact 3 that proves completion]

**State Transition:**
```yaml
before:
  status: pending
  witness: impossible

after:
  status: complete
  witness: observed
  evidence: [artifact1, artifact2, artifact3]
```

---

## Constraint Compliance

**CONTEXT_PRESERVATION:** [How this task honors continuity across time]
**CONSTRAINT_INHERITANCE:** [How this task ensures children obey parent constraints]
**TRACE_REQUIRED:** [How this task ensures all decisions are traceable]
**RESOURCE_STEWARDSHIP:** [How this task uses minimum necessary resources]
**RESIDUE_FREE:** [How this task leaves no unclear artifacts]

---

## Notes

[Any additional context, gotchas, or insights]
