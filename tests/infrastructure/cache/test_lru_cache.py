from src.infrastructure.cache.lru_cache import LRUCache


class TestTTL:
    def test_get_returns_none_when_ttl_expired(self, monkeypatch):
        fake_time = [1000.0]
        monkeypatch.setattr(
            "src.infrastructure.cache.lru_cache.time.monotonic", lambda: fake_time[0]
        )

        cache = LRUCache(default_ttl=10)
        cache.set("k", "v")

        fake_time[0] = 1011.0  # +11s, TTL dépassé
        assert cache.get("k") is None

    def test_get_returns_value_when_ttl_not_expired(self, monkeypatch):
        fake_time = [1000.0]
        monkeypatch.setattr(
            "src.infrastructure.cache.lru_cache.time.monotonic", lambda: fake_time[0]
        )

        cache = LRUCache(default_ttl=10)
        cache.set("k", "v")

        fake_time[0] = 1005.0  # +5s, dans TTL
        assert cache.get("k") == "v"


class TestPerKeyTTL:
    def test_per_key_ttl_overrides_default(self, monkeypatch):
        fake_time = [1000.0]
        monkeypatch.setattr(
            "src.infrastructure.cache.lru_cache.time.monotonic", lambda: fake_time[0]
        )

        cache = LRUCache(default_ttl=10)
        cache.set("k", "v", ttl=5)  # ttl personnalisé plus court

        fake_time[0] = 1006.0  # +6s, dépasse le ttl=5 mais pas default_ttl=10
        assert cache.get("k") is None


class TestLRUEviction:
    def test_evicts_oldest_when_max_size_reached(self):
        cache = LRUCache(max_size=2)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.set("k3", "v3")  # déclenche éviction de k1

        assert cache.get("k1") is None
        assert cache.get("k2") == "v2"
        assert cache.get("k3") == "v3"
        assert cache.size == 2

    def test_get_moves_key_to_most_recent(self):
        cache = LRUCache(max_size=2)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.get("k1")  # k1 redevient récent → c'est k2 qui sera évincé
        cache.set("k3", "v3")

        assert cache.get("k1") == "v1"
        assert cache.get("k2") is None
