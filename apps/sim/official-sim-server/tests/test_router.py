def _get_app():
    from app.main import app as official_sim_app

    return official_sim_app


class TestRouterRegistration:
    def test_no_query_routes_registered(self):
        app = _get_app()
        routes = [route.path for route in app.routes]
        query_routes = [r for r in routes if "/query" in r]
        assert len(query_routes) == 0, f"Found query routes that should not exist: {query_routes}"

    def test_no_unified_routes_registered(self):
        app = _get_app()
        routes = [route.path for route in app.routes]
        unified_routes = [r for r in routes if "/unified" in r]
        assert len(unified_routes) == 0, f"Found unified routes that should not exist: {unified_routes}"

    def test_runs_routes_registered(self):
        app = _get_app()
        routes = [route.path for route in app.routes]
        runs_routes = [r for r in routes if "/official-sim/runs" in r]
        assert len(runs_routes) > 0, "No runs routes found"

    def test_raw_routes_registered(self):
        app = _get_app()
        routes = [route.path for route in app.routes]
        raw_routes = [r for r in routes if "/official-sim/raw" in r]
        assert len(raw_routes) > 0, "No raw routes found"

    def test_six_platform_compat_routes_registered(self):
        app = _get_app()
        routes = [route.path for route in app.routes]
        platforms = ["jd", "douyin", "wecom", "taobao", "xhs", "kuaishou"]

        for platform in platforms:
            platform_routes = [r for r in routes if f"/mock/{platform}" in r]
            assert len(platform_routes) > 0, f"No mock routes found for platform: {platform}"

    def test_official_sim_prefix_only(self):
        app = _get_app()
        routes = [route.path for route in app.routes if hasattr(route, 'path')]

        forbidden_prefixes = [
            "/official-sim/query",
            "/official-sim/unified",
            "/official-sim/users",
            "/official-sim/orders",
        ]
        
        for prefix in forbidden_prefixes:
            matching_routes = [r for r in routes if r.startswith(prefix)]
            assert len(matching_routes) == 0, f"Found routes with forbidden prefix {prefix}: {matching_routes}"
