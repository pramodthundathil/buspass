from django.shortcuts import redirect
from django.contrib import messages


# def admin_only(views_func):
#     def wrapper_func(request,*args, **kwargs):
#         group = None
#         if request.user.is_authenticated:
#             if request.user.groups.all().exists():
#                 group = request.user.groups.all()[0].name
            
#             if group == "admin":
#                 return redirect("admin_index")
#             elif group == "user":
#                 return views_func(request, *args, **kwargs)
#             else:
#                 return views_func(request, *args, **kwargs)
#         else:
#             messages.error(request, "You are not Logged in")
#             return redirect("signin")
            
#     return wrapper_func


def admin_only(views_func):
    def wrapper_func(request,*args, **kwargs):
        group = None
        if request.user.is_authenticated:
            if request.user.role == "admin":
                return redirect("admin_index")
            
            elif request.user.role == "user":
                return views_func(request, *args, **kwargs)
            
            elif request.user.role == "conductor":
                return redirect("conductor_index")
            
            else:
                return views_func(request, *args, **kwargs)
        else:
            return views_func(request, *args, **kwargs)
        
    return wrapper_func
