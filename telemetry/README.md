# Telemetry

This directory will hold runtime observations that are useful for evaluation, routing, or debugging.

Telemetry should be decision-useful. If a field does not improve model selection, workflow design, cost control, or failure analysis, it probably should not be collected.

Examples of useful telemetry data:

- task type
- selected harness and models
- elapsed time and cost
- success or failure outcome
- retry, escalation, or fallback behavior

Avoid low-signal exhaust that does not support a clear decision.

Telemetry should describe what happened in real execution, not replace benchmark data.
