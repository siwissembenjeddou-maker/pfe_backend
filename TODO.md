# TODO

- [ ] Add Flutter route/screen for "Forgot Password" so Navigator.pushNamed('/forgot-password') works.
- [ ] Implement ForgotPasswordScreen (enter email -> call ApiService.forgotPassword -> navigate to /verify-reset-code with email).
- [ ] Wire route '/forgot-password' into pfe_frontend/lib/main.dart.
- [ ] Ensure reset flow works end-to-end: Login -> ForgotPassword -> VerifyResetCode -> ResetPassword.
- [ ] Run Flutter analyze/tests (flutter analyze, flutter test) and fix any build errors.
