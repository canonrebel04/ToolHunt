## 2025-05-28 - Insecure FAISS Index Deserialization
**Vulnerability:** FAISS.load_local was called with allow_dangerous_deserialization=True, potentially allowing arbitrary code execution if a malicious pickle file were loaded.
**Learning:** Always be cautious when deserializing data from disk using pickle or libraries that rely on it.
**Prevention:** Explicitly set allow_dangerous_deserialization=False when loading FAISS indices to enforce security checks, or avoid loading indices from untrusted sources.
