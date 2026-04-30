# AutiSense Full App Bug Fix & Run Guide
## Status: In Progress

### Step 1: Fix Frontend Merge Conflicts ✅
- [x] `pfe_frontend/lib/services/api_service.dart` - Fixed merge conflicts, duplicates
- [x] `pfe_frontend/lib/screens/psychologist/psychologist_screen.dart` - Fixed massive _MessagesTab merge conflict

### Step 2: Verify Dependencies & Models [TODO]
- [ ] Check `pfe_frontend/lib/models/models.dart`
- [ ] `pfe_frontend/pubspec.yaml`

### Step 3: Backend Verification [TODO]
- [ ] `python manage.py check`
- [ ] `makemigrations && migrate`
- [ ] `python seed.py`

### Step 4: Create Full Run Guide [TODO]
- [ ] `FULL_RUN_GUIDE.md`

### Step 5: Test Compilation & Run [TODO]
- Backend: `python manage.py runserver`
- Frontend: `cd ../pfe_frontend && flutter clean && pub get && run`

### Step 6: Physical Phone Setup [TODO]
- Enable USB debugging, `flutter devices`, `flutter run -d <id>`



