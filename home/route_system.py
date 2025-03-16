from decimal import Decimal
from django.utils import timezone
from .models import *

def create_route_with_stops(route_number, route_name, stops_list):
    """
    Create a new bus route with multiple stops.
    
    Args:
        route_number (str): Route identifier
        route_name (str): Descriptive name of the route
        stops_list (list): List of stop names in order
        
    Returns:
        BusRoute: The newly created route
    """
    if len(stops_list) < 2:
        raise ValueError("A route must have at least 2 stops")
        
    # Create the route
    route = BusRoute.objects.create(
        route_number=route_number,
        route_name=route_name,
        start_point=stops_list[0],
        end_point=stops_list[-1]
    )
    
    # Create stops with sequence numbers
    stops = []
    for i, stop_name in enumerate(stops_list):
        stop = BusStop.objects.create(
            route=route,
            stop_name=stop_name,
            sequence_number=i
        )
        stops.append(stop)
    
    return route

def define_segment_fares(route, segment_fares):
    """
    Define fares for each segment of the route.
    
    Args:
        route (BusRoute): Route object
        segment_fares (list): List of dictionaries with segment fare info:
            [{'start': 'Stop A', 'end': 'Stop B', 'fare': 10.00, 'distance': 5.2}, ...]
    """
    for segment in segment_fares:
        try:
            start_stop = BusStop.objects.get(route=route, stop_name=segment['start'])
            end_stop = BusStop.objects.get(route=route, stop_name=segment['end'])
            
            # Ensure the stops are consecutive
            if end_stop.sequence_number != start_stop.sequence_number + 1:
                raise ValueError(f"Stops {segment['start']} and {segment['end']} are not consecutive")
                
            RouteSegment.objects.create(
                route=route,
                start_stop=start_stop,
                end_stop=end_stop,
                base_fare=Decimal(str(segment['fare'])),
                distance=Decimal(str(segment['distance']))
            )
        except BusStop.DoesNotExist:
            raise ValueError(f"One or both stops not found: {segment['start']} to {segment['end']}")

def apply_for_bus_pass(user, route, from_stop, to_stop, profession, valid_months=3, photo=None, id_proof=None):
    """
    Apply for a new bus pass.
    
    Args:
        user (CustomUser): User applying for pass
        route (BusRoute): Selected bus route
        from_stop (str): Starting stop name
        to_stop (str): Ending stop name
        profession (str): User profession (student, senior_citizen, etc.)
        valid_months (int): Number of months the pass is valid for
        photo, id_proof: Optional uploaded files
        
    Returns:
        BusPass: The newly created bus pass application
    """
    try:
        from_stop_obj = BusStop.objects.get(route=route, stop_name=from_stop)
        to_stop_obj = BusStop.objects.get(route=route, stop_name=to_stop)
        
        # Ensure from_stop comes before to_stop in the route
        if from_stop_obj.sequence_number >= to_stop_obj.sequence_number:
            raise ValueError("From stop must come before to stop in the route")
            
        # Calculate validity period
        today = timezone.now().date()
        valid_until = today.replace(month=today.month + valid_months)
        if valid_until.month > 12:
            valid_until = valid_until.replace(year=valid_until.year + 1, month=valid_until.month - 12)
        
        # Create the pass
        bus_pass = BusPass.objects.create(
            user=user,
            bus_route=route,
            from_stop=from_stop_obj,
            to_stop=to_stop_obj,
            profession=profession,
            valid_from=today,
            valid_until=valid_until,
            photo=photo,
            id_proof=id_proof
        )
        
        return bus_pass
        
    except BusStop.DoesNotExist:
        raise ValueError(f"One or both stops not found: {from_stop} to {to_stop}")

def approve_bus_pass(bus_pass_id, approved=True):
    """
    Approve or reject a bus pass application
    
    Args:
        bus_pass_id: ID of the bus pass to approve/reject
        approved (bool): True to approve, False to reject
    """
    try:
        bus_pass = BusPass.objects.get(id=bus_pass_id)
        
        if approved:
            bus_pass.approval_status = 'approved'
            bus_pass.date_approved = timezone.now()
        else:
            bus_pass.approval_status = 'rejected'
            bus_pass.date_rejected = timezone.now()
            
        bus_pass.save()
        return bus_pass
        
    except BusPass.DoesNotExist:
        raise ValueError(f"Bus pass with ID {bus_pass_id} not found")