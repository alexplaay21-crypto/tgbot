"""
The onboarding flow (/start -> language -> documents -> menu) stays
entirely stateless - each step is recomputed from Backend rather than
tracked here, matching section 89's "Backend is always the source of
truth". FSM state is reserved for things Backend genuinely has no
business tracking, like "the next plain-text message is a search query"
(store.py) - a purely local, conversational bit of state, not an
entitlement or account fact.
"""
