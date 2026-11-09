#!/usr/bin/env python3
"""Order spaces by agent activity and sort the Agents sidebar to match.

Spaces: active (working/blocked) agents first, then other spaces with agents,
both by newest state_change_seq; spaces without agents keep their order last.
"""
import os

from recency import PLUGIN_ID, call, lock_runs, rank_spaces


def space_order():
    current = [w["workspace_id"] for w in call("workspace.list")["workspaces"]]
    rank = rank_spaces()
    with_agents = sorted((ws for ws in current if ws in rank),
                         key=lambda ws: rank[ws], reverse=True)
    return current, with_agents + [ws for ws in current if ws not in rank]


with lock_runs():
    current, wanted = space_order()
    if wanted != current:
        call("workspace.move_block", {"workspace_ids": wanted})
        print("spaces:", " ".join(wanted))
    if os.environ.get("HERDR_PLUGIN_EVENT") != "pane.agent_status_changed":
        call("agent.view.set", {
            "source": f"plugin:{PLUGIN_ID}",
            "label": "recency",
            "sort": [
                {"field": "workspace_order", "order": "asc"},
                {"field": "attention", "order": "desc"},
                {"field": "state_change_seq", "order": "desc"},
            ],
        })
