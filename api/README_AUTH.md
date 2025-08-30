# TauLayer Authentication & Authorization

This document explains the reasoning and design behind TauLayer’s authentication and authorization system using **Supabase** and a custom **`public.users`** table.

---

## 🔑 Authentication (Who you are)

TauLayer uses **Supabase Auth** as the source of truth for user authentication:

- Users must exist in Supabase’s **`auth.users`** table.
- **Invite-only** sign-up model:
  - New users cannot self-register.
  - An admin must invite a user via the Supabase dashboard or API.
  - Supabase sends the invited user a secure link via email.
- After accepting the invite, users sign in using a **magic link**.
- Every request’s **JWT** is verified against Supabase’s JWKS (RS256) to ensure authenticity.

---

## 🔒 Authorization (What you can do)

Supabase Auth tells us *who* the user is, but TauLayer often needs more:

- **Tenant scoping**: associate users with a `client_name` (e.g., *Client Alpha*).
- **Custom metadata**: store default priority, API key hash, or usage quotas.
- **Per-client limits**: enforce rules around cost, latency, or access levels.

For this reason we maintain a **`public.users`** table:

| Column            | Purpose                                    |
|-------------------|--------------------------------------------|
| `email`           | Maps back to Supabase Auth email           |
| `client_name`     | Identifies which tenant a user belongs to  |
| `default_priority`| Controls request priority defaults         |
| `api_key_hash`    | Supports API key–based access (optional)   |
| `created_at`      | Auditing & lifecycle tracking              |

---

## ⚡ Why both layers?

- **Supabase Auth → Authentication**
  - Secure invite, confirmation, and JWT issuance.
  - Prevents unauthorized sign-ups.
- **`public.users` → Authorization**
  - Holds tenant/business-level metadata.
  - Ensures users only access their own client’s data.
  - Supports analytics and usage enforcement.

---

## 🚀 Typical Flow

1. **Admin invites user**
   - User is added to Supabase `auth.users`.
   - A corresponding row is inserted in `public.users` with tenant info.
   - Supabase sends an invite email.

2. **User signs in with magic link**
   - Supabase issues a JWT.
   - Backend verifies the JWT against Supabase JWKS.
   - Claims (`sub`, `email`) extracted.

3. **Backend cross-checks `public.users`**
   - Finds the user’s email.
   - Loads tenant metadata (priority, client name).
   - Applies authorization rules.

4. **Request processed**
   - Executed under tenant-aware rules.
   - Usage and analytics tied to the correct client.

---

## ✅ Benefits

- Strong security (Supabase JWTs, RS256).
- Invite-only onboarding.
- Clear separation of concerns:
  - Authentication = Supabase Auth.
  - Authorization = `public.users`.
- Enables multi-tenant SaaS, with per-client rules.

---

## ❓ FAQ

**Q: Why not only rely on Supabase Auth?**  
A: Auth provides identity, but not tenant context or business metadata. `public.users` adds this layer.

**Q: What happens if a user is in Auth but missing in `public.users`?**  
A: They can authenticate, but won’t be authorized until added to `public.users`.

**Q: What if it’s single-tenant?**  
A: You could skip `public.users` and rely solely on Supabase Auth. For multi-tenant SaaS, keep both layers.
