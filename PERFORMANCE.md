# H1-AI Performance Benchmarks

## Environment
- **CPU**: Intel i5-2400S (4 cores @ 2.5-3.3 GHz)
- **RAM**: 16GB DDR3
- **OS**: Debian 13 (LMDE 7)
- **PostgreSQL**: 17.11
- **Python**: 3.13.5
- **Uvicorn**: 2 workers, uvloop, httptools

## Results (clean environment)

| Users | Duration | Requests | Failures | Avg | P95 | P99 | RPS |
|-------|----------|----------|----------|-----|-----|-----|-----|
| 10 | 30s | 234 | 0% | 8ms | 31ms | 69ms | 7.9 |
| 50 | 60s | 2,216 | 0% | 9ms | 30ms | 97ms | 37.1 |
| 200 | 120s | 18,231 | 0% | 16ms | 59ms | 120ms | 152.2 |

## Endpoint Breakdown (200 users)

| Endpoint | Requests | Avg | P99 |
|----------|----------|-----|-----|
| GET /health | 9,001 | 9ms | 74ms |
| GET /ready | 3,537 | 9ms | 78ms |
| GET /v1/products | 2,728 | 19ms | 83ms |
| POST /v1/knowledge/search | 1,720 | 20ms | 120ms |
| POST /v1/chat | 374 | 117ms | 260ms |
| POST /v1/webhook | 870 | 41ms | 120ms |

## Resource Usage (200 users)
- RAM: 3.1GB / 15GB (20%)
- Load average: 0.57 / 4 cores (14%)
- Swap: unused
- Zero errors, zero timeouts

## Notes
- Tests run with SOC monitoring stack stopped
- CPU governor: performance mode
- Rate limits: CHAT=10000/min, AUTH=10/min (test config)
