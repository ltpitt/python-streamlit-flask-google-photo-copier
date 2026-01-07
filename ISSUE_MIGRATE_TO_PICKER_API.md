# Issue: Migrate from Google Photos Library API to Picker API

## Problem Description

The application currently fails with **403 Forbidden** errors when attempting to list photos from Google Photos because Google **removed the required OAuth scopes** on **March 31, 2025**.

### Current Error
```
HTTP Error: 403 Client Error: Forbidden for url: 
https://photoslibrary.googleapis.com/v1/mediaItems?pageSize=100
```

### Root Cause

Google Photos Library API changes (effective April 1, 2025):
- ❌ **REMOVED scopes**:
  - `https://www.googleapis.com/auth/photoslibrary.readonly` 
  - `https://www.googleapis.com/auth/photoslibrary`
  - `https://www.googleapis.com/auth/photoslibrary.sharing`

- ✅ **Remaining scopes** (only for app-created content):
  - `photoslibrary.appendonly` - Upload new media only
  - `photoslibrary.readonly.appcreateddata` - Read only app-created content
  - `photoslibrary.edit.appcreateddata` - Edit only app-created content

**The Library API can NO LONGER access the user's entire photo library.**

Source: [Google Photos API Updates](https://developers.google.com/photos/support/updates)

---

## Current Architecture

```
Streamlit UI → Flask API → GooglePhotosClient → Library API REST endpoints
                                                  └─> mediaItems.list (403 FORBIDDEN)
```

**Current Implementation:**
- `src/google_photos_sync/google_photos/client.py` - Uses Library API REST endpoints
- `src/google_photos_sync/google_photos/auth.py` - OAuth with deprecated scopes
- `src/google_photos_sync/core/compare_service.py` - Compares photos using `list_photos()`
- `src/google_photos_sync/core/sync_service.py` - Syncs photos between accounts

---

## Required Solution

### 1. Migrate to Google Photos Picker API

Replace the Library API integration with the **Google Photos Picker API** for accessing user's entire library.

**New Scope:**
```
https://www.googleapis.com/auth/photospicker.mediaitems.readonly
```

**New Architecture:**
```
Streamlit UI → Flask API → Picker API Integration
                           ├─> Create session
                           ├─> Get session URL (for user selection)
                           └─> Retrieve selected media items
```

### 2. Key Differences

| Feature | Library API (Old) | Picker API (New) |
|---------|------------------|------------------|
| Access | Entire library programmatically | User selects specific photos via UI |
| Scope | `photoslibrary.readonly` (removed) | `photospicker.mediaitems.readonly` |
| Flow | Direct API calls | Session-based with user interaction |
| List All Photos | ✅ Yes (was possible) | ❌ No (user must select) |
| Compare Entire Libraries | ✅ Yes | ❌ No (only selected items) |

### 3. Impact on Features

**This migration fundamentally changes the app's capabilities:**

- ❌ **Cannot compare entire libraries** automatically
- ❌ **Cannot sync all photos** without user selection
- ✅ **Can let user select specific photos** to sync
- ✅ **Can upload selected photos** to target account

**Alternative Approach: Restrict to App-Created Content**

If the goal is to sync photos that *this app* uploaded:
- Use `photoslibrary.readonly.appcreateddata` scope
- Use `photoslibrary.appendonly` scope for uploads
- Library API methods work for app-created content only

---

## Implementation Tasks

### Phase 1: Research & Design
- [ ] Read [Picker API documentation](https://developers.google.com/photos/picker/guides/get-started-picker)
- [ ] Determine if Picker API fits the use case (user-selected photos only)
- [ ] **Decision Point:** Use Picker API OR pivot to app-created content only?

### Phase 2: Update Authentication (if using Picker API)
- [ ] Update `src/google_photos_sync/google_photos/auth.py`:
  - Replace scopes with `https://www.googleapis.com/auth/photospicker.mediaitems.readonly`
  - Remove deprecated scopes
- [ ] Update `.env.example` with new scope documentation
- [ ] Delete old credentials: `~/.google_photos_sync/credentials/*.json`

### Phase 3: Implement Picker API Client
- [ ] Create `src/google_photos_sync/google_photos/picker_client.py`:
  ```python
  class GooglePhotosPickerClient:
      """Client for Google Photos Picker API."""
      
      def create_session(self, config: SessionConfig) -> Session:
          """Create a new picker session.
          
          POST https://photospicker.googleapis.com/v1/sessions
          """
          pass
      
      def get_session(self, session_id: str) -> Session:
          """Get session details and media items.
          
          GET https://photospicker.googleapis.com/v1/sessions/{sessionId}
          """
          pass
      
      def delete_session(self, session_id: str) -> None:
          """Delete a session.
          
          DELETE https://photospicker.googleapis.com/v1/sessions/{sessionId}
          """
          pass
  ```

### Phase 4: Update Core Services
- [ ] Modify `src/google_photos_sync/core/compare_service.py`:
  - Change from `list_photos()` to session-based selection
  - User must manually select photos in both accounts
- [ ] Modify `src/google_photos_sync/core/sync_service.py`:
  - Sync only user-selected photos (not entire library)
  - Use `photoslibrary.appendonly` scope for uploads

### Phase 5: Update UI Flow
- [ ] Update `src/google_photos_sync/ui/components/auth_component.py`:
  - Update OAuth scope documentation
- [ ] Update `src/google_photos_sync/ui/components/compare_view.py`:
  - Add "Select Photos" workflow using Picker API session URL
  - Display selected photos from both accounts
  - Compare selected items only
- [ ] Update `src/google_photos_sync/ui/components/sync_view.py`:
  - Show selected photos to sync
  - Clarify that sync is for selected items only

### Phase 6: Update Flask API
- [ ] Add routes in `src/google_photos_sync/api/routes.py`:
  - `POST /api/picker/session` - Create picker session
  - `GET /api/picker/session/{id}` - Get session and selected items
  - `DELETE /api/picker/session/{id}` - Delete session
- [ ] Update `/api/compare` to use session-based comparison
- [ ] Update `/api/sync` to use session-based sync

### Phase 7: Update Documentation
- [ ] Update `README.md`:
  - Explain new Picker API workflow
  - Clarify limitations (user must select photos)
  - Update architecture diagram
- [ ] Update `docs/OAUTH_SETUP.md`:
  - Remove deprecated scopes
  - Add Picker API scope
- [ ] Update `docs/user_guide.md`:
  - Explain new photo selection workflow
  - Set correct expectations (not automatic full library sync)

### Phase 8: Testing
- [ ] Update `tests/unit/test_google_photos_client.py` → `test_picker_client.py`
- [ ] Update `tests/integration/test_api_routes.py` with new picker endpoints
- [ ] Update `tests/e2e/test_sync_workflow.py` with session-based flow
- [ ] Manual testing with real Google account

### Phase 9: Migration Guide
- [ ] Create `MIGRATION_GUIDE.md`:
  - Explain breaking changes
  - Provide step-by-step migration for existing users
  - List removed features (automatic full library comparison)

---

## Alternative: Pivot to App-Created Content Only

**If the use case is to sync photos uploaded by this app:**

### Simplified Approach
- Keep Library API integration
- Change scopes to:
  - `photoslibrary.appendonly` - For uploads
  - `photoslibrary.readonly.appcreateddata` - For listing/reading
- Update documentation to clarify: "Syncs only photos uploaded via this app"
- This avoids the Picker API complexity but limits functionality

### Tasks for This Approach
- [ ] Update scopes in `auth.py`
- [ ] Update UI to set expectations (app-created content only)
- [ ] Test that `mediaItems.list` works with new scope
- [ ] Update documentation

---

## Acceptance Criteria

### For Picker API Migration
- [ ] OAuth flow uses `photospicker.mediaitems.readonly` scope
- [ ] User can select photos from source account via Picker UI
- [ ] User can select photos from target account via Picker UI
- [ ] App compares selected photos from both accounts
- [ ] App syncs selected photos to target account
- [ ] No 403 Forbidden errors
- [ ] All tests pass with 90%+ coverage
- [ ] Documentation updated with new workflow

### For App-Created Content Approach
- [ ] OAuth flow uses `photoslibrary.appendonly` + `photoslibrary.readonly.appcreateddata`
- [ ] App can list photos created by the app
- [ ] App can upload new photos
- [ ] App can compare app-created photos between accounts
- [ ] No 403 Forbidden errors
- [ ] Documentation clarifies "app-created content only"

---

## Resources

- [Google Photos Picker API Documentation](https://developers.google.com/photos/picker/guides/get-started-picker)
- [Google Photos API Updates (April 2025)](https://developers.google.com/photos/support/updates)
- [Library API Scopes](https://developers.google.com/photos/overview/authorization#library-api-scopes)
- [Picker API Reference](https://developers.google.com/photos/picker/reference/rest)
- [Authorization Guide](https://developers.google.com/photos/library/guides/authentication-authorization)

---

## Decision Required

**Before implementation, decide:**

1. **Use Picker API** (user selects photos manually)
   - Pros: Can access user's entire library
   - Cons: No automatic full library sync, requires user interaction
   
2. **Use App-Created Content Only** (simple, limited)
   - Pros: Simpler implementation, automatic sync
   - Cons: Only works for photos uploaded by this app

**Recommendation:** Given the original project goal was "sync entire Google Photos library between accounts," this is **no longer possible** with Google Photos APIs as of April 2025. Consider:
- Pivoting to Picker API with user selection
- Or pivoting to a different Google Workspace API if available
- Or reconsidering the project's viability

---

## Related Files

- `src/google_photos_sync/google_photos/auth.py` - OAuth scopes
- `src/google_photos_sync/google_photos/client.py` - Library API client (to be replaced/modified)
- `src/google_photos_sync/core/compare_service.py` - Uses `list_photos()`
- `src/google_photos_sync/core/sync_service.py` - Sync logic
- `src/google_photos_sync/api/routes.py` - API endpoints
- `src/google_photos_sync/ui/components/compare_view.py` - Compare UI
- `.github/copilot-instructions.md` - Update with new API architecture

---

## Priority

**🔴 CRITICAL - Blocks all functionality**

The app is completely non-functional due to removed API scopes. This must be addressed before any other development.
