# RoClaw Negative Constraints

Negative Constraints are learned prohibitions extracted from failed navigation traces during dream consolidation. They prevent the robot from repeating known mistakes.

## Format

Each constraint includes:
- **Rule**: Natural language prohibition
- **Confidence**: 0.0-1.0 (based on evidence count and consistency)
- **Category**: TERRAIN, TEMPORAL, STATIC, HAZARD, DYNAMIC
- **Evidence**: Number of supporting failure traces
- **Created**: Date first observed

---

## Active Constraints

*No constraints yet — they will be generated after the first dream consolidation cycle.*

<!-- Dream-generated constraints will be appended below this line -->
