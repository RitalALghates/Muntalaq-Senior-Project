# Muntalaq (منطلق) - Updated Build

This is the updated build of the senior project with all requirements from the client's change-request document (FR1–FR16, NFR1–NFR7).

## What changed

### New database tables (auto-created on first run)
`courses`, `enrollments`, `favorites`, `graduate_evaluations`, `posts`, `post_likes`, `post_comments`, `groups`, `group_members`, `chat_messages`, `course_offers`.

### Demo data seeding
On first run (when `database.db` doesn't exist), the app auto-seeds:
- 5 demo graduates — all with password `Demo@123`
  - `ahmad.salem@muntalaq.com`
  - `layla.ibrahim@muntalaq.com`
  - `mohammad.hassan@muntalaq.com`
  - `fatima.ahmad@muntalaq.com`
  - `ahmad.saeed@muntalaq.com`
- 7 published courses across different fields
- 5 community groups

### New / updated features mapped to requirements

| Requirement | Where | File |
|---|---|---|
| FR2.3 forgot password | `/forgot-password` | `forgot_password.html` |
| FR5 graduates evaluation (list, search, profile, rate) | `/graduates`, `/graduates/<id>`, `/graduates/<id>/evaluate` | `graduates.html`, `graduate_profile.html`, `evaluate_graduate.html` |
| FR6 browse courses | `/courses` | `courses_list.html` |
| FR7 course details + enroll | `/courses/<id>`, `POST /courses/<id>/enroll` | `course_details.html` |
| FR8 my courses + filter by status | `/my-courses?status=current|completed|cancelled` | `my_courses.html`, `my_courses_graduate.html` |
| FR9 course management (create/cancel/republish) | `/courses/new`, `POST /courses/<id>/cancel`, `POST /courses/<id>/republish` | `course_new.html` |
| FR10.1–10.5 posts feed + search + like + comment | `/community/posts` | `community_posts.html` |
| FR10.6, 10.7 groups + join | `/community` | `community.html` |
| FR10.8 community stats | on `/community` | `community.html` |
| FR10.9 trending hashtags | on `/community` | `community.html` |
| FR11.1–11.3 real chat | `/messages` | `messages.html` |
| FR11.4 graduate shares course offer in chat | offer menu in chat | `messages.html` |
| FR11.5 student accepts/rejects offer | buttons on offer card | `messages.html` |
| FR14 favorites (real DB) | `/favorites`, `POST /api/favorites/<id>` | `favorites.html` |
| FR15.2 language toggle | `/set-language/ar|en` | header button in `base.html` |
| FR16.6 Analyze my profile | `POST /api/analyze-profile` (GPT-4o-mini) | button on `recommendations_ai.html` |

### Requirements already in the project that I preserved
FR1 registration, FR2 login, FR3 profile management, FR4 student dashboard, FR10.2–10.4 post creation/interaction (backend rewritten to use DB), FR12 chatbot, FR13 notifications, FR15.1 settings, FR15.3 notifications toggle, FR15.4 logout, FR16.1–16.5 smart recommendations.

## How to run

```bash
# (optional) delete any old DB so the new schema + seed data apply
rm -f database.db

# install dependencies
pip install -r requirements.txt

# set OpenAI key for AI features (chatbot, evaluation, recommendations, profile analysis)
export OPENAI_API_KEY=sk-...

# run
python app.py
```

Server starts on `http://localhost:5001`.

## Test accounts
- **Graduate:** `ahmad.salem@muntalaq.com` / `Demo@123` (has 2 seed courses)
- **Graduate:** `layla.ibrahim@muntalaq.com` / `Demo@123` (UI/UX instructor)
- **Student:** register a new account through `/account-selection`

## Verified routes (all return 200)
`/`, `/dashboard`, `/courses`, `/courses/<id>`, `/courses/new`, `/my-courses`, `/graduates`, `/graduates/<id>`, `/graduates/<id>/evaluate`, `/community`, `/community/posts`, `/messages`, `/messages?with=<id>`, `/favorites`, `/settings`, `/recommendations`, `/notifications`, `/profile`, `/forgot-password`.

Verified JSON APIs: `/api/favorites/<id>`, `/api/posts/<id>/like`, `/api/posts/<id>/comment`, `/api/messages/send`, `/api/messages/start`, `/api/messages/share-course`, `/api/offer/<id>/respond`, `/api/analyze-profile`.
