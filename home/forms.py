from django.contrib.auth.models import User 
from django.contrib.auth.forms import UserCreationForm , UserChangeForm
from .models import CustomUser
from django import forms


class UserAddForm(UserCreationForm):
    class Meta:
        model = CustomUser 
        # fields = "__all__"
        fields = ["username","phone","pro_pic","address","email","first_name","last_name","password1","password2"]


        widgets = {
            "username":forms.TextInput(attrs={"class":"form-control", "placeholder":"Username"}),
            "phone":forms.NumberInput(attrs={"class":"form-control","placeholder":"Phone Number"}),
            "pro_pic":forms.FileInput(attrs={"class":"form-control"}),
            "address":forms.Textarea(attrs={"class":"form-control"}),
            "email":forms.EmailInput(attrs={"class":"form-control","placeholder":"Email"}),
            "first_name":forms.TextInput(attrs={"class":"form-control", "placeholder":"First Name"}),
            "last_name":forms.TextInput(attrs={"class":"form-control", "placeholder":"Last Name"}),
        
        }

    def __init__(self, *args, **kwargs):
        super(UserAddForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class': 'form-control  py-3', 'placeholder': 'Password'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class': 'form-control  py-3', 'placeholder': 'Password confirmation'})


class UserUpdateForm(UserChangeForm):
    class Meta:
        model = CustomUser 
        # fields = "__all__"
        fields = ["username","phone","pro_pic","address","email","first_name","last_name","password"]


        widgets = {
            "username":forms.TextInput(attrs={"class":"form-control", "placeholder":"Username"}),
            "phone":forms.NumberInput(attrs={"class":"form-control","placeholder":"Phone Number"}),
            "pro_pic":forms.ClearableFileInput(attrs={"class":"form-control"}),
            "address":forms.Textarea(attrs={"class":"form-control"}),
            "email":forms.EmailInput(attrs={"class":"form-control","placeholder":"Email"}),
            "first_name":forms.TextInput(attrs={"class":"form-control", "placeholder":"First Name"}),
            "last_name":forms.TextInput(attrs={"class":"form-control", "placeholder":"Last Name"}),
        
        }

    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.fields['password'].widget = forms.PasswordInput(attrs={'class': 'form-control  py-3', 'placeholder': 'Password'})
       


from django import forms
from django.forms import modelformset_factory, inlineformset_factory
from .models import BusRoute, BusStop, RouteSegment, BusPass
from django import forms
from .models import BusRoute, BusStop, RouteSegment, BusPass

class RouteForm(forms.ModelForm):
    class Meta:
        model = BusRoute
        fields = ['route_number', 'route_name', 'start_point', 'end_point']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        route_number = cleaned_data.get('route_number')
        
        # Check if route_number already exists
        if BusRoute.objects.filter(route_number=route_number).exists():
            if not self.instance.pk or self.instance.route_number != route_number:
                self.add_error('route_number', 'Route number already exists')
                
        return cleaned_data


class BusStopForm(forms.ModelForm):
    class Meta:
        model = BusStop
        fields = ['stop_name', 'sequence_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class RouteSegmentForm(forms.ModelForm):
    class Meta:
        model = RouteSegment
        fields = ['start_stop', 'end_stop', 'base_fare', 'distance']

    def __init__(self, *args, **kwargs):
        route = kwargs.pop('route', None)
        super().__init__(*args, **kwargs)
        
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Filter stops to only show those from the current route
        if route:
            self.fields['start_stop'].queryset = BusStop.objects.filter(route=route)
            self.fields['end_stop'].queryset = BusStop.objects.filter(route=route)

    def clean(self):
        cleaned_data = super().clean()
        start_stop = cleaned_data.get('start_stop')
        end_stop = cleaned_data.get('end_stop')

        if start_stop and end_stop:
            # Ensure the stops are for the same route
            if start_stop.route != end_stop.route:
                self.add_error('end_stop', 'Both stops must belong to the same route')

            # Ensure end stop immediately follows start stop
            if end_stop.sequence_number != start_stop.sequence_number + 1:
                self.add_error('end_stop', 'End stop must immediately follow the start stop')

        return cleaned_data
    

# Create formsets for managing multiple stops and segments
BusStopFormSet = forms.modelformset_factory(
    BusStop, 
    form=BusStopForm,
    extra=3,
    can_delete=True
)

RouteSegmentFormSet = forms.modelformset_factory(
    RouteSegment,
    form=RouteSegmentForm,
    extra=2,
    can_delete=True
)


class BusPassApplicationForm(forms.ModelForm):
    class Meta:
        model = BusPass
        fields = [
            'bus_route', 'from_stop', 'to_stop',"pass_validity_in_days", 
            'profession', 'photo', 'id_proof'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

        # Limit stop choices initially
        self.fields['from_stop'].queryset = BusStop.objects.none()
        self.fields['to_stop'].queryset = BusStop.objects.none()

        # If route is selected and form is bound, populate stops
        if 'bus_route' in self.data:
            try:
                route_id = int(self.data.get('bus_route'))
                self.fields['from_stop'].queryset = BusStop.objects.filter(
                    route_id=route_id
                ).order_by('sequence_number')
                self.fields['to_stop'].queryset = BusStop.objects.filter(
                    route_id=route_id
                ).order_by('sequence_number')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['from_stop'].queryset = BusStop.objects.filter(
                route=self.instance.bus_route
            ).order_by('sequence_number')
            self.fields['to_stop'].queryset = BusStop.objects.filter(
                route=self.instance.bus_route
            ).order_by('sequence_number')

    def clean(self):
        cleaned_data = super().clean()
        from_stop = cleaned_data.get('from_stop')
        to_stop = cleaned_data.get('to_stop')

        if from_stop and to_stop:
            # Ensure from_stop comes before to_stop
            if from_stop.sequence_number >= to_stop.sequence_number:
                self.add_error('to_stop', 'To stop must come after from stop')

        return cleaned_data
