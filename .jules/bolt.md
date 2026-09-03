## 2025-03-01 - O(N) divisions vs O(1) comparison
**Learning:** The previous implementation calculated `similarity = 1.0 / (1.0 + distance)` in a loop for each FAISS result, performing O(N) divisions. We can optimize this by algebraically converting the target threshold to a max distance once outside the loop.
**Action:** Use inverse calculations to pull expensive math operations out of large loops whenever filtering thresholds.
