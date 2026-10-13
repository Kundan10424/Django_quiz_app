from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import RegisterForm
from .models import Attempt, AttemptAnswer, Category, Quiz


def published_quizzes():
    """Published quizzes that have at least one question."""
    return (Quiz.objects.filter(is_published=True)
            .select_related('category')
            .annotate(question_total=Count('questions', distinct=True))
            .filter(question_total__gt=0))


# ---------------------------------------------------------------- auth
def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Welcome! Your account has been created.')
        return redirect('dashboard')
    return render(request, 'registration/register.html', {'form': form})


# ----------------------------------------------------------- dashboard
@login_required
def dashboard(request):
    finished_qs = Attempt.objects.filter(user=request.user, finished_at__isnull=False).select_related('quiz')
    finished = list(finished_qs[:200])
    percentages = [a.percentage for a in finished]
    context = {
        'attempt_count': finished_qs.count(),
        'average': round(sum(percentages) / len(percentages), 1) if percentages else None,
        'best': max(percentages) if percentages else None,
        'passed_count': sum(1 for a in finished if a.passed),
        'recent': finished[:5],
        'in_progress': Attempt.objects.filter(user=request.user, finished_at__isnull=True).select_related('quiz'),
        'featured': published_quizzes().order_by('-created_at')[:3],
    }
    return render(request, 'quiz/dashboard.html', context)


# ------------------------------------------------------------- quizzes
@login_required
def quiz_list(request):
    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()

    quizzes = published_quizzes()
    if q:
        quizzes = quizzes.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if category_id.isdigit():
        quizzes = quizzes.filter(category_id=int(category_id))

    page_obj = Paginator(quizzes, 6).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'quiz/quiz_list.html', {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'q': q, 'category_id': category_id,
        'querystring': params.urlencode(),
    })


@login_required
def quiz_detail(request, pk):
    quiz = get_object_or_404(published_quizzes(), pk=pk)
    my_attempts = Attempt.objects.filter(user=request.user, quiz=quiz, finished_at__isnull=False)[:5]
    in_progress = Attempt.objects.filter(user=request.user, quiz=quiz, finished_at__isnull=True).first()
    return render(request, 'quiz/quiz_detail.html', {
        'quiz': quiz, 'my_attempts': my_attempts, 'in_progress': in_progress,
    })


@login_required
@require_POST
def quiz_start(request, pk):
    quiz = get_object_or_404(published_quizzes(), pk=pk)
    attempt = Attempt.objects.filter(user=request.user, quiz=quiz, finished_at__isnull=True).first()
    if attempt is None:
        attempt = Attempt.objects.create(user=request.user, quiz=quiz, total=quiz.question_total)
    return redirect('attempt_take', pk=attempt.pk)


# ------------------------------------------------------------ attempts
@login_required
def attempt_take(request, pk):
    attempt = get_object_or_404(Attempt.objects.select_related('quiz'), pk=pk, user=request.user)
    if attempt.is_finished:
        return redirect('attempt_result', pk=attempt.pk)

    questions = list(attempt.quiz.questions.prefetch_related('choices'))

    if request.method == 'POST':
        late = attempt.is_late()
        correct = 0
        with transaction.atomic():
            for question in questions:
                choice = None
                raw = None if late else request.POST.get(f'question_{question.pk}')
                if raw and raw.isdigit():
                    choice = next((c for c in question.choices.all() if c.pk == int(raw)), None)
                is_correct = bool(choice and choice.is_correct)
                correct += int(is_correct)
                AttemptAnswer.objects.update_or_create(
                    attempt=attempt, question=question,
                    defaults={'choice': choice, 'is_correct': is_correct})
            attempt.score = correct
            attempt.total = len(questions)
            attempt.finished_at = timezone.now()
            attempt.save()
        if late:
            messages.error(request, 'Time limit exceeded - late answers were not counted.')
        return redirect('attempt_result', pk=attempt.pk)

    return render(request, 'quiz/attempt_take.html', {
        'attempt': attempt, 'quiz': attempt.quiz, 'questions': questions,
        'remaining': attempt.remaining_seconds(),
    })


@login_required
def attempt_result(request, pk):
    attempt = get_object_or_404(Attempt.objects.select_related('quiz'), pk=pk, user=request.user)
    if not attempt.is_finished:
        return redirect('attempt_take', pk=attempt.pk)

    answers = {a.question_id: a for a in attempt.answers.all()}
    review = []
    for question in attempt.quiz.questions.prefetch_related('choices'):
        answer = answers.get(question.pk)
        review.append({
            'question': question,
            'choices': question.choices.all(),
            'selected_id': answer.choice_id if answer else None,
            'is_correct': answer.is_correct if answer else False,
        })
    return render(request, 'quiz/attempt_result.html', {
        'attempt': attempt, 'quiz': attempt.quiz, 'review': review,
        'wrong': attempt.total - attempt.score,
    })


@login_required
def attempt_history(request):
    attempts = Attempt.objects.filter(user=request.user, finished_at__isnull=False).select_related('quiz')
    page_obj = Paginator(attempts, 10).get_page(request.GET.get('page'))
    return render(request, 'quiz/attempt_history.html', {'page_obj': page_obj, 'querystring': ''})


# --------------------------------------------------------- leaderboard
@login_required
def leaderboard(request):
    quizzes = list(published_quizzes())
    selected = None
    quiz_id = request.GET.get('quiz', '')
    if quiz_id.isdigit():
        selected = next((q for q in quizzes if q.pk == int(quiz_id)), None)
    if selected is None and quizzes:
        selected = quizzes[0]

    rows = []
    if selected:
        attempts = (Attempt.objects.filter(quiz=selected, finished_at__isnull=False)
                    .select_related('user', 'quiz'))
        ranked = sorted(attempts, key=lambda a: (-a.percentage, a.duration_seconds))
        seen = set()
        for attempt in ranked:          # keep only each user's best attempt
            if attempt.user_id in seen:
                continue
            seen.add(attempt.user_id)
            rows.append(attempt)
            if len(rows) == 10:
                break
    return render(request, 'quiz/leaderboard.html', {'quizzes': quizzes, 'selected': selected, 'rows': rows})
