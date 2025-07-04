from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect


def home(request):
    """Home page redirects to films catalog"""
    return redirect('films:catalog')


@csrf_protect
@require_http_methods(["POST"])
def custom_logout(request):
    """Custom logout view that redirects to the referring page"""
    # Get the referring page, defaulting to home if not available
    next_page = request.META.get('HTTP_REFERER', '/')
    
    # Clean up the next_page to ensure it's a relative URL for security
    if next_page and next_page.startswith(request.build_absolute_uri('/')):
        # Make it relative by removing the domain part
        next_page = '/' + next_page.split('/', 3)[-1] if '/' in next_page[8:] else '/'
    else:
        next_page = '/'
    
    # Perform logout
    logout(request)
    
    # Redirect to the referring page
    return redirect(next_page)
