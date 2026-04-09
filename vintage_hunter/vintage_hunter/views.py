from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth import login, logout

from .forms import SignInForm, SignUpForm


@require_http_methods(['GET', 'POST'])
def signin(request):
    if request.method == 'POST':
        form = SignInForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            if not form.cleaned_data.get('remember'):
                request.session.set_expiry(0)
                
            return redirect('catalog:get_list')
    else:
        form = SignInForm()
    
    return render(request, 'signin.html', {
        'form': form
        })

@require_http_methods(['GET', 'POST'])
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('catalog:get_list') 
    else:
        form = SignUpForm()
        return render(request, 'signup.html', {
            'form': form
        })

@require_http_methods(['GET', 'POST'])
def password_reset(request):
     return render(request, 'password_reset.html', {})

@require_POST
def signout(requset):
    logout(requset)
    return redirect('catalog:get_list')
