from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from .forms import *
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .decorators import admin_only
from .models import *


# # Create your views here.
# def signin(request):
#     return HttpResponse("<h1>App Is Working</h1>")

@admin_only
def index(request):
    
    context = {
        
    }
    return render(request,"index.html",context)

@login_required(login_url='signin')
def admin_index(request):
    return render(request,"admin/index.html")

@login_required(login_url='signin')
def conductor_index(request):
    return render(request,"conductor/index.html")


def signin(request):
    if request.method == "POST":
        uname = request.POST.get('uname')
        pswd = request.POST.get('pswd')
        user = authenticate(request, username = uname, password = pswd)
        if user is not None:
            login(request, user)
            return redirect("index")
        else:
            messages.error(request,"Username or password incorrect")
            return redirect("signin")
        
    return render(request, 'login.html')


def signup(request):
    form = UserAddForm()
    if request.method == "POST":
        form = UserAddForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"User Registered Success....")
            return redirect("signin")
        else:
            messages.error(request,form.errors)
            return redirect("signup")
        
    context = {
        "form":form
    }
    return render(request,'register.html',context)


def signout(request):
    logout(request)
    return redirect(signin)


# buss pass functionalities 

@login_required(login_url='signin')
def buss_pass(request):
    buspasses = BusPass.objects.filter(user=request.user, status= False).order_by('-date_applied')
    return render(request,"buss_pass.html",{"buspasses":buspasses})


@login_required(login_url='signin')
def approved_buss_pass(request):
    
    buspasses = BusPass.objects.filter(user=request.user, status = True).order_by('-date_applied')
    return render(request,"approved_buss_pass.html",{"buspasses":buspasses})



@login_required(login_url='signin')
def application_single(request, pk):
    
    buspass = BusPass.objects.get(id = pk)
    return render(request,"application_single.html",{"buspass":buspass})


@login_required(login_url='signin')
def buspass_application(request):
    return render(request,"buspass_application.html")


import razorpay
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

razorpay_client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))


@csrf_exempt
def Payment_screen(request, pk):
    order_id = get_object_or_404(BusPass, id= pk)
    if request.method == "POST":
        data = {
                "amount": int(order_id.pass_fare * 100),
                "currency": "INR",
                "payment_capture": "1"
            }
        order = razorpay_client.order.create(data)
        order_id.payment_order_id = order["id"]
        order_id.save()

        return JsonResponse({"order_id": order["id"], "amount": order_id.pass_fare, "key": settings.RAZOR_KEY_ID})
    return render(request,"check_out.html",{"order":order_id, "items":get_object_or_404(BusPass, id= pk)})


@csrf_exempt
def callback(request):
    if request.method == "POST":
        response_data = request.POST
        order_id = response_data.get("razorpay_order_id")
        payment_id = response_data.get("razorpay_payment_id")
        signature = response_data.get("razorpay_signature")

        # Verify payment signature
        try:
            razorpay_client.utility.verify_payment_signature(response_data)
            print(order_id)
            order = get_object_or_404(BusPass, payment_order_id = order_id )
            order.payment_status = True 
            order.save()
            print("Working........")
            return JsonResponse({"status": "success"})
            # return render(request,"success.html")

        except:
            return JsonResponse({"status": "failed"})
            
            # return render(request,"error.html")
            
            # return JsonResponse({"status": "failed"})

    return JsonResponse({"status": "error"})
     




from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .models import BusRoute, BusStop, RouteSegment, BusPass
from .forms import BusPassApplicationForm, RouteForm, BusStopFormSet, RouteSegmentFormSet


# Route Management Views
@login_required(login_url='signin')
def route_list(request):
    """Display all available bus routes"""
    routes = BusRoute.objects.all()
    return render(request, 'admin/route_list.html', {'routes': routes})


