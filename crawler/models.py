# In crawler/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

def default_trial_end():
    return timezone.now() + timedelta(days=settings.TRIAL_PERIOD_DAYS)

class UserSubscription(models.Model):
    user_id = models.IntegerField(unique=True)
    subscription_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=(
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('expired', 'Expired')
    ), default='trial')
    trial_end = models.DateTimeField(default=timezone.now() + timezone.timedelta(days=3))
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_valid(self):
        if self.status == 'active':
            return True
        if self.status == 'trial' and self.trial_end > timezone.now():
            return True
        return False
    
    class Meta:
        verbose_name = "User Subscription"
        verbose_name_plural = "User Subscriptions"