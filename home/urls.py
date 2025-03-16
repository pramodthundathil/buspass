from django.urls import path
from . import views
from django.contrib.auth.decorators import user_passes_test



urlpatterns = [
    path('', views.index, name='index'),
    path('admin_index/', views.admin_index, name='admin_index'),
    path('conductor/', views.conductor_index, name='conductor_index'),
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('signout/', views.signout, name='signout'),
    path("buss_pass",views.buss_pass,name="buss_pass"),
    path("buspass_application",views.buspass_application,name="buspass_application"),
    path("approved_buss_pass",views.approved_buss_pass,name="approved_buss_pass"),

    path('application_single/<int:pk>/', views.application_single, name='application_single'),


    path('routes/', views.route_list, name='route_list'),
    path('routes/<int:route_id>/', views.route_detail, name='route_detail'),
    path('routes/create/', views.create_route, name='create_route'),
    path('routes/<int:route_id>/edit/', views.edit_route, name='edit_route'),
    path('buspass/apply/', views.buspass_apply, name='buspass_apply'),
    path('buspass/status/', views.buspass_status, name='buspass_status'),
    path('buspass/<int:pass_id>/', views.buspass_detail, name='buspass_detail'),
    path('admin_pending_passes/', views.admin_pending_passes, name='admin_pending_passes'),
    path('admin_approved_passes/', views.admin_approved_passes, name='admin_approved_passes'),
    path('admin_approve_pass/<int:pass_id>/', views.admin_approve_pass, name='admin_approve_pass'),
    # path('ajax/get_route_stops/', views.get_route_stops, name='get_route_stops'),
    path('view_application/<int:pk>/', views.view_application, name='view_application'),
    path('api/route/<int:route_id>/stops/', views.get_route_stops, name='get_route_stops'),
    path('ajax/calculate_fare/', views.calculate_fare, name='calculate_fare'),


    path('routes/<int:route_id>/delete/', views.delete_route, name='delete_route'),


    path("bus_routes",views.bus_routes,name="bus_routes"),
    path('routes/<int:route_id>/user', views.route_detail_user, name='route_detail_user'),

    
    path('Payment_screen/<int:pk>/', views.Payment_screen, name='Payment_screen'),
    path('callback', views.callback, name='callback'),
    path("buspassgenerate/<int:pk>",views.buspassgenerate,name="buspassgenerate")
    
   

]