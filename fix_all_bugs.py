#!/usr/bin/env python3
"""
Fix all critical Flutter bugs found by flutter analyze
"""

import re

def fix_file(filepath, fixes):
    """Apply multiple regex fixes to a file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {filepath}")
        return True
    return False

# Fix psychologist_screen.dart - remaining issues
psychologist_fixes = [
    # Fix escaped dollar signs in error message
    (r"Text\('Connection Error: \\\$\{snapshot\.error}'\)", r"Text('Connection Error: ${snapshot.error}')"),
    # Fix the conversation empty message with escaped newlines
    (r"'No conversations yet\.\\nContact parents directly after reviewing assessments\.'", 
     r"'No conversations yet.\\nContact parents directly after reviewing assessments.'"),
    (r'"No conversations yet\.\\nContact parents directly after reviewing assessments\."', 
     r'"No conversations yet.\nContact parents directly after reviewing assessments."'),
    # Fix remaining \\\n patterns
    (r"\\n", r"\n"),
]

# Fix parent_screen.dart - ScoreBadge positional arguments  
parent_fixes = [
    # ScoreBadge takes positional argument, not named
    (r"ScoreBadge\(score: ", r"ScoreBadge("),
    # StatusBadge takes positional argument, not named  
    (r"StatusBadge\(status: ", r"StatusBadge("),
    # Fix orphaned ScoreBadge and StatusBadge closing parenthesis
    (r"ScoreBadge\(([\w\.]+)\)", r"ScoreBadge(\1)"),
    (r"StatusBadge\(([\w\.]+)\)", r"StatusBadge(\1)"),
]

# Fix common_widgets.dart
common_fixes = [
    # Fix invalid constant value at line 99 - probably a nullable issue
    (r"severityColor\s*\{\s*switch\s*\(\s*severity\.toLowerCase\(\)\s*\)\s*\{\s*case\s+'mild':\s*return\s+const\s+Color\(0xFF50C878\);\s*case\s+'moderate':\s*return\s+const\s+Color\(0xFFFF8C00\);\s*case\s+'severe':\s*return\s+const\s+Color\(0xFFE74C3C\);\s*default:\s*return\s+const\s+Color\(0xFF7F8C8D\);\s*\}\s*\}", 
     r"""severityColor {
    switch (severity.toLowerCase()) {
      case 'mild':
        return const Color(0xFF50C878);
      case 'moderate':
        return const Color(0xFFFF8C00);
      case 'severe':
        return const Color(0xFFE74C3C);
      default:
        return const Color(0xFF7F8C8D);
    }
  }"""),
]

# Apply fixes
fix_file(r"c:\autisense\backend\pfe_frontend\lib\screens\psychologist\psychologist_screen.dart", psychologist_fixes)
fix_file(r"c:\autisense\backend\pfe_frontend\lib\screens\parent\parent_screen.dart", parent_fixes)
fix_file(r"c:\autisense\backend\pfe_frontend\lib\widgets\common_widgets.dart", common_fixes)

print("\nAll critical fixes applied!")
