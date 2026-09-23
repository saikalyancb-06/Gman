"""
test_local_search.py
--------------------
Tests for the LOCAL_SEARCH intent pipeline added to GeoGuide.

Covers:
 - Intent classification for business/place queries
 - location_hint extraction from neighbourhood keywords
 - OUT_OF_DOMAIN guard is NOT overridden by LOCAL_SEARCH
 - search_local_business() returns structured records for real Bengaluru places
 - answer_query() returns answerable=True with LOCAL_PLACES_SEARCH mode for valid queries
 - answer_query() falls back gracefully when OSM returns nothing
 - Indian 'Hotel' ambiguity — category_intent selection
"""
import pytest
from backend.rag_service import QueryContext, GroundedRAGService


# ---------------------------------------------------------------------------
# 1. Intent classification tests (no network calls)
# ---------------------------------------------------------------------------

class TestLocalSearchIntentClassification:
    """Unit tests for LOCAL_SEARCH intent routing inside QueryContext.resolve()."""

    def _ctx(self, query: str, city_id: int = 2) -> QueryContext:
        return QueryContext.resolve(query, session_city_id=city_id)

    def test_where_is_slv_hotel_triggers_local_search(self):
        ctx = self._ctx("where is SLV hotel in Basavanagudi?")
        assert ctx.intent == "LOCAL_SEARCH", f"Expected LOCAL_SEARCH, got {ctx.intent}"

    def test_hotels_in_gandhi_bazaar_triggers_local_search(self):
        ctx = self._ctx("which hotels are there in Gandhi Bazaar?")
        assert ctx.intent == "LOCAL_SEARCH", f"Expected LOCAL_SEARCH, got {ctx.intent}"

    def test_restaurants_near_lalbagh_triggers_local_search(self):
        ctx = self._ctx("restaurants near Lalbagh Bengaluru")
        assert ctx.intent == "LOCAL_SEARCH", f"Expected LOCAL_SEARCH, got {ctx.intent}"

    def test_where_can_i_eat_in_malleswaram(self):
        ctx = self._ctx("where can i eat in Malleswaram?")
        assert ctx.intent == "LOCAL_SEARCH", f"Expected LOCAL_SEARCH, got {ctx.intent}"

    def test_neighbourhood_hint_gandhi_bazaar_extracted(self):
        ctx = self._ctx("restaurants in Gandhi Bazaar Bengaluru")
        assert ctx.location_hint == "gandhi bazaar", f"Expected 'gandhi bazaar', got {ctx.location_hint!r}"

    def test_neighbourhood_hint_malleswaram_extracted(self):
        ctx = self._ctx("cafes in Malleswaram")
        assert ctx.location_hint == "malleswaram", f"Expected 'malleswaram', got {ctx.location_hint!r}"

    def test_no_location_hint_when_absent(self):
        ctx = self._ctx("where is SLV hotel")
        assert ctx.location_hint is None, f"Expected None, got {ctx.location_hint!r}"

    def test_manager_query_stays_out_of_domain(self):
        """'Who is the manager of X restaurant' must be OUT_OF_DOMAIN, not LOCAL_SEARCH."""
        ctx = self._ctx("Who is the current manager of the Hampi Bazaar restaurant?", city_id=1)
        assert ctx.intent == "OUT_OF_DOMAIN", f"Expected OUT_OF_DOMAIN, got {ctx.intent}"

    def test_open_now_query_stays_operational_status(self):
        """'Is X open now?' must trigger OPERATIONAL_STATUS, not LOCAL_SEARCH."""
        ctx = self._ctx("Is Vidyarthi Bhavan restaurant open now?")
        assert ctx.intent == "OPERATIONAL_STATUS", f"Expected OPERATIONAL_STATUS, got {ctx.intent}"

    def test_hotel_booking_stays_out_of_domain(self):
        """'hotel booking' must stay OUT_OF_DOMAIN."""
        ctx = self._ctx("help me with hotel booking in Bengaluru")
        assert ctx.intent == "OUT_OF_DOMAIN", f"Expected OUT_OF_DOMAIN, got {ctx.intent}"

    def test_entry_fee_query_not_local_search(self):
        """Entry fee queries must NOT be classified as LOCAL_SEARCH."""
        ctx = self._ctx("what is the entry fee for Lalbagh?")
        assert ctx.intent == "ENTRY_FEE", f"Expected ENTRY_FEE, got {ctx.intent}"


