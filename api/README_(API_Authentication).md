### 🔐 API Authentication

- Clients may send `X-API-Key` header for authenticated requests
- Keys are hashed with SHA-256 and stored in the `users.api_key_hash` column
- If no key is provided, request is treated as anonymous
- You can protect routes using `Depends(require_api_key)`

To generate a key:
```python
from auth import generate_api_key, hash_api_key
api_key = generate_api_key()
api_key_hash = hash_api_key(api_key)