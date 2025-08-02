from datetime import datetime, timezone
from uuid import uuid4

import factory
import factory.fuzzy

from focus_track_api.models import (
    DailySummary,
    StudySession,
    User,
    UserSettings,
)


class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'test{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@test.com')
    password = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')


class DailySummaryFactory(factory.Factory):
    class Meta:
        model = DailySummary

    user_id = factory.LazyFunction(uuid4)
    avg_fatigue = factory.fuzzy.FuzzyFloat(0.0, 100.0)
    avg_distraction = factory.fuzzy.FuzzyFloat(0.0, 100.0)
    focused_time = factory.fuzzy.FuzzyInteger(0, 480)


class StudySessionFactory(factory.Factory):
    class Meta:
        model = StudySession

    user_id = factory.LazyFunction(uuid4)
    daily_summary_id = factory.LazyFunction(uuid4)
    start_time = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    average_attention_score = factory.fuzzy.FuzzyFloat(0.0, 100.0)
    average_fatigue = factory.fuzzy.FuzzyFloat(0.0, 100.0)
    average_distraction = factory.fuzzy.FuzzyFloat(0.0, 100.0)
    distraction_rate = factory.fuzzy.FuzzyFloat(0.0, 100.0)
    max_fatigue = factory.fuzzy.FuzzyFloat(0.0, 100.0)
    max_distraction = factory.fuzzy.FuzzyFloat(0.0, 100.0)
    perclos = factory.fuzzy.FuzzyFloat(0.0, 100.0)


class UserSettingsFactory(factory.Factory):
    class Meta:
        model = UserSettings

    fatigue_threshold = factory.fuzzy.FuzzyInteger(30, 90)
    distraction_threshold = factory.fuzzy.FuzzyInteger(20, 80)
