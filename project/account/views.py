from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseBadRequest
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User

from .forms import RegisterForm, ProfileUpdateForm
from .models import Profile
from .utils import send_confirmation_mail


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_confirmation_mail(request, user, user.email, "confirm_registration")
            return redirect("shop:home")
    else:
        form = RegisterForm()
    return render(request, "account/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get("next")
            return redirect(next_url or "shop:home")
        else:
            return render(
                request, "account/login.html", {"error": "incorrect login or password"}
            )
    else:
        return render(request, "account/login.html")


def logout_view(request):
    logout(request)
    return redirect("shop:home")


@login_required
def profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, "account/profile.html", {"profile": profile})


@login_required
def edit_profile_view(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            new_email = form.cleaned_data.get("email")
            if new_email != user.email:
                send_confirmation_mail(request, user, new_email, "confirm_email")

            avatar = form.cleaned_data.get("avatar")
            if avatar:
                profile.avatar = avatar
            profile.save()
            return redirect("account:profile")
    else:
        form = ProfileUpdateForm(user=user)

    return render(request, "account/edit_profile.html", {"form": form})


def confirm_email(request):
    user_id = request.GET.get("user")
    email = request.GET.get("email")

    if not user_id or email:
        return HttpResponseBadRequest("Bad request: no user or email")
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return HttpResponseBadRequest("User not found")
    if User.objects.filter(email=email).exists():
        return HttpResponseBadRequest("This email already taken")
    user.email = email
    user.save()
    return render(request, "account/confirm_email.html", {"new_email": email})


def confirm_registration(request):
    user_id = request.GET.get("user")
    email = request.GET.get("email")

    if not user_id or not email:
        return HttpResponseBadRequest("Bad request: No user or email")
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return HttpResponseBadRequest("Bad request: No user or email")

    login(request, user)
    return render(request, "account/confirm_email.html", {"email": email})
