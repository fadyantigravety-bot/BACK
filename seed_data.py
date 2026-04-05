"""
Seed script for Church Follow-up System — creates test users and sample data.
Run: python manage.py shell < seed_data.py
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User, PriestProfile, ServiceLeaderProfile, ServantProfile, MemberProfile
from church.models import ServiceStage, ServiceGroup
from prayers.models import PrayerDefinition, PrayerLog
from friday_attendance.models import FridayMeetingSession, FridayAttendanceRecord
from confessions.models import ConfessionRecord
from followups.models import FollowUpRecord
from notifications.models import Notification
from datetime import date, timedelta, time

print("=" * 50)
print("  بدء إنشاء البيانات التجريبية...")
print("=" * 50)

# ───── 1. Service Stages & Groups ─────
stage1, _ = ServiceStage.objects.get_or_create(name='ابتدائي', defaults={'description': 'مرحلة ابتدائي', 'order': 1})
stage2, _ = ServiceStage.objects.get_or_create(name='إعدادي', defaults={'description': 'مرحلة إعدادي', 'order': 2})
stage3, _ = ServiceStage.objects.get_or_create(name='ثانوي', defaults={'description': 'مرحلة ثانوي', 'order': 3})
print(f"✓ مراحل الخدمة: {ServiceStage.objects.count()}")

group1, _ = ServiceGroup.objects.get_or_create(name='مجموعة أ', defaults={'stage': stage1})
group2, _ = ServiceGroup.objects.get_or_create(name='مجموعة ب', defaults={'stage': stage2})
group3, _ = ServiceGroup.objects.get_or_create(name='مجموعة ج', defaults={'stage': stage3})
print(f"✓ مجموعات الخدمة: {ServiceGroup.objects.count()}")

# ───── 2. Users ─────
# Priest
priest_user = User.objects.filter(phone='01000000001').first()
if not priest_user:
    priest_user = User.objects.create_user(
        phone='01000000001', password='priest123',
        first_name='أبونا', last_name='مينا', role='priest', email='priest@test.com'
    )
    PriestProfile.objects.get_or_create(user=priest_user)
print(f"✓ كاهن: {priest_user.first_name} {priest_user.last_name} (01000000001 / priest123)")

# Service Leader
leader_user = User.objects.filter(phone='01000000002').first()
if not leader_user:
    leader_user = User.objects.create_user(
        phone='01000000002', password='leader123',
        first_name='مارك', last_name='عادل', role='service_leader', email='leader@test.com'
    )
    ServiceLeaderProfile.objects.get_or_create(user=leader_user, defaults={'service_stage': stage1})
print(f"✓ مسؤول خدمة: {leader_user.first_name} {leader_user.last_name} (01000000002 / leader123)")

# Servant
servant_user = User.objects.filter(phone='01000000003').first()
if not servant_user:
    servant_user = User.objects.create_user(
        phone='01000000003', password='servant123',
        first_name='يوسف', last_name='سمير', role='servant', email='servant@test.com'
    )
    ServantProfile.objects.get_or_create(user=servant_user, defaults={'service_group': group1, 'supervisor': leader_user})
print(f"✓ خادم: {servant_user.first_name} {servant_user.last_name} (01000000003 / servant123)")

# Members
members = []
member_data = [
    ('جورج', 'فادي', '01100000001', 'male', '2010-03-15'),
    ('مريم', 'سامي', '01100000002', 'female', '2011-07-22'),
    ('بيتر', 'ماجد', '01100000003', 'male', '2009-12-01'),
    ('ماريا', 'عماد', '01100000004', 'female', '2010-09-10'),
    ('أندرو', 'نبيل', '01100000005', 'male', '2008-04-05'),
]

for fn, ln, phone, gender, dob in member_data:
    u = User.objects.filter(phone=phone).first()
    if not u:
        u = User.objects.create_user(phone=phone, password='member123', first_name=fn, last_name=ln, role='member')
        MemberProfile.objects.get_or_create(
            user=u, defaults={
                'date_of_birth': dob, 'gender': gender,
                'service_group': group1, 'assigned_servant': servant_user,
            }
        )
    members.append(u)
print(f"✓ مخدومين: {len(members)} أعضاء (كلمة المرور: member123)")

# ───── 3. Prayer Definitions ─────
prayers_data = [
    ('صلاة باكر', '07:00', 1),
    ('صلاة الساعة الثالثة', '09:00', 2),
    ('صلاة الساعة السادسة', '12:00', 3),
    ('صلاة الساعة التاسعة', '15:00', 4),
    ('صلاة الغروب', '18:00', 5),
    ('صلاة النوم', '22:00', 6),
]
for name, stime, order in prayers_data:
    PrayerDefinition.objects.get_or_create(name=name, defaults={'scheduled_time': stime, 'order': order})
print(f"✓ صلوات: {PrayerDefinition.objects.count()} صلاة مُعرّفة")

# Create today's prayer logs for all members
today = date.today()
from datetime import datetime
prayer_defs = list(PrayerDefinition.objects.all())
logs_created = 0
for member in members:
    for pdef in prayer_defs:
        scheduled_dt = datetime.combine(today, pdef.scheduled_time)
        from django.utils import timezone
        scheduled_dt = timezone.make_aware(scheduled_dt)
        _, created = PrayerLog.objects.get_or_create(
            member=member, prayer=pdef, date=today,
            defaults={'scheduled_time': scheduled_dt}
        )
        if created: logs_created += 1
# Mark some as completed
for member in members[:3]:
    PrayerLog.objects.filter(member=member, date=today, prayer__order__lte=3).update(status='completed')
print(f"✓ سجلات صلاة اليوم: {logs_created} سجل")

# ───── 4. Friday Attendance ─────
last_friday = today - timedelta(days=(today.weekday() + 3) % 7)  # Most recent Friday
session, _ = FridayMeetingSession.objects.get_or_create(
    date=last_friday, defaults={'title': 'اجتماع الجمعة', 'service_stage': stage1}
)
statuses = ['present', 'present', 'present', 'absent', 'excused']
for i, member in enumerate(members):
    FridayAttendanceRecord.objects.get_or_create(
        session=session, member=member,
        defaults={'status': statuses[i], 'marked_by': servant_user}
    )
print(f"✓ حضور الجمعة: جلسة {last_friday} (3 حاضر، 1 غائب، 1 معتذر)")

# ───── 5. Follow-up Records ─────
from django.utils import timezone as tz
now = tz.now()
FollowUpRecord.objects.get_or_create(
    member=members[3], servant=servant_user, date=now,
    defaults={
        'type': 'phone_call', 'priority': 'high', 'status': 'pending',
        'summary': 'المتابعة بسبب الغياب المتكرر',
    }
)
FollowUpRecord.objects.get_or_create(
    member=members[4], servant=servant_user, date=now - timedelta(days=3),
    defaults={
        'type': 'visit', 'priority': 'urgent', 'status': 'overdue',
        'summary': 'زيارة منزلية بسبب الانقطاع',
    }
)
print(f"✓ متابعات: {FollowUpRecord.objects.count()} سجل")

# ───── 6. Confession Records ─────
for member in members[:3]:
    ConfessionRecord.objects.get_or_create(
        member=member, defaults={
            'recorded_by': priest_user,
            'has_confessed': True,
            'last_confession_date': today - timedelta(days=10),
        }
    )
ConfessionRecord.objects.get_or_create(
    member=members[3], defaults={
        'recorded_by': priest_user,
        'has_confessed': False,
        'last_confession_date': today - timedelta(days=45),
        'is_overdue': True,
    }
)
print(f"✓ سجلات الاعتراف: {ConfessionRecord.objects.count()}")

# ───── 7. Notifications ─────
Notification.objects.get_or_create(
    recipient=priest_user, notification_type='absence_alert',
    defaults={
        'title': 'تنبيه غياب', 'body': f'ماريا عماد غائبة لمدة 3 أسابيع متتالية',
    }
)
Notification.objects.get_or_create(
    recipient=servant_user, notification_type='followup_due',
    defaults={
        'title': 'متابعة مطلوبة', 'body': 'يجب متابعة أندرو نبيل — زيارة منزلية',
    }
)
for member in members:
    Notification.objects.get_or_create(
        recipient=member, notification_type='prayer_alert',
        defaults={'title': 'حان وقت الصلاة', 'body': 'صلاة باكر — ابدأ يومك بالصلاة'}
    )
print(f"✓ إشعارات: {Notification.objects.count()}")

print()
print("=" * 50)
print("  ✅ تم إنشاء البيانات التجريبية بنجاح!")
print("=" * 50)
print()
print("┌─────────────────────────────────────────────┐")
print("│ بيانات الدخول للاختبار                     │")
print("├─────────────────────────────────────────────┤")
print("│  كاهن:     01000000001 / priest123          │")
print("│  مسؤول:    01000000002 / leader123          │")
print("│  خادم:     01000000003 / servant123         │")
print("│  مخدوم:    01100000001 / member123          │")
print("└─────────────────────────────────────────────┘")
