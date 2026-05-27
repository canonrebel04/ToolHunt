## 2026-05-27 - Unnecessary Expensive Code on Health Check endpoint
 **Vulnerability:** DoS (Denial of Service) via high-cost execution on `/health` endpoint due to `search_tool("*")` calling heavy Machine Learning pipelines instead of cheap database loading.
 **Learning:** Health checks must be lightweight, they get polled often. A slow health endpoint can take the whole system down by starving thread pools/resources.
 **Prevention:** Keep health endpoints light. For simple data counts, query the cache or database directly. Never put heavy computation on a highly accessible uncontrolled endpoint.
