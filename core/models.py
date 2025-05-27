from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver

# South African Banks and their branch codes
BANK_CHOICES = [
    ('ABSA', 'ABSA Bank'),
    ('CAPITEC', 'Capitec Bank'),
    ('FNB', 'First National Bank'),
    ('INVESTEC', 'Investec Bank'),
    ('NEDBANK', 'Nedbank'),
    ('STANDARD', 'Standard Bank'),
    ('AFRICAN', 'African Bank'),
    ('BIDVEST', 'Bidvest Bank'),
    ('DISCOVERY', 'Discovery Bank'),
    ('GRINDROD', 'Grindrod Bank'),
    ('HSBC', 'HSBC Bank'),
    ('MERCANTILE', 'Mercantile Bank'),
    ('SAHL', 'South African Home Loans'),
    ('TYM', 'TymeBank'),
    ('UBS', 'UBS Bank'),
]

# Custom user model extending AbstractUser
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    auto_reinvest = models.BooleanField(default=False)
    total_invested = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    level = models.IntegerField(default=1)
    last_ip = models.GenericIPAddressField(null=True, blank=True)  # Last known IP address
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def update_level(self):
        """Update user level based on total investment"""
        if self.total_invested >= Decimal('20000'):
            self.level = 3
        elif self.total_invested >= Decimal('10000'):
            self.level = 2
        else:
            self.level = 1
        self.save()

    def get_next_level_threshold(self):
        """Get the amount needed to reach next level"""
        if self.level == 1:
            return Decimal('10000') - self.total_invested
        elif self.level == 2:
            return Decimal('20000') - self.total_invested
        return Decimal('0')

    def get_available_tiers(self):
        """Get tiers available for user's level"""
        if self.level == 1:
            return [50, 100, 250, 500, 1000]
        elif self.level == 2:
            return [2000, 5000, 7500, 10000]
        else:
            return [20000, 50000]

# Investment tier model (e.g. R50, R200, etc.)
class InvestmentTier(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    return_amount = models.DecimalField(max_digits=12, decimal_places=2)
    duration_days = models.IntegerField()
    min_level = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    logo = models.ImageField(upload_to='tier_logos/', null=True, blank=True)  # Logo for the tier
    description = models.TextField(blank=True)  # Description of the tier

    def __str__(self):
        return f"{self.name} - R{self.amount}"

# Investment model
class Investment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    tier = models.ForeignKey(InvestmentTier, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    return_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    expires_at = models.DateTimeField(default=timezone.now)  # Added default value
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Update user's total_invested when creating new investment
        if not self.pk:  # Only on creation
            self.user.total_invested += self.amount
            self.user.update_level()
        super().save(*args, **kwargs)

# Deposit model
class Deposit(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    PAYMENT_METHODS = [
        ('eft', 'EFT'),
        ('cash', 'Cash Deposit'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    proof_image = models.ImageField(upload_to='deposit_proofs/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True)  # Admin notes for approval/rejection

    def __str__(self):
        return f"{self.user.username} - R{self.amount} ({self.status})"

# Withdrawal model
class Withdrawal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    PAYMENT_METHODS = [
        ('bank', 'Bank Transfer'),
        ('cash', 'Cash Withdrawal'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    # Bank details fields
    account_holder_name = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, choices=BANK_CHOICES, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    branch_code = models.CharField(max_length=20, blank=True)
    account_type = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True)  # Admin notes for approval/rejection

    def __str__(self):
        return f"{self.user.username} - R{self.amount} ({self.status})"

    def save(self, *args, **kwargs):
        # Get the old instance if this is an update
        if self.pk:
            try:
                old_instance = Withdrawal.objects.get(pk=self.pk)
                # If status is changing to approved
                if old_instance.status != 'approved' and self.status == 'approved':
                    # Get the user's wallet
                    wallet = self.user.wallet
                    if wallet.balance >= self.amount:
                        wallet.balance -= self.amount
                        wallet.save()
                    else:
                        raise ValueError("Insufficient balance for withdrawal")
            except Withdrawal.DoesNotExist:
                pass
        super().save(*args, **kwargs)

# Wallet model (one per user)
class Wallet(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# Referral model
class Referral(models.Model):
    inviter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='referrals_made')
    invitee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='referrals_received')
    bonus_amount = models.DecimalField(max_digits=12, decimal_places=2, default=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# IP Address log for R50 limit enforcement
class IPAddress(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)  # User associated with IP
    ip_address = models.GenericIPAddressField()  # IP address
    tier = models.ForeignKey('InvestmentTier', on_delete=models.CASCADE)  # Tier (for R50 enforcement)
    created_at = models.DateTimeField(auto_now_add=True)  # When logged

class ReferralReward(models.Model):
    """Model to track referral rewards for successful deposits"""
    referrer = models.ForeignKey(CustomUser, related_name='rewards', on_delete=models.CASCADE)
    referred = models.ForeignKey(CustomUser, related_name='referred_rewards', on_delete=models.CASCADE)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=10)
    awarded_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

    class Meta:
        unique_together = ('referrer', 'referred')
        ordering = ['-awarded_at']

    def __str__(self):
        return f"R{self.reward_amount} reward for {self.referrer.username} from {self.referred.username}"

    def save(self, *args, **kwargs):
        if not self.is_paid:
            # Credit the referrer's wallet
            wallet = self.referrer.wallet
            wallet.balance += self.reward_amount
            wallet.save()
            self.is_paid = True
        super().save(*args, **kwargs)

# Update User model to include referral tracking
CustomUser.add_to_class('referred_by', models.ForeignKey(
    'self',
    null=True,
    blank=True,
    on_delete=models.SET_NULL,
    related_name='referred_users'
))

# Signal to create ReferralReward when a deposit is approved
@receiver(post_save, sender=Deposit)
def create_referral_reward(sender, instance, created, **kwargs):
    if instance.status == 'approved' and instance.amount >= Decimal('50.00'):
        user = instance.user
        if user.referred_by and not ReferralReward.objects.filter(referrer=user.referred_by, referred=user).exists():
            ReferralReward.objects.create(
                referrer=user.referred_by,
                referred=user,
                deposit_amount=instance.amount
            )

class DailySpecial(models.Model):
    tier = models.ForeignKey(InvestmentTier, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    special_return_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)  # e.g., 1.5 for 50% extra returns
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tier.name} Special ({self.start_time.date()})"

    @property
    def special_return_amount(self):
        """Calculate the special return amount based on the multiplier"""
        return self.tier.return_amount * self.special_return_multiplier

    @property
    def is_currently_active(self):
        """Check if the special is currently active"""
        now = timezone.now()
        return self.is_active and self.start_time <= now <= self.end_time

    class Meta:
        ordering = ['-start_time']
