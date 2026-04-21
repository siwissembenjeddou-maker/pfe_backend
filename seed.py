#!/usr/bin/env python
import os
import sys
import django
from datetime import date, timedelta, time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autisense.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.users.models import User
from apps.children.models import Child
from apps.assessments.models import Assessment
from apps.notifications.models import Notification
from apps.schedules.models import ActivitySchedule

print("🌱  Seeding AutiSense database …")

def create_user(email, name, role, password='demo1234'):
    if User.objects.filter(email=email).exists():
        print(f"   ⚠ User {email} already exists, skipping.")
        return User.objects.get(email=email)
    parts = name.split(' ', 1)
    u = User(
        username=email, email=email, role=role,
        first_name=parts[0],
        last_name=parts[1] if len(parts) > 1 else '',
        is_active=True,
    )
    u.set_password(password)
    u.save()
    print(f"   ✅ Created {role}: {name}  ({email})")
    return u

admin  = create_user('demo.admin@autisense.app',        'Admin AutiSense',    'admin')
p1     = create_user('demo.parent@autisense.app',       'Sarah Johnson',      'parent')
p2     = create_user('parent2@autisense.app',           'Ahmed Benali',       'parent')
psych1 = create_user('demo.psychologist@autisense.app', 'Dr. Emily Carter',   'psychologist')
psych2 = create_user('psych2@autisense.app',            'Dr. Karim Mansouri', 'psychologist')
edu1   = create_user('demo.educator@autisense.app',     'Ms. Laura Bennett',  'educator')
edu2   = create_user('educator2@autisense.app',         'Mr. Youssef Hakim',  'educator')

def create_child(name, dob_str, gender, parent, notes=''):
    if Child.objects.filter(name=name, parent=parent).exists():
        print(f"   ⚠ Child {name} already exists, skipping.")
        return Child.objects.get(name=name, parent=parent)
    c = Child.objects.create(
        name=name,
        date_of_birth=date.fromisoformat(dob_str),
        gender=gender, parent=parent, notes=notes,
    )
    print(f"   ✅ Created child: {name}")
    return c

child1 = create_child('Liam Johnson',   '2019-03-15', 'male',   p1, 'Loves trains and drawing.')
child2 = create_child('Emma Johnson',   '2021-07-22', 'female', p1, 'Very sensitive to sounds.')
child3 = create_child('Yassine Benali', '2018-11-05', 'male',   p2, 'Enjoys repetitive play.')
child4 = create_child('Nour Benali',    '2020-09-18', 'female', p2, 'Limited verbal communication.')

SAMPLE_ASSESSMENTS = [
    {
        'child': child1, 'activity_type': 'Playing',
        'transcription': 'Liam lines up his toy trains in exact order and gets very upset if any are moved. He plays alone for hours without looking up or responding when called.',
        'autism_score': 5.8, 'severity_level': 'moderate',
        'dimension_scores': {
            'Social Interaction': 6.5, 'Communication': 5.0,
            'Repetitive Behaviors': 7.5, 'Sensory Response': 4.0,
            'Daily Living Skills': 5.5, 'Emotional Regulation': 6.0,
        },
        'ai_analysis': 'Liam demonstrates clear repetitive and restrictive behaviours during play, including rigid ordering rituals and significant emotional distress when routines are disrupted.',
        'status': 'confirmed',
    },
    {
        'child': child2, 'activity_type': 'Eating',
        'transcription': 'Emma refuses most foods. She will only eat beige or white foods and panics if a new food touches her plate. She gags when she smells certain foods.',
        'autism_score': 4.5, 'severity_level': 'moderate',
        'dimension_scores': {
            'Social Interaction': 3.0, 'Communication': 4.0,
            'Repetitive Behaviors': 5.5, 'Sensory Response': 7.5,
            'Daily Living Skills': 5.0, 'Emotional Regulation': 4.5,
        },
        'ai_analysis': 'Emma\'s eating difficulties are primarily driven by significant sensory hypersensitivity to texture, colour, and smell.',
        'status': 'pending',
    },
    {
        'child': child3, 'activity_type': 'Social Interaction',
        'transcription': 'Yassine does not look at other children and walks away when they try to play. He spends most of recess spinning in circles. He has about 5 words he uses.',
        'autism_score': 7.8, 'severity_level': 'severe',
        'dimension_scores': {
            'Social Interaction': 8.5, 'Communication': 8.0,
            'Repetitive Behaviors': 8.0, 'Sensory Response': 7.0,
            'Daily Living Skills': 7.5, 'Emotional Regulation': 8.5,
        },
        'ai_analysis': 'Yassine presents with severe autism indicators across multiple domains. Extremely limited verbal communication and absence of social engagement require immediate intensive intervention.',
        'status': 'corrected',
        'corrected_score': 8.1,
        'psychologist_note': 'Score confirmed at 8.1. Immediate referral for intensive ABA and AAC evaluation is critical.',
    },
    {
        'child': child4, 'activity_type': 'Writing',
        'transcription': 'Nour holds the pencil in her fist and presses very hard. She scribbles in the same corner every time and does not attempt letters.',
        'autism_score': 2.4, 'severity_level': 'mild',
        'dimension_scores': {
            'Social Interaction': 2.5, 'Communication': 2.0,
            'Repetitive Behaviors': 3.0, 'Sensory Response': 2.5,
            'Daily Living Skills': 2.5, 'Emotional Regulation': 2.0,
        },
        'ai_analysis': 'Nour shows mild indicators. Atypical pencil grip and repetitive spatial positioning during writing are consistent with fine motor delays.',
        'status': 'pending',
    },
]