@login_required(login_url='signin')
def route_detail(request, route_id):
    """Display details of a specific route with all stops and segments"""
    route = get_object_or_404(BusRoute, id=route_id)
    stops = BusStop.objects.filter(route=route).order_by('sequence_number')
    segments = RouteSegment.objects.filter(route=route).order_by('start_stop__sequence_number')
    
    return render(request, 'admin/route_detail.html', {
        'route': route,
        'stops': stops,
        'segments': segments
    })


@login_required(login_url='signin')
def create_route(request):
    """Create a new bus route with stops and fare segments"""
    if request.method == 'POST':
        form = RouteForm(request.POST)
        stop_formset = BusStopFormSet(request.POST, prefix='stops')
        segment_formset = RouteSegmentFormSet(request.POST, prefix='segments')
        
        if form.is_valid() and stop_formset.is_valid() and segment_formset.is_valid():
            # Save the route
            route = form.save()
            
            # Save stops
            stops = stop_formset.save(commit=False)
            for stop in stops:
                stop.route = route
                stop.save()
            
            # Save segments
            segments = segment_formset.save(commit=False)
            for segment in segments:
                segment.route = route
                segment.save()
            
            messages.success(request, f"Route {route.route_number} created successfully!")
            return redirect('route_detail', route_id=route.id)
    else:
        form = RouteForm()
        stop_formset = BusStopFormSet(prefix='stops')
        segment_formset = RouteSegmentFormSet(prefix='segments')
    
    return render(request, 'admin/create_route.html', {
        'form': form,
        'stop_formset': stop_formset,
        'segment_formset': segment_formset
    })


@login_required(login_url='signin')
def edit_route(request, route_id):
    """Edit an existing route with its stops and segments"""
    route = get_object_or_404(BusRoute, id=route_id)
    
    if request.method == 'POST':
        form = RouteForm(request.POST, instance=route)
        stop_formset = BusStopFormSet(request.POST, prefix='stops', queryset=BusStop.objects.filter(route=route))
        segment_formset = RouteSegmentFormSet(request.POST, prefix='segments', 
                                           queryset=RouteSegment.objects.filter(route=route))
        
        if form.is_valid() and stop_formset.is_valid() and segment_formset.is_valid():
            # Save the route first
            saved_route = form.save()
            
            # Save stops but don't commit to DB yet
            stops = stop_formset.save(commit=False)
            for stop in stops:
                stop.route = saved_route  # Assign the route to each stop
                stop.save()
            
            # Handle deleted stops
            for obj in stop_formset.deleted_objects:
                obj.delete()
            
            # Save segments but don't commit to DB yet
            segments = segment_formset.save(commit=False)
            for segment in segments:
                segment.route = saved_route  # Assign the route to each segment
                segment.save()
            
            # Handle deleted segments
            for obj in segment_formset.deleted_objects:
                obj.delete()
            
            messages.success(request, f"Route {route.route_number} updated successfully!")
            return redirect('route_detail', route_id=route.id)
    else:
        form = RouteForm(instance=route)
        stop_formset = BusStopFormSet(prefix='stops', queryset=BusStop.objects.filter(route=route))
        segment_formset = RouteSegmentFormSet(prefix='segments', 
                                           queryset=RouteSegment.objects.filter(route=route))
    
    return render(request, 'admin/edit_route.html', {
        'form': form,
        'stop_formset': stop_formset,
        'segment_formset': segment_formset,
        'route': route
    })


# Bus Pass Application Views
@login_required(login_url='signin')
def buspass_apply(request):
    """Apply for a new bus pass"""
    if request.method == 'POST':
        form = BusPassApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            bus_pass = form.save(commit=False)
            bus_pass.user = request.user
            
            # Calculate fare
            route = bus_pass.bus_route
            from_stop = bus_pass.from_stop
            to_stop = bus_pass.to_stop
            is_student = bus_pass.profession == 'student'
            
            # bus_pass.pass_fare = route.calculate_fare(
            #     from_stop.stop_name, 
            #     to_stop.stop_name,
            #     is_student=is_student,
            #     profession=bus_pass.profession
            # )
            
            # Set validity period (default 3 months)
            today = timezone.now().date()
            # valid_until = today.replace(month=today.month + 3)
            # if valid_until.month > 12:
            #     valid_until = valid_until.replace(year=valid_until.year + 1, month=valid_until.month - 12)
            
            bus_pass.valid_from = today
            # bus_pass.valid_until = valid_until
            # bus_pass.save()
            
            messages.success(request, "Bus pass application submitted successfully!")
            return redirect('Payment_screen', pk = bus_pass.id )
    else:
        form = BusPassApplicationForm()
    
    return render(request, 'buspass_apply.html', {'form': form})


