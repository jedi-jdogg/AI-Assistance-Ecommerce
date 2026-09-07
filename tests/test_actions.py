from lindas_agent.actions.shopify_actions import ActionLog, flip_to_preorder
from lindas_agent.inventory.alerts import preorder_candidates
from lindas_agent.inventory.ranking import rank_variants


def test_preorder_dry_run_never_calls_client(settings, catalog):
    ranked = rank_variants(catalog, settings)
    log = ActionLog()
    flip_to_preorder(preorder_candidates(ranked, settings), client=None, settings=settings, apply=False, log=log)
    assert log.results and all(not r.applied for r in log.results)
    assert any("Queen" in r.entity for r in log.results)


def test_preorder_apply_calls_client(settings, catalog):
    calls = []

    class Fake:
        def set_inventory_policy(self, pid, vids, policy): calls.append(("policy", pid, policy))
        def add_tags(self, pid, tags): calls.append(("tags", pid, tuple(tags)))

    ranked = rank_variants(catalog, settings)
    log = ActionLog()
    flip_to_preorder([v for v in preorder_candidates(ranked, settings) if "Queen" in v.product_title], Fake(), settings, apply=True, log=log)
    assert ("policy", "gid://shopify/Product/2", "CONTINUE") in calls
    assert any(c[0] == "tags" and "Pre-Order" in c[2] for c in calls)
    assert log.results[0].applied
