from django.contrib import admin
from .models import CustomUser, InvestmentTier, Investment, Wallet, Referral, IPAddress, ReferralReward, Withdrawal, Deposit
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone', 'level', 'total_invested', 'wallet_balance', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'level', 'date_joined')
    search_fields = ('username', 'email', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('email', 'phone', 'auto_reinvest')}),
        (_('Investment info'), {'fields': ('level', 'total_invested')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'password1', 'password2'),
        }),
    )

    def wallet_balance(self, obj):
        try:
            return f"R{obj.wallet.balance}"
        except:
            return "N/A"
    wallet_balance.short_description = 'Wallet Balance'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('wallet')

# Register CustomUser with enhanced admin
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(InvestmentTier)
admin.site.register(Investment)
admin.site.register(Wallet)
admin.site.register(Referral)
admin.site.register(IPAddress)

@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_method', 'status', 'created_at', 'view_proof', 'action_buttons')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'user__email', 'amount')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'amount', 'payment_method', 'status')
        }),
        ('Proof of Payment', {
            'fields': ('proof_image',),
            'description': 'Upload or view the proof of payment image'
        }),
        ('Additional Information', {
            'fields': ('admin_notes', 'created_at', 'updated_at')
        }),
    )

    def view_proof(self, obj):
        if obj.proof_image:
            return format_html('<a href="{}" target="_blank">View Proof</a>', obj.proof_image.url)
        return "No proof uploaded"
    view_proof.short_description = 'Proof of Payment'

    def action_buttons(self, obj):
        if obj.status == 'pending':
            approve_url = reverse('admin:approve_deposit', args=[obj.pk])
            reject_url = reverse('admin:reject_deposit', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">Approve</a>&nbsp;'
                '<a class="button" href="{}">Reject</a>',
                approve_url, reject_url
            )
        return obj.status.title()
    action_buttons.short_description = 'Actions'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:deposit_id>/approve/',
                self.admin_site.admin_view(self.approve_deposit),
                name='approve_deposit',
            ),
            path(
                '<int:deposit_id>/reject/',
                self.admin_site.admin_view(self.reject_deposit),
                name='reject_deposit',
            ),
        ]
        return custom_urls + urls

    def approve_deposit(self, request, deposit_id):
        deposit = self.get_object(request, deposit_id)
        if deposit and deposit.status == 'pending':
            deposit.status = 'approved'
            deposit.save()
            # Update user's wallet balance
            wallet, created = Wallet.objects.get_or_create(user=deposit.user)
            wallet.balance += deposit.amount
            wallet.save()
            # Update user's total invested amount
            deposit.user.total_invested += deposit.amount
            deposit.user.update_level()
            deposit.user.save()
        return self.response_change(request, deposit)

    def reject_deposit(self, request, deposit_id):
        deposit = self.get_object(request, deposit_id)
        if deposit and deposit.status == 'pending':
            deposit.status = 'rejected'
            deposit.save()
        return self.response_change(request, deposit)

@admin.register(ReferralReward)
class ReferralRewardAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referred', 'deposit_amount', 'reward_amount', 'awarded_at', 'is_paid')
    list_filter = ('is_paid', 'awarded_at')
    search_fields = ('referrer__username', 'referred__username')
    readonly_fields = ('awarded_at',)
    ordering = ('-awarded_at',)

@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_method', 'status', 'created_at', 'action_buttons')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__username', 'user__email', 'account_number', 'account_holder_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'amount', 'payment_method', 'status')
        }),
        ('Bank Details', {
            'fields': ('account_holder_name', 'bank_name', 'account_number', 'branch_code', 'account_type'),
            'classes': ('collapse',),
            'description': 'Bank details for bank transfer withdrawals'
        }),
        ('Additional Information', {
            'fields': ('admin_notes', 'created_at', 'updated_at')
        }),
    )

    def action_buttons(self, obj):
        if obj.status == 'pending':
            approve_url = reverse('admin:approve_withdrawal', args=[obj.pk])
            reject_url = reverse('admin:reject_withdrawal', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}">Approve</a>&nbsp;'
                '<a class="button" href="{}">Reject</a>',
                approve_url, reject_url
            )
        return obj.status.title()
    action_buttons.short_description = 'Actions'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:withdrawal_id>/approve/',
                self.admin_site.admin_view(self.approve_withdrawal),
                name='approve_withdrawal',
            ),
            path(
                '<int:withdrawal_id>/reject/',
                self.admin_site.admin_view(self.reject_withdrawal),
                name='reject_withdrawal',
            ),
        ]
        return custom_urls + urls

    def approve_withdrawal(self, request, withdrawal_id):
        withdrawal = self.get_object(request, withdrawal_id)
        if withdrawal and withdrawal.status == 'pending':
            try:
                # Get the user's wallet
                wallet = withdrawal.user.wallet
                if wallet.balance >= withdrawal.amount:
                    # Update withdrawal status
                    withdrawal.status = 'approved'
                    withdrawal.save()
                    
                    # Deduct from wallet and ensure it doesn't go below 0
                    wallet.balance = max(0, wallet.balance - withdrawal.amount)
                    wallet.save()
                    
                    # Update message based on remaining balance
                    if wallet.balance == 0:
                        self.message_user(request, f'Withdrawal of R{withdrawal.amount} has been approved. Wallet balance is now R0.00')
                    else:
                        self.message_user(request, f'Withdrawal of R{withdrawal.amount} has been approved. Remaining balance: R{wallet.balance}')
                else:
                    self.message_user(request, 'Insufficient balance for withdrawal.', level='error')
            except Exception as e:
                self.message_user(request, str(e), level='error')
        return self.response_change(request, withdrawal)

    def reject_withdrawal(self, request, withdrawal_id):
        withdrawal = self.get_object(request, withdrawal_id)
        if withdrawal and withdrawal.status == 'pending':
            withdrawal.status = 'rejected'
            withdrawal.save()
            self.message_user(request, f'Withdrawal of R{withdrawal.amount} has been rejected.')
        return self.response_change(request, withdrawal)
