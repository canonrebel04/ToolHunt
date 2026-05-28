🎯 **What:** The application checks for valid JSON in the `/search` endpoint using `request.get_json(silent=True)` and appropriately rejects invalid JSON with a 400 Bad Request error. However, this specific validation was not covered by any test cases. This PR adds `test_invalid_json_returns_400` to the test suite to specifically test this functionality.

📊 **Coverage:** The new test ensures that a POST request to `/search` with a request body that is not valid JSON string correctly yields a 400 status code and the expected error message `"Invalid JSON body"`.

✨ **Result:** Test coverage for `app/routes.py` is improved, preventing regressions related to request body validation.
