# Fix escaping issues in psychologist_screen.dart
import re

with open('pfe_frontend/lib/screens/psychologist/psychologist_screen.dart', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix escaped backslash-n in strings
content = content.replace(r'No conversations yet.\\nContact', 'No conversations yet.\nContact')
content = content.replace(r'Connection Error: \${', r'Connection Error: ${')

with open('pfe_frontend/lib/screens/psychologist/psychologist_screen.dart', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed psychologist_screen.dart")
