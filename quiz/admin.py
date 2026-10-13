from django import forms
from django.contrib import admin
from django.forms import BaseInlineFormSet

from .models import Attempt, Category, Choice, Question, Quiz


class ChoiceInlineFormSet(BaseInlineFormSet):
    """Every question needs at least 2 choices and exactly 1 correct one."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        filled = [f for f in self.forms
                  if f.cleaned_data and not f.cleaned_data.get('DELETE', False)]
        if len(filled) < 2:
            raise forms.ValidationError('Add at least 2 choices.')
        if sum(1 for f in filled if f.cleaned_data.get('is_correct')) != 1:
            raise forms.ValidationError('Mark exactly ONE choice as correct.')


class ChoiceInline(admin.TabularInline):
    model = Choice
    formset = ChoiceInlineFormSet
    extra = 4


class QuestionInline(admin.TabularInline):
    model = Question
    fields = ('text', 'order')
    extra = 1
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'time_limit_minutes', 'pass_percentage', 'is_published')
    list_filter = ('category', 'is_published')
    search_fields = ('title',)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'order')
    list_filter = ('quiz',)
    inlines = [ChoiceInline]


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'total', 'started_at', 'finished_at')
    list_filter = ('quiz',)
