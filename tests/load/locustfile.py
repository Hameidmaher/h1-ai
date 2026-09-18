"""H1-AI Load Testing — Token reuse + realistic scenarios."""
from locust import HttpUser, task, between, events
import os
import random
import logging
import threading

WEBHOOK_API_KEY = os.getenv("WEBHOOK_API_KEY", "")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

# ─── Shared token (login once for all users) ───
_shared_token = None
_token_lock = threading.Lock()


def get_shared_token(client):
    """Get token, reusing across all users."""
    global _shared_token
    if _shared_token:
        return _shared_token
    
    with _token_lock:
        if _shared_token:
            return _shared_token
        
        try:
            r = client.post(
                "/v1/auth/login",
                json={"username": ADMIN_USER, "password": ADMIN_PASS},
                name="[Auth] Login (shared)",
            )
            if r.status_code == 200:
                _shared_token = r.json().get("access_token")
        except Exception as e:
            logging.warning(f"Login failed: {e}")
    
    return _shared_token


class H1AIUser(HttpUser):
    """Simulates a real H1-AI user."""
    
    wait_time = between(0.5, 2.0)
    
    def on_start(self):
        """Use shared token."""
        self.token = get_shared_token(self.client)
        self.session_id = None
    
    @property
    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    # ─── Fast operations ───
    
    @task(50)
    def health_check(self):
        """Health — fastest."""
        self.client.get("/health", name="[Health]")
    
    @task(20)
    def ready_check(self):
        self.client.get("/ready", name="[Health] Ready")
    
    @task(15)
    def list_products(self):
        """Products — fast."""
        if not self.token:
            return
        self.client.get(
            "/v1/admin/products?limit=20",
            headers=self.auth_headers,
            name="[Products]",
        )
    
    @task(10)
    def knowledge_search(self):
        """Knowledge — fast BM25."""
        if not self.token:
            return
        self.client.post(
            "/v1/knowledge/search",
            json={"query": "باراسيتامول", "top_k": 5},
            headers=self.auth_headers,
            name="[Knowledge] Search",
        )
    
    # ─── Medium operations ───
    
    @task(5)
    def webhook_incoming(self):
        """Webhook — full pipeline."""
        if not WEBHOOK_API_KEY:
            return
        phone = f"+2010{random.randint(10000000, 99999999)}"
        self.client.post(
            "/webhook/v2/incoming",
            json={"phone": phone, "message": "عايز بديل"},
            headers={"X-API-Key": WEBHOOK_API_KEY},
            name="[Webhook]",
            timeout=30,
        )
    
    # ─── Slow operations (LLM) ───
    
    @task(2)
    def chat(self):
        """Chat — slow (LLM)."""
        if not self.token:
            return
        with self.client.post(
            "/v1/chat",
            json={"message": "السلام عليكم", "session_id": self.session_id},
            headers=self.auth_headers,
            name="[Chat] LLM",
            timeout=60,
            catch_response=True,
        ) as r:
            if r.status_code == 200:
                try:
                    self.session_id = r.json().get("session_id")
                    r.success()
                except Exception:
                    r.failure("JSON parse")
            elif r.status_code == 429:
                r.failure("Rate limited")
            else:
                r.failure(f"Status {r.status_code}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    s = environment.stats
    print("\n" + "="*60)
    print("  🏁 Final Results")
    print("="*60)
    print(f"  Requests:   {s.total.num_requests:,}")
    print(f"  Failures:   {s.total.num_failures:,} ({s.total.fail_ratio*100:.2f}%)")
    print(f"  Avg:        {s.total.avg_response_time:.0f}ms")
    print(f"  P95:        {s.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"  P99:        {s.total.get_response_time_percentile(0.99):.0f}ms")
    print(f"  RPS:        {s.total.total_rps:.1f}")
    print("="*60 + "\n")