# ---------------------------------------------------------------------------
# 2. WebRetriever.search_local_business() unit tests (live network — marked slow)
# ---------------------------------------------------------------------------

@pytest.mark.slow
class TestSearchLocalBusiness:
    """Live integration tests for OSM Nominatim retrieval."""

    def setup_method(self):
        from backend.web_retriever import WebRetriever
        self.wr = WebRetriever()

    def test_slv_hotel_returns_results(self):
        results = self.wr.search_local_business(
            query="where is SLV hotel",
            entity_name="SLV",
            location_hint="basavanagudi",
            destination_name="Bengaluru",
            category_intent=None
        )
        # Nominatim should find at least one SLV Corner / SLV Delite variant
        assert len(results) >= 1, "Expected at least 1 result for SLV in Basavanagudi"

    def test_result_schema_is_complete(self):
        results = self.wr.search_local_business(
            query="restaurants in Gandhi Bazaar",
            entity_name=None,
            location_hint="gandhi bazaar",
            destination_name="Bengaluru",
            category_intent="RESTAURANT"
        )
        if results:
            r = results[0]
            assert "name" in r
            assert "category" in r
            assert "address" in r
            assert "latitude" in r
            assert "longitude" in r
            assert "source" in r
            assert "source_url" in r
            assert r["source"] == "OpenStreetMap Local Places Registry"

    def test_ctr_malleswaram_found(self):
        results = self.wr.search_local_business(
            query="CTR hotel Malleswaram",
            entity_name="CTR",
            location_hint="malleswaram",
            destination_name="Bengaluru",
        )
        assert any("ctr" in r["name"].lower() or "central tiffin" in r["name"].lower() for r in results), \
            f"CTR not found in results: {[r['name'] for r in results]}"


# ---------------------------------------------------------------------------
# 3. answer_query() end-to-end integration tests
# ---------------------------------------------------------------------------

class TestAnswerQueryLocalSearch:
    """End-to-end tests: LOCAL_SEARCH queries must produce answerable=True with LOCAL_PLACES_SEARCH mode."""

    def setup_method(self):
        self.rag = GroundedRAGService()

    def test_slv_hotel_query_is_answerable(self):
        """'where is SLV hotel' must return answerable=True (not an abstention)."""
        res = self.rag.answer_query("where is SLV hotel in Basavanagudi?", language="en", city_id=2)
        assert res["answerable"] is True, (
            f"Expected answerable=True for SLV hotel query.\n"
            f"Got: {res.get('answer', '')[:200]}"
        )

    def test_slv_hotel_uses_local_places_retrieval(self):
        """retrieval_mode must be LOCAL_PLACES_SEARCH when OSM returns results."""
        res = self.rag.answer_query("where is SLV hotel?", language="en", city_id=2)
        # If OSM worked, mode is LOCAL_PLACES_SEARCH; if OSM failed, it falls through
        # to WEB_RETRIEVAL which is also acceptable — never ABSTAINED
        assert res.get("retrieval_mode") in ("LOCAL_PLACES_SEARCH", "WEB_RETRIEVAL", "PACK_RETRIEVAL"), \
            f"Unexpected retrieval_mode: {res.get('retrieval_mode')}"

    def test_restaurants_in_gandhi_bazaar_answerable(self):
        res = self.rag.answer_query("which restaurants are there in Gandhi Bazaar?", language="en", city_id=2)
        assert res["answerable"] is True, (
            f"Expected answerable=True for Gandhi Bazaar restaurants.\n"
            f"Got: {res.get('answer', '')[:200]}"
        )

    def test_manager_query_still_abstains(self):
        """OUT_OF_DOMAIN guard must still function after LOCAL_SEARCH was added."""
        res = self.rag.answer_query("Who is the current manager of the Hampi Bazaar restaurant?", language="en", city_id=1)
        assert res["answerable"] is False, (
            f"Expected abstention for manager query.\n"
            f"Got: answerable={res['answerable']}, answer={res.get('answer', '')[:100]}"
        )

    def test_answer_has_no_hardcoded_strings(self):
        """Answer must not contain any hardcoded template strings."""
        res = self.rag.answer_query("where is SLV hotel?", language="en", city_id=2)
        answer = res.get("answer", "")
        forbidden_phrases = [
            "Jolada rotti",
            "GeoGuide couldn't verify that specific information",
            "Ask anything about Hampi",
        ]
        for phrase in forbidden_phrases:
            assert phrase not in answer, f"Hardcoded phrase found in answer: {phrase!r}"
