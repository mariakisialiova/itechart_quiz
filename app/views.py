from django import forms
from django.forms import inlineformset_factory
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from .models import QuizProfile, Question, AttemptedQuestion, Choice, Category
from .forms import UserLoginForm, RegistrationForm, AddQuestionForm, QuestionForm, ChoiceInlineFormset


def home(request):
    context = {}
    return render(request, 'quiz/home.html', context=context)


@login_required()
def user_home(request):
    context = {}
    return render(request, 'quiz/user_home.html', context=context)


def leaderboard(request):

    top_quiz_profiles = QuizProfile.objects.order_by('-total_score')[:500]
    total_count = top_quiz_profiles.count()
    context = {
        'top_quiz_profiles': top_quiz_profiles,
        'total_count': total_count,
    }
    return render(request, 'quiz/leaderboard.html', context=context)


@login_required()
def play(request):
    quiz_profile, created = QuizProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        question_pk = request.POST.get('question_pk')

        attempted_question = quiz_profile.attempts.select_related('question').get(question__pk=question_pk)

        choice_pk = request.POST.get('choice_pk')

        try:
            selected_choice = attempted_question.question.choices.get(pk=choice_pk)
        except ObjectDoesNotExist:
            raise Http404

        quiz_profile.evaluate_attempt(attempted_question, selected_choice)

        return redirect(attempted_question)

    else:
        question = quiz_profile.get_new_question()
        if question is not None:
            quiz_profile.create_attempt(question)

        context = {
            'question': question,
        }

        return render(request, 'quiz/play.html', context=context)


@login_required()
def submission_result(request, attempted_question_pk):
    attempted_question = get_object_or_404(AttemptedQuestion, pk=attempted_question_pk)
    context = {
        'attempted_question': attempted_question,
    }

    return render(request, 'quiz/submission_result.html', context=context)


def login_view(request):
    title = "Login"
    form = UserLoginForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(username=username, password=password)
        login(request, user)
        return redirect('/user-home')
    return render(request, 'quiz/login.html', {"form": form, "title": title})


def register(request):
    title = "Create account"
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/login')
    else:
        form = RegistrationForm()

    context = {'form': form, 'title': title}
    return render(request, 'quiz/registration.html', context=context)


def logout_view(request):
    logout(request)
    return redirect('/')


def error_404(request):
    data = {}
    return render(request, 'quiz/error_404.html', data)


def error_500(request):
    data = {}
    return render(request, 'quiz/error_500.html', data)


def add_question(request):
    if request.user.is_staff:
        ChoicesFormset = inlineformset_factory(
            Question,
            Choice,
            fields=('html', 'is_correct'),
            formset=ChoiceInlineFormset,
            can_delete=False,
            widgets={
                'html': forms.Textarea(attrs={'rows': 2, 'cols': 80}),
            },
            extra=4,
        )

        if request.method == 'POST':
            form = QuestionForm(request.POST)
            formset = ChoicesFormset(request.POST)
            if formset.is_valid() and form.is_valid():
                question = form.save()
                answers = formset.save(commit=False)
                for answer in answers:
                    answer.question = question
                    answer.save()
                return redirect('/')
            else:
                context = {'formset': formset, 'form': form}
                return render(request, 'quiz/add_question.html', context)
        formset = ChoicesFormset()
        form = QuestionForm()
        context = {'formset': formset, 'form': form}
        return render(request, 'quiz/add_question.html', context)
    else:
        return redirect('home')


def categories(request):

    categories = Category.objects.all()
    return render(request, 'quiz/categories.html', {'categories': categories})
