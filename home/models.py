from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("The username field to be set")
        username = self.normalize_email(username)
        user = self.model(username = username, **extra_fields)
        user.set_password(password)
        user.save(using = self._db)
        return user 
    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser',True)
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have superuser status is True ')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have staff status is True ')
        
        return self.create_user(username, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True, verbose_name='username')
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=200, blank=True, null=True)
    last_name = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    pro_pic = models.FileField(upload_to="profile_pic", null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="active")
    is_staff = models.BooleanField(default=False, verbose_name="staff")
    date_joined = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=20, choices=(("user","user"),('admin',"admin"),("conductor","conductor")), default='user')

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ["first_name","email"]


    class Meta:
        verbose_name='user'
        verbose_name_plural = "users"




from django.db import models
from decimal import Decimal

class BusRoute(models.Model):
    route_name = models.CharField(max_length=100, unique=True)
    start_point = models.CharField(max_length=100)
    end_point = models.CharField(max_length=100)
    route_number = models.CharField(max_length=10, unique=True)
    
    class Meta:
        verbose_name = 'bus route'
        verbose_name_plural = 'bus routes'

    def __str__(self):
        return f"{self.route_number} - {self.route_name}"
    
    def get_all_stops(self):
        """Return all stops in order for this route"""
        return [stop.stop_name for stop in self.busstop_set.all().order_by('sequence_number')]
    
    def calculate_fare(self, from_stop, to_stop, is_student=False, profession=None):
        """Calculate fare between two stops on this route"""
        try:
            # Get stop sequence numbers
            from_stop_obj = self.busstop_set.get(stop_name=from_stop)
            to_stop_obj = self.busstop_set.get(stop_name=to_stop)
            
            # Find all segments between these stops
            segments = self.routesegment_set.filter(
                start_stop__sequence_number__gte=from_stop_obj.sequence_number,
                end_stop__sequence_number__lte=to_stop_obj.sequence_number
            )
            
            # Sum up the segment fares
            total_fare = sum(segment.base_fare for segment in segments)
            
            # Apply discount based on user type
            if is_student:
                total_fare = total_fare * Decimal('0.5')  # 50% discount for students
            elif profession == 'senior_citizen':
                total_fare = total_fare * Decimal('0.7')  # 30% discount for senior citizens
            
            return total_fare
            
        except (self.busstop_set.model.DoesNotExist, self.routesegment_set.model.DoesNotExist):
            return None


class BusStop(models.Model):
    route = models.ForeignKey(BusRoute, on_delete=models.CASCADE)
    stop_name = models.CharField(max_length=100)
    sequence_number = models.PositiveIntegerField()
    
    class Meta:
        verbose_name = 'bus stop'
        verbose_name_plural = 'bus stops'
        unique_together = ('route', 'sequence_number')
        ordering = ['route', 'sequence_number']
    
    def __str__(self):
        return f"{self.route.route_number} - {self.stop_name} (Stop {self.sequence_number})"


class RouteSegment(models.Model):
    route = models.ForeignKey(BusRoute, on_delete=models.CASCADE)
    start_stop = models.ForeignKey(BusStop, on_delete=models.CASCADE, related_name='starting_segments')
    end_stop = models.ForeignKey(BusStop, on_delete=models.CASCADE, related_name='ending_segments')
    base_fare = models.DecimalField(max_digits=10, decimal_places=2)
    distance = models.DecimalField(max_digits=10, decimal_places=2, help_text="Distance in kilometers")
    
    class Meta:
        verbose_name = 'route segment'
        verbose_name_plural = 'route segments'
    
    def __str__(self):
        return f"{self.route.route_number}: {self.start_stop.stop_name} to {self.end_stop.stop_name}"
    
    def save(self, *args, **kwargs):
        # Ensure the segment is between consecutive stops
        if self.end_stop.sequence_number != self.start_stop.sequence_number + 1:
            raise ValueError("Segments can only be created between consecutive stops")
        super().save(*args, **kwargs)

from django.utils import timezone
from datetime import timedelta

class BusPass(models.Model):
    PROFESSION_CHOICES = (
        ('student', 'Student'),
        ('senior_citizen', 'Senior Citizen'),
        ('general', 'General'),
        ('government_employee', 'Government Employee'),
    )
    
    APPROVAL_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='buspasses')
    photo = models.ImageField(upload_to='buspass_photos/', null=True, blank=True)
    id_proof = models.FileField(upload_to='id_proofs/', null=True, blank=True)
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default="pending")
    status = models.BooleanField(default=False)
    date_applied = models.DateTimeField(auto_now_add=True)
    date_approved = models.DateTimeField(null=True, blank=True)
    date_rejected = models.DateTimeField(null=True, blank=True)
    profession = models.CharField(max_length=100, choices=PROFESSION_CHOICES, default='general')
    bus_route = models.ForeignKey(BusRoute, on_delete=models.CASCADE, related_name='passes')
    from_stop = models.ForeignKey(BusStop, on_delete=models.CASCADE, related_name='passes_from')
    to_stop = models.ForeignKey(BusStop, on_delete=models.CASCADE, related_name='passes_to')
    valid_from = models.DateField()
    valid_until = models.DateField()
    payment_status = models.BooleanField(default=False)
    pass_validity_in_days = models.BigIntegerField(default=30) 
    payment_order_id = models.CharField(max_length=100,null=True, blank=True)
    pass_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    
    class Meta:
        verbose_name = 'bus pass'
        verbose_name_plural = 'bus passes'
    
    def __str__(self):
        return f"{self.user.username} - {self.bus_route.route_number} ({self.from_stop.stop_name} to {self.to_stop.stop_name})"
    
    def save(self, *args, **kwargs):
        # Calculate fare if not already set
        if not self.pass_fare:
            is_student = self.profession == 'student'
            single_fare = self.bus_route.calculate_fare(
                self.from_stop.stop_name, 
                self.to_stop.stop_name,
                is_student=is_student,
                profession=self.profession
            )
            # Ensure proper Decimal conversion and multiplication
            self.pass_fare = Decimal(single_fare) * Decimal(self.pass_validity_in_days)

        if not self.valid_from:
            self.valid_from = timezone.now().date()

        self.valid_until = self.valid_from + timedelta(days=self.pass_validity_in_days)
        super().save(*args, **kwargs)