@login_required(login_url='signin')
def buspass_status(request):
    """View status of user's bus pass applications"""
    passes = BusPass.objects.filter(user=request.user).order_by('-date_applied')
    return render(request, 'buspass/buspass_status.html', {'passes': passes})


@login_required(login_url='signin')
def buspass_detail(request, pass_id):
    """View details of a specific bus pass"""
    bus_pass = get_object_or_404(BusPass, id=pass_id, user=request.user)
    return render(request, 'buspass/buspass_detail.html', {'pass': bus_pass})


# Admin Views
@login_required(login_url='signin')
def admin_pending_passes(request):
    """Admin view to see all pending bus pass applications"""
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('home')
    
    pending_passes = BusPass.objects.filter(status=False).order_by('date_applied')
    return render(request, 'admin/admin_pending_passes.html', {'pending_passes': pending_passes})


@login_required(login_url='signin')
def admin_approved_passes(request):
    """Admin view to see all pending bus pass applications"""
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('home')
    
    pending_passes = BusPass.objects.filter(status=True).order_by('date_applied')
    return render(request, 'admin/buss_passes.html', {'pending_passes': pending_passes})


def view_application(request,pk):
    bus_pass = get_object_or_404(BusPass, id = pk)

    return render(request,"admin/view_application.html",{"original":bus_pass})



@login_required(login_url='signin')
def admin_approve_pass(request, pass_id):
    """Admin view to approve or reject a bus pass application"""
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('home')
    
    bus_pass = get_object_or_404(BusPass, id=pass_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            bus_pass.approval_status = 'approved'
            bus_pass.date_approved = timezone.now()
            bus_pass.status = True
            messages.success(request, f"Bus pass for {bus_pass.user.username} has been approved.")
        elif action == 'reject':
            bus_pass.approval_status = 'rejected'
            bus_pass.date_rejected = timezone.now()
            messages.success(request, f"Bus pass for {bus_pass.user.username} has been rejected.")
        
        bus_pass.save()
        return redirect('admin_pending_passes')
    
    return render(request, 'buspass/admin_approve_pass.html', {'pass': bus_pass})


# AJAX Views
# @require_http_methods(["GET"])
# def get_route_stops(request):
#     """AJAX view to get all stops for a selected route"""
#     route_id = request.GET.get('route_id')
    
#     if not route_id:
#         return JsonResponse({'error': 'Route ID is required'}, status=400)
    
#     try:
#         stops = BusStop.objects.filter(route_id=route_id).order_by('sequence_number')
#         stops_data = [{'id': stop.id, 'name': stop.stop_name} for stop in stops]
#         return JsonResponse({'stops': stops_data})
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)
    
    
def get_route_stops(request, route_id):
    try:
        bus_route = BusRoute.objects.get(id=route_id)
        stops = bus_route.busstop_set.order_by('sequence_number').values('id', 'stop_name')
        return JsonResponse(list(stops), safe=False)
    except BusRoute.DoesNotExist:
        return JsonResponse({'error': 'Route not found'}, status=404)