for a_data in SAMPLE_ASSESSMENTS:
    child = a_data['child']
    if Assessment.objects.filter(child=child, activity_type=a_data['activity_type']).exists():
        print(f"   ⚠ Assessment for {child.name}/{a_data['activity_type']} exists, skipping.")
        continue
    Assessment.objects.create(
        child=child,
        activity_type=a_data['activity_type'],
        audio_transcription=a_data['transcription'],
        autism_score=a_data['autism_score'],
        severity_level=a_data['severity_level'],
        dimension_scores=a_data['dimension_scores'],
        ai_analysis=a_data['ai_analysis'],
        status=a_data.get('status', 'pending'),
        corrected_score=a_data.get('corrected_score'),
        psychologist_note=a_data.get('psychologist_note', ''),
        reviewed_by=psych1 if a_data.get('status') in ('confirmed', 'corrected') else None,
    )
    print(f"   ✅ Assessment: {child.name} – {a_data['activity_type']}")

notif_data = [
    (p1,     'Assessment Reviewed',       'Liam\'s Playing assessment has been confirmed. Score: 5.8/10.',    'review_complete'),
    (p2,     'Assessment Review Complete','Yassine\'s assessment corrected. Updated score: 8.1/10 (Severe).',  'review_complete'),
    (psych1, 'New Assessment Pending',    'Emma Johnson has a new Eating assessment. AI Score: 4.5/10.',       'assessment_result'),
    (psych1, 'New Assessment Pending',    'Nour Benali has a new Writing assessment. AI Score: 2.4/10.',       'assessment_result'),
    (edu1,   'Schedule Updated',          'A new Social Interaction session has been added for tomorrow.',     'reminder'),
]
for recipient, title, message, ntype in notif_data:
    if not Notification.objects.filter(recipient=recipient, title=title).exists():
        Notification.objects.create(recipient=recipient, title=title, message=message, type=ntype)
        print(f"   ✅ Notification → {recipient.name}: {title}")

today = date.today()
sched_data = [
    ('Sensory Play Session',    'Sensory Response',   today + timedelta(days=1), time(10, 0),  'Sensory bins, water play, and tactile exploration.'),
    ('Communication Circle',    'Communicating',      today + timedelta(days=2), time(9, 30),  'Group AAC practice and social story sharing.'),
    ('Fine Motor Workshop',     'Writing',            today + timedelta(days=3), time(11, 0),  'Pencil grip exercises, tracing, and cutting skills.'),
    ('Social Skills Play Date', 'Social Interaction', today + timedelta(days=5), time(14, 0),  'Structured peer interaction with turn-taking games.'),
]
for title, atype, d, t, desc in sched_data:
    if not ActivitySchedule.objects.filter(title=title).exists():
        ActivitySchedule.objects.create(
            title=title, description=desc, date=d, time=t,
            activity_type=atype, created_by=edu1,
            participant_ids=[child1.id, child2.id, child3.id],
        )
        print(f"   ✅ Schedule: {title}")

print("\n✅  Seed complete!")
print("─" * 50)
print("   Role           Email                              Password")
print("─" * 50)
for role, email in [
    ('Admin',        'demo.admin@autisense.app'),
    ('Parent',       'demo.parent@autisense.app'),
    ('Psychologist', 'demo.psychologist@autisense.app'),
    ('Educator',     'demo.educator@autisense.app'),
]:
    print(f"   {role:<14} {email:<36} demo1234")
print("─" * 50)