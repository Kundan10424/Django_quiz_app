from django.core.management.base import BaseCommand
from django.db import transaction

from quiz.models import Category, Choice, Question, Quiz

# (question, [choices], index_of_correct_choice, explanation)
DATA = [
    {
        'category': 'Python', 'title': 'Python Basics',
        'description': 'Test your knowledge of Python fundamentals: data types, loops and functions.',
        'time': 5, 'pass': 60,
        'questions': [
            ('Which keyword is used to define a function in Python?', ['func', 'def', 'function', 'define'], 1, 'Functions start with the def keyword.'),
            ('What is the output of len([1, 2, 3, 4])?', ['3', '4', '5', 'Error'], 1, 'The list has 4 items.'),
            ('Which data type is immutable?', ['list', 'dict', 'tuple', 'set'], 2, 'Tuples cannot be changed after creation.'),
            ('Which symbol starts a single-line comment?', ['//', '#', '--', '/*'], 1, 'Python comments start with #.'),
            ('What does range(3) produce?', ['1, 2, 3', '0, 1, 2', '0, 1, 2, 3', '1, 2'], 1, 'range(3) gives 0, 1, 2.'),
        ],
    },
    {
        'category': 'Web', 'title': 'HTML & CSS Essentials',
        'description': 'Check how well you know the building blocks of web pages.',
        'time': 5, 'pass': 60,
        'questions': [
            ('Which HTML tag creates a hyperlink?', ['<link>', '<a>', '<href>', '<url>'], 1, 'The anchor tag <a> creates links.'),
            ('Which CSS property changes the text colour?', ['font-color', 'text-color', 'color', 'foreground'], 2, 'Use the color property.'),
            ('Which CSS property controls the space INSIDE an element border?', ['margin', 'padding', 'spacing', 'gap'], 1, 'Padding is inside the border; margin is outside.'),
            ('Which value makes an element a flex container?', ['display: flex', 'flex: on', 'position: flex', 'layout: flex'], 0, 'Set display: flex on the parent.'),
            ('Which tag holds the main heading of a page?', ['<head>', '<h1>', '<header1>', '<title>'], 1, '<h1> is the top-level heading.'),
        ],
    },
    {
        'category': 'Python', 'title': 'Django Fundamentals',
        'description': 'Models, views, templates and URLs - the core of every Django project.',
        'time': 6, 'pass': 60,
        'questions': [
            ('Which command creates a new Django project?', ['django-admin startproject', 'python manage.py newproject', 'django new', 'pip startproject'], 0, 'Use django-admin startproject <name>.'),
            ('Which file maps URLs to views?', ['models.py', 'urls.py', 'admin.py', 'forms.py'], 1, 'urls.py holds URL patterns.'),
            ('Which command applies migrations to the database?', ['makemigrations', 'migrate', 'syncdb', 'runmigrations'], 1, 'migrate applies them; makemigrations only creates them.'),
            ('Which template tag protects forms against CSRF attacks?', ['{% secure %}', '{% csrf_token %}', '{% token %}', '{% protect %}'], 1, 'Add {% csrf_token %} inside every POST form.'),
            ('Where do you register models for the admin site?', ['views.py', 'settings.py', 'admin.py', 'apps.py'], 2, 'Use admin.site.register or @admin.register in admin.py.'),
        ],
    },
]


class Command(BaseCommand):
    help = 'Load sample categories, quizzes, questions and choices (safe to run more than once).'

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        for item in DATA:
            category, _ = Category.objects.get_or_create(name=item['category'])
            quiz, was_created = Quiz.objects.get_or_create(
                title=item['title'],
                defaults={'description': item['description'], 'category': category,
                          'time_limit_minutes': item['time'], 'pass_percentage': item['pass']})
            if not was_created:
                continue
            created += 1
            for order, (text, choices, correct, explanation) in enumerate(item['questions'], start=1):
                question = Question.objects.create(quiz=quiz, text=text, explanation=explanation, order=order)
                for index, choice_text in enumerate(choices):
                    Choice.objects.create(question=question, text=choice_text, is_correct=(index == correct))
        self.stdout.write(self.style.SUCCESS(f'Done. {created} new quiz(zes) added.'))