@require_http_methods(["GET"])
def calculate_fare(request):
    """AJAX view to calculate fare between two stops"""
    route_id = request.GET.get('route_id')
    from_stop_id = request.GET.get('from_stop_id')
    to_stop_id = request.GET.get('to_stop_id')
    profession = request.GET.get('profession', 'general')
    
    if not all([route_id, from_stop_id, to_stop_id]):
        return JsonResponse({'error': 'All parameters are required'}, status=400)
    
    try:
        route = get_object_or_404(BusRoute, id=route_id)
        from_stop = get_object_or_404(BusStop, id=from_stop_id)
        to_stop = get_object_or_404(BusStop, id=to_stop_id)
        
        # Ensure from_stop comes before to_stop
        if from_stop.sequence_number >= to_stop.sequence_number:
            return JsonResponse({'error': 'From stop must come before to stop'}, status=400)
        
        is_student = profession == 'student'
        fare = route.calculate_fare(
            from_stop.stop_name, 
            to_stop.stop_name,
            is_student=is_student,
            profession=profession
        )
        
        return JsonResponse({
            'fare': float(fare),
            'from_stop': from_stop.stop_name,
            'to_stop': to_stop.stop_name
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    



@login_required(login_url='signin')
def delete_route(request, route_id):
    """Delete an existing route"""
    route = get_object_or_404(BusRoute, id=route_id)
    
    
    route.delete()
    messages.success(request, f"Route {route.route_number} deleted successfully!")
    return redirect('route_list')

# @login_required(login_url='signin')
# def edit_route(request, route_id):
#     """Edit an existing route with its stops and segments"""
#     route = get_object_or_404(BusRoute, id=route_id)
    
#     if request.method == 'POST':
#         form = RouteForm(request.POST, instance=route)
#         stop_formset = BusStopFormSet(request.POST, prefix='stops', queryset=BusStop.objects.filter(route=route))
#         segment_formset = RouteSegmentFormSet(request.POST, prefix='segments', 
#                                             queryset=RouteSegment.objects.filter(route=route))
        
#         if form.is_valid() and stop_formset.is_valid() and segment_formset.is_valid():
#             form.save()
#             stop_formset.save()
#             segment_formset.save()
            
#             messages.success(request, f"Route {route.route_number} updated successfully!")
#             return redirect('route_detail', route_id=route.id)
#     else:
#         form = RouteForm(instance=route)
#         stop_formset = BusStopFormSet(prefix='stops', queryset=BusStop.objects.filter(route=route))
#         segment_formset = RouteSegmentFormSet(prefix='segments', 
#                                             queryset=RouteSegment.objects.filter(route=route))
    
#     return render(request, 'buspass/edit_route.html', {
#         'form': form,
#         'stop_formset': stop_formset,
#         'segment_formset': segment_formset,
#         'route': route
#     })



def bus_routes(request):

    routes = BusRoute.objects.all()
    context = {
        "routes":routes
    }
    return render(request,"bus_routes.html",context)


@login_required(login_url='signin')
def route_detail_user(request, route_id):
    """Display details of a specific route with all stops and segments"""
    route = get_object_or_404(BusRoute, id=route_id)
    stops = BusStop.objects.filter(route=route).order_by('sequence_number')
    segments = RouteSegment.objects.filter(route=route).order_by('start_stop__sequence_number')
    
    return render(request, 'route_single.html', {
        'route': route,
        'stops': stops,
        'segments': segments
    })



import qrcode
from io import BytesIO
import base64
from django.contrib.sites.shortcuts import get_current_site


def buspassgenerate(request, pk):
    # Get the user instance
    buspass =  get_object_or_404(BusPass, id = pk)
    
     # Generate the QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    current_site = get_current_site(request)
    domain = current_site.domain
    qr_data = f"{domain}/view_application/{buspass.id}"
    qr.add_data(qr_data)
    qr.make(fit=True)

    # Generate QR code image
    img = qr.make_image(fill='Green', back_color='white')

    # Save the QR code to a BytesIO object
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Encode the image to base64
    qr_code_image = base64.b64encode(buffer.read()).decode('utf-8')

    # Pass the encoded image to the template
    context = {
        'buspass': buspass,
        'qr_code_image': qr_code_image
    }

    return render(request, 'id_card.html', context)

