from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Quiz(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='quizzes')
    time_limit_minutes = models.PositiveIntegerField(default=10, validators=[MinValueValidator(1)],
                                                     help_text='Time allowed in minutes.')
    pass_percentage = models.PositiveIntegerField(default=50, validators=[MinValueValidator(1), MaxValueValidator(100)])
    is_published = models.BooleanField(default=True, help_text='Only published quizzes with questions are shown to users.')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        verbose_name_plural = 'quizzes'

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    explanation = models.TextField(blank=True, help_text='Shown on the result page (optional).')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text[:70]


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.text


class Attempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.user} - {self.quiz} ({self.score}/{self.total})'

    @property
    def is_finished(self):
        return self.finished_at is not None

    @property
    def percentage(self):
        return round(self.score * 100 / self.total) if self.total else 0

    @property
    def passed(self):
        return self.percentage >= self.quiz.pass_percentage

    @property
    def duration_seconds(self):
        if not self.finished_at:
            return 0
        return max(0, int((self.finished_at - self.started_at).total_seconds()))

    @property
    def duration_display(self):
        minutes, seconds = divmod(self.duration_seconds, 60)
        return f'{minutes:02d}:{seconds:02d}'

    def remaining_seconds(self):
        elapsed = (timezone.now() - self.started_at).total_seconds()
        return max(0, int(self.quiz.time_limit_minutes * 60 - elapsed))

    def is_late(self, grace_seconds=60):
        elapsed = (timezone.now() - self.started_at).total_seconds()
        return elapsed > self.quiz.time_limit_minutes * 60 + grace_seconds


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='+')
    choice = models.ForeignKey(Choice, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('attempt', 'question')
