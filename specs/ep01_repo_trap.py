"""Ep01 - Check these 3 things before installing a GitHub repo (the pilot)."""
import math
from explainer import card_repo, card_checklist, card_commit, card_config, card_chart, card_follow, prog, ease_out

SCENES = [  # start, headline, highlighted phrase, card factory(t, local_t)
    (0.00,  "This GitHub Repo", "Might Be a Trap", lambda t, lt: card_repo()),
    (4.92,  "Before You Install", "Check 3 Things", lambda t, lt: card_checklist(marks=min(3, 1 + int(lt / 0.5)))),
    (8.70,  "Check #1", "Last Commit", lambda t, lt: card_commit(badge=t > 11.2)),
    (16.34, "Check #2", "Permissions", lambda t, lt: card_config(pulse=(0.5 + 0.5 * math.sin(t * 7)) if t > 19.88 else 0)),
    (25.66, "Check #3", "Star History", lambda t, lt: card_chart(p=ease_out(prog(lt, 0.8, 2.6)))),
    (35.42, "So… Is It", "Worth the Risk?", lambda t, lt: card_checklist(crossed=True)),
    (40.30, "The Verdict", "Skip It", None),
    (41.58, "Ship It", "or Skip It?", lambda t, lt: card_follow()),
]
STAMPS = [(23.82, 25.4, "NO."), (32.78, 35.2, "BOUGHT?"), (40.30, 41.5, "SKIP IT")]
POSE_CUES = [(0, "shocked"), (4.9, "explain"), (8.7, "point"), (11.2, "warn"), (16.3, "point"), (19.9, "warn"),
             (23.8, "explain"), (25.6, "point"), (28.0, "warn"), (35.4, "think"), (40.3, "skip"), (41.6, "ship")]

