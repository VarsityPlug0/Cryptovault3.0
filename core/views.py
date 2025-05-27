from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import InvestmentTier, Investment, Wallet, Referral, IPAddress, CustomUser, Deposit, ReferralReward, Withdrawal, DailySpecial
from django.contrib import messages
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from datetime import timedelta
from decimal import Decimal
from django.db.models import Sum
from django.http import JsonResponse
from django.urls import reverse
import random
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count

# Home view
# Landing page for the application
def home_view(request):
    # Get investment tiers
    investment_tiers = InvestmentTier.objects.all().order_by('amount')
    
    # Get platform stats
    total_investors = CustomUser.objects.count()
    total_payouts = Investment.objects.filter(is_active=False).aggregate(
        total=Sum('return_amount')
    )['total'] or 0
    ai_strategies = 5  # Mock value for now
    
    # Get top referrers
    top_referrers = CustomUser.objects.annotate(
        total_earnings=Sum('rewards__reward_amount')
    ).filter(total_earnings__isnull=False).order_by('-total_earnings')[:3]
    
    # Generate referral link for authenticated users
    referral_link = None
    if request.user.is_authenticated:
        referral_link = request.build_absolute_uri(
            reverse('register') + f'?ref={request.user.username}'
        )
    
    # Mock testimonials (replace with real data later)
    testimonials = [
        {
            'name': 'John D.',
            'content': 'I turned R50 into R75 in just 7 days. This platform works!'
        },
        {
            'name': 'Sarah M.',
            'content': 'The AI trading system is impressive. My investments are growing steadily.'
        },
        {
            'name': 'Michael T.',
            'content': 'Best crypto investment platform I\'ve used. The returns are consistent.'
        }
    ]
    
    context = {
        'investment_tiers': investment_tiers,
        'total_investors': total_investors,
        'total_payouts': total_payouts,
        'ai_strategies': ai_strategies,
        'top_referrers': top_referrers,
        'referral_link': referral_link,
        'testimonials': testimonials,
    }
    
    return render(request, 'core/home.html', context)

# Registration view
# Handles user registration
def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('register')
            
        try:
            user = CustomUser.objects.create_user(
                username=email,
                email=email,
                password=password,
                phone=phone
            )
            
            # Create a wallet for the user
            Wallet.objects.create(user=user)
            
            # Handle referral code
            ref_code = request.GET.get('ref')
            if ref_code:
                try:
                    referrer = CustomUser.objects.get(username=ref_code)
                    user.referred_by = referrer
                    user.save()
                except CustomUser.DoesNotExist:
                    pass
            
            # Log the user in
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to AI Crypto Vault.')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, 'An error occurred during registration. Please try again.')
            return redirect('register')
            
    return render(request, 'core/register.html')

# Login view
# Handles user login
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'core/login.html')

# Dashboard view
# Shows user balance, investments, and referral stats
@login_required
def dashboard_view(request):
    user = request.user
    # Get or create wallet for the user
    wallet, created = Wallet.objects.get_or_create(user=user)
    investments = Investment.objects.filter(user=user)
    deposits = Deposit.objects.filter(user=user).order_by('-created_at')
    referrals = Referral.objects.filter(inviter=user)
    
    # Calculate total earnings
    total_earnings = sum(inv.return_amount - inv.amount for inv in investments if not inv.is_active)
    
    # Calculate total expected return from active investments
    active_investments = investments.filter(is_active=True)
    total_expected_return = sum(inv.return_amount for inv in active_investments)
    
    # Calculate max waiting time (days until the furthest end date)
    max_waiting_time = 0
    if active_investments.exists():
        furthest_end_date = max(inv.end_date for inv in active_investments)
        max_waiting_time = (furthest_end_date - timezone.now()).days
    
    # Calculate total deposits
    total_deposits = sum(dep.amount for dep in deposits if dep.status == 'approved')
    
    # Calculate total bonus from referrals
    total_bonus = sum(ref.bonus_amount for ref in referrals)
    
    # Get active and completed investments
    active_investments = investments.filter(is_active=True)
    completed_investments = investments.filter(is_active=False)
    
    # Get available tiers for user's level
    available_tiers = InvestmentTier.objects.filter(min_level__lte=user.level)
    
    # Calculate progress to next level
    next_level_threshold = user.get_next_level_threshold()
    progress_percentage = 0
    if next_level_threshold > 0:
        if user.level == 1:
            progress_percentage = (user.total_invested / Decimal('10000')) * 100
        elif user.level == 2:
            progress_percentage = ((user.total_invested - Decimal('10000')) / Decimal('10000')) * 100
    
    context = {
        'wallet': wallet,
        'total_earnings': total_earnings,
        'total_expected_return': total_expected_return,
        'max_waiting_time': max_waiting_time,
        'total_deposits': total_deposits,
        'total_bonus': total_bonus,
        'active_investments': active_investments,
        'completed_investments': completed_investments,
        'deposits': deposits,
        'tiers': available_tiers,
        'user_level': user.level,
        'total_invested': user.total_invested,
        'next_level_threshold': next_level_threshold,
        'progress_percentage': progress_percentage,
    }
    
    return render(request, 'core/dashboard.html', context)

# Tiers view
# Lists all available investment tiers
@login_required
def tiers_view(request):
    user = request.user
    tiers = InvestmentTier.objects.all()
    
    # Get active daily special
    now = timezone.now()
    try:
        daily_special = DailySpecial.objects.filter(
            is_active=True,
            start_time__lte=now,
            end_time__gte=now
        ).latest('start_time')
    except DailySpecial.DoesNotExist:
        daily_special = None
    
    # Calculate total invested from actual investments
    total_invested = sum(inv.amount for inv in Investment.objects.filter(user=user))
    
    # Get or create user's wallet
    wallet, created = Wallet.objects.get_or_create(user=user)
    
    # Add eligibility and lock status to each tier
    for tier in tiers:
        tier.eligible = tier.min_level <= user.level
        # Get investment for this tier if it exists
        investment = Investment.objects.filter(user=user, tier=tier).first()
        tier.invested = investment is not None
        
        # Calculate if user has enough balance for this tier
        tier.has_sufficient_balance = wallet.balance >= tier.amount
        if not tier.has_sufficient_balance:
            tier.remaining_amount = tier.amount - wallet.balance
        
        if investment:
            time_remaining = investment.end_date - timezone.now()
            tier.waiting_time_days = time_remaining.days
            tier.waiting_time_hours = time_remaining.seconds // 3600
            tier.waiting_time_minutes = (time_remaining.seconds % 3600) // 60
            tier.waiting_time_seconds = time_remaining.seconds % 60
            tier.can_cash_out = not investment.is_active and investment.end_date <= timezone.now()
        # Check if this tier is the daily special
        if daily_special and daily_special.tier == tier:
            tier.is_daily_special = True
            tier.special_return_multiplier = daily_special.special_return_multiplier
            tier.special_return_amount = daily_special.special_return_amount
        else:
            tier.is_daily_special = False
    
    context = {
        'tiers': tiers,
        'user_level': user.level,
        'total_invested': total_invested,
        'daily_special': daily_special,
        'wallet_balance': wallet.balance,
    }
    return render(request, 'core/tiers.html', context)

# Invest view
# Allows user to invest in a tier
@login_required
def invest_view(request, tier_id):
    try:
        user = request.user
        tier = InvestmentTier.objects.get(id=tier_id)
        
        # Check if user's level allows this tier
        if user.level < tier.min_level:
            messages.error(request, f'You need to be level {tier.min_level} to invest in this tier.')
            return redirect('tiers')
        
        # Check if user has sufficient balance
        wallet = Wallet.objects.get(user=user)
        if wallet.balance < tier.amount:
            messages.error(request, 'Insufficient balance. Please make a deposit first.')
            return redirect('tiers')
        
        # Create investment
        end_date = timezone.now() + timedelta(days=tier.duration_days)
        investment = Investment.objects.create(
            user=user,
            tier=tier,
            amount=tier.amount,
            return_amount=tier.return_amount,
            end_date=end_date,
            expires_at=end_date  # Set expires_at to the same value as end_date
        )
        
        # Update wallet balance
        wallet.balance -= tier.amount
        wallet.save()
        
        messages.success(request, f'Successfully invested R{tier.amount} in {tier.name}.')
        return redirect('dashboard')
        
    except InvestmentTier.DoesNotExist:
        messages.error(request, 'Invalid investment tier.')
        return redirect('tiers')

# Wallet view
# Shows wallet balance and withdrawal option
@login_required
def wallet_view(request):
    user = request.user
    # Get or create wallet for the user
    wallet, created = Wallet.objects.get_or_create(user=user)
    deposits = Deposit.objects.filter(user=user).order_by('-created_at')
    withdrawals = Withdrawal.objects.filter(user=user).order_by('-created_at')
    
    context = {
        'wallet': wallet,
        'deposits': deposits,
        'withdrawals': withdrawals,
    }
    return render(request, 'core/wallet.html', context)

# Referral view
# Shows referral link and stats
@login_required
def referral_view(request):
    user = request.user
    referrals = Referral.objects.filter(inviter=user)
    total_bonus = sum(ref.bonus_amount for ref in referrals)
    
    context = {
        'referrals': referrals,
        'total_bonus': total_bonus,
        'referral_code': user.username,  # Using username as referral code
    }
    return render(request, 'core/referral.html', context)

# Profile view
# Shows and allows editing of user profile
@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        user.auto_reinvest = request.POST.get('auto_reinvest') == 'on'
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    return render(request, 'core/profile.html')

# Logout view
# Handles user logout
@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

# Deposit view
# Handles deposit creation
@login_required
def deposit_view(request):
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        payment_method = request.POST.get('payment_method')
        proof_image = request.FILES.get('proof_image')
        
        if amount < 50:
            messages.error(request, 'Minimum deposit amount is R50.')
            return redirect('deposit')
        
        Deposit.objects.create(
            user=request.user,
            amount=amount,
            payment_method=payment_method,
            proof_image=proof_image
        )
        
        messages.success(request, 'Deposit request submitted successfully. Please wait for approval.')
        return redirect('wallet')
        
    return render(request, 'core/deposit.html')

@login_required
def referral_page(request):
    user = request.user
    context = {
        'total_referred': user.referred_users.count(),
        'valid_deposits': user.rewards.count(),
        'total_earned': user.rewards.aggregate(Sum('reward_amount'))['reward_amount__sum'] or 0,
        'referral_rewards': user.rewards.select_related('referred').all(),
        'referral_code': user.username,  # Using username as referral code
    }
    return render(request, 'core/referral.html', context)

@login_required
def withdrawal_view(request):
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        payment_method = request.POST.get('payment_method')
        
        if amount < 50:
            messages.error(request, 'Minimum withdrawal amount is R50.')
            return redirect('withdrawal')
        
        # Check if user has sufficient balance
        wallet = Wallet.objects.get(user=request.user)
        if wallet.balance < amount:
            messages.error(request, 'Insufficient balance for withdrawal.')
            return redirect('withdrawal')
        
        try:
            withdrawal_data = {
                'user': request.user,
                'amount': amount,
                'payment_method': payment_method,
            }
            
            # Add bank details if payment method is bank transfer
            if payment_method == 'bank':
                withdrawal_data.update({
                    'account_holder_name': request.POST.get('account_holder_name', ''),
                    'bank_name': request.POST.get('bank_name', ''),
                    'account_number': request.POST.get('account_number', ''),
                    'branch_code': request.POST.get('branch_code', ''),
                    'account_type': request.POST.get('account_type', ''),
                })
            
            Withdrawal.objects.create(**withdrawal_data)
            messages.success(request, 'Withdrawal request submitted successfully. Please wait for approval.')
            return redirect('wallet')
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('withdrawal')
        
    return render(request, 'core/withdrawal.html')

# Feed view
# Shows real-time activity and AI investment updates
@login_required
def feed_view(request):
    # Get latest investment payouts from the last 24 hours
    latest_payouts = Investment.objects.filter(
        is_active=False,
        end_date__gte=timezone.now() - timedelta(days=1)
    ).select_related('tier', 'user').order_by('-end_date')[:5]
    
    # Get recent deposits from the last 24 hours
    recent_deposits = Deposit.objects.filter(
        status='approved',
        created_at__gte=timezone.now() - timedelta(days=1)
    ).select_related('user').order_by('-created_at')[:10]
    
    # Get recent referral rewards from the last 24 hours
    recent_referrals = ReferralReward.objects.filter(
        awarded_at__gte=timezone.now() - timedelta(days=1)
    ).select_related(
        'referrer', 'referred'
    ).order_by('-awarded_at')[:5]
    
    # Dummy usernames for simulated activity
    dummy_names = [
        'BitcoinPro', 'DigitalTrader', 'CryptoNinja', 'BlockchainKing',
        'EthereumMaster', 'TradingGuru', 'TradingTitan', 'CryptoQueen',
        'BitcoinWizard', 'BlockchainBoss', 'SmartInvestor', 'CryptoElite'
    ]
    
    # Dummy tier names and durations
    dummy_tiers = [
        {'name': 'Silver Elite', 'duration': 14},
        {'name': 'Gold Premium', 'duration': 21},
        {'name': 'Diamond VIP', 'duration': 45}
    ]
    
    # Process AI investment updates with dummy data
    investment_updates = [
        {
            'tier_name': 'Diamond VIP',
            'username': 'CryptoQueen',
            'return_amount': 5667.53,
            'amount': 4733,
            'duration': 45,
            'timestamp': timezone.now() - timedelta(minutes=14)
        },
        {
            'tier_name': 'Diamond VIP',
            'username': 'CryptoNinja',
            'return_amount': 2982.07,
            'amount': 2270,
            'duration': 45,
            'timestamp': timezone.now() - timedelta(minutes=27)
        },
        {
            'tier_name': 'Silver Elite',
            'username': 'BitcoinWizard',
            'return_amount': 10352.35,
            'amount': 9183,
            'duration': 14,
            'timestamp': timezone.now() - timedelta(minutes=29)
        },
        {
            'tier_name': 'Diamond VIP',
            'username': 'BitcoinPro',
            'return_amount': 9164.33,
            'amount': 6808,
            'duration': 45,
            'timestamp': timezone.now() - timedelta(minutes=44)
        },
        {
            'tier_name': 'Gold Premium',
            'username': 'DigitalTrader',
            'return_amount': 7602.12,
            'amount': 5964,
            'duration': 21,
            'timestamp': timezone.now() - timedelta(minutes=60)
        }
    ]
    
    # Get user milestones (deposits, upgrades, payouts)
    user_milestones = []
    
    # Add real deposits with dummy usernames
    for deposit in recent_deposits:
        user_milestones.append({
            'type': 'deposit',
            'user': {'username': random.choice(dummy_names)},
            'amount': deposit.amount,
            'timestamp': deposit.created_at
        })
    
    # Add simulated deposits if we have less than 10 total activities
    while len(user_milestones) < 10:
        user_milestones.append({
            'type': 'deposit',
            'user': {'username': random.choice(dummy_names)},
            'amount': random.randint(1000, 5000),
            'timestamp': timezone.now() - timedelta(minutes=random.randint(1, 60))
        })
    
    # Add upgrades (when users reach new levels) from the last 24 hours
    level_upgrades = CustomUser.objects.filter(
        level__gt=1,
        date_joined__gte=timezone.now() - timedelta(days=1)
    ).order_by('-date_joined')[:3]
    
    # Add real upgrades with dummy usernames
    for user in level_upgrades:
        user_milestones.append({
            'type': 'upgrade',
            'user': {'username': random.choice(dummy_names)},
            'level': user.level,
            'timestamp': user.date_joined
        })
    
    # Add simulated upgrades if we have less than 13 total activities
    while len(user_milestones) < 13:
        user_milestones.append({
            'type': 'upgrade',
            'user': {'username': random.choice(dummy_names)},
            'level': random.randint(2, 3),
            'timestamp': timezone.now() - timedelta(minutes=random.randint(1, 60))
        })
    
    # Add real payouts with dummy usernames
    for payout in latest_payouts:
        user_milestones.append({
            'type': 'payout',
            'user': {'username': random.choice(dummy_names)},
            'amount': payout.return_amount - payout.amount,
            'timestamp': payout.end_date
        })
    
    # Add simulated payouts if we have less than 15 total activities
    while len(user_milestones) < 15:
        user_milestones.append({
            'type': 'payout',
            'user': {'username': random.choice(dummy_names)},
            'amount': random.randint(1000, 5000),
            'timestamp': timezone.now() - timedelta(minutes=random.randint(1, 60))
        })
    
    # Sort milestones by timestamp
    user_milestones.sort(key=lambda x: x['timestamp'], reverse=True)
    user_milestones = user_milestones[:15]  # Keep the 15 most recent activities
    
    # Process referral activities with dummy usernames
    referral_activities = []
    
    # Add real referral activities with dummy usernames
    for reward in recent_referrals:
        referral_activities.append({
            'referrer': random.choice(dummy_names),
            'referred': random.choice(dummy_names),
            'amount': reward.reward_amount,
            'timestamp': reward.awarded_at
        })
    
    # Add simulated referral activities if we have less than 5
    while len(referral_activities) < 5:
        referral_activities.append({
            'referrer': random.choice(dummy_names),
            'referred': random.choice(dummy_names),
            'amount': random.randint(35, 88),
            'timestamp': timezone.now() - timedelta(minutes=random.randint(1, 60))
        })
    
    # Sort referral activities by timestamp
    referral_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    referral_activities = referral_activities[:5]  # Keep the 5 most recent activities
    
    # Dynamic tips based on recent activity
    tips = [
        "💡 Tip: Reinvest to reach higher tiers faster.",
        "💡 Tip: Refer friends to earn passive income.",
        "💡 Tip: Higher tiers offer better returns.",
        "💡 Tip: Stay consistent with your investments.",
        "💡 Tip: Monitor market trends for better timing."
    ]
    
    # Security reminders
    security_reminders = [
        "⚠️ We never ask for your private keys. Stay safe.",
        "⚠️ Enable 2FA for extra security.",
        "⚠️ Keep your login credentials private.",
        "⚠️ Verify all transactions carefully.",
        "⚠️ Report suspicious activity immediately."
    ]
    
    context = {
        'investment_updates': investment_updates,
        'user_milestones': user_milestones,
        'referral_activities': referral_activities,
        'tips': tips,
        'security_reminders': security_reminders,
    }
    
    return render(request, 'core/feed.html', context)

@login_required
def cash_out_view(request, investment_id):
    try:
        investment = Investment.objects.get(id=investment_id, user=request.user)
        
        # Check if investment is ready for cash out
        if investment.is_active or investment.end_date > timezone.now():
            messages.error(request, 'This investment is not ready for cash out yet.')
            return redirect('tiers')
        
        # Get user's wallet
        wallet = Wallet.objects.get(user=request.user)
        
        # Add return amount to wallet balance
        wallet.balance += investment.return_amount
        wallet.save()
        
        # Mark investment as cashed out
        investment.is_active = False
        investment.save()
        
        messages.success(request, f'Successfully cashed out R{investment.return_amount}.')
        return redirect('tiers')
        
    except Investment.DoesNotExist:
        messages.error(request, 'Invalid investment.')
        return redirect('tiers')

@login_required
def check_cash_out_view(request, investment_id):
    try:
        investment = Investment.objects.get(id=investment_id, user=request.user)
        can_cash_out = not investment.is_active and investment.end_date <= timezone.now()
        
        return JsonResponse({
            'can_cash_out': can_cash_out,
            'return_amount': str(investment.return_amount) if can_cash_out else None
        })
    except Investment.DoesNotExist:
        return JsonResponse({'error': 'Invalid investment'}, status=404)

@login_required
def get_server_time_view(request):
    return JsonResponse({
        'server_time': timezone.now().isoformat()
    })

def newsletter_subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Here you would typically save the email to your newsletter subscribers list
            # For now, we'll just show a success message
            messages.success(request, 'Thank you for subscribing to our newsletter!')
        else:
            messages.error(request, 'Please provide a valid email address.')
    return redirect('home')

def terms_view(request):
    return render(request, 'core/terms.html')

def privacy_view(request):
    return render(request, 'core/privacy.html')

def contact_view(request):
    if request.method == 'POST':
        # Here you would typically handle the contact form submission
        # For now, we'll just show a success message
        messages.success(request, 'Thank you for your message. We will get back to you soon!')
        return redirect('contact')
    return render(request, 'core/contact.html')

@staff_member_required
def admin_dashboard_view(request):
    # Get all tiers
    tiers = InvestmentTier.objects.all().order_by('amount')
    
    # Get investment statistics for each tier
    tier_stats = []
    for tier in tiers:
        # Get total number of investments for this tier
        total_investments = Investment.objects.filter(tier=tier).count()
        
        # Get total amount invested in this tier
        total_invested = Investment.objects.filter(tier=tier).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Get total returns for this tier
        total_returns = Investment.objects.filter(tier=tier).aggregate(
            total=Sum('return_amount')
        )['total'] or 0
        
        # Get active investments count
        active_investments = Investment.objects.filter(
            tier=tier,
            is_active=True
        ).count()
        
        # Get completed investments count
        completed_investments = Investment.objects.filter(
            tier=tier,
            is_active=False
        ).count()
        
        # Get unique investors count for this tier
        unique_investors = Investment.objects.filter(tier=tier).values('user').distinct().count()
        
        tier_stats.append({
            'tier': tier,
            'total_investments': total_investments,
            'total_invested': total_invested,
            'total_returns': total_returns,
            'active_investments': active_investments,
            'completed_investments': completed_investments,
            'unique_investors': unique_investors,
        })
    
    # Get overall statistics
    total_deposits = Deposit.objects.filter(status='approved').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_investments = Investment.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_returns = Investment.objects.filter(is_active=False).aggregate(
        total=Sum('return_amount')
    )['total'] or 0
    
    total_users = CustomUser.objects.count()
    
    # Get detailed user information
    users = CustomUser.objects.all().order_by('-date_joined')
    user_details = []
    
    for user in users:
        # Get user's wallet
        wallet = Wallet.objects.filter(user=user).first()
        
        # Get user's deposits
        deposits = Deposit.objects.filter(user=user).order_by('-created_at')
        total_deposited = deposits.filter(status='approved').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Get user's investments
        investments = Investment.objects.filter(user=user)
        total_invested = investments.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Get user's returns
        total_returns = investments.filter(is_active=False).aggregate(
            total=Sum('return_amount')
        )['total'] or 0
        
        # Get user's active investments
        active_investments = investments.filter(is_active=True)
        
        # Get user's referral earnings
        referral_earnings = ReferralReward.objects.filter(referrer=user).aggregate(
            total=Sum('reward_amount')
        )['total'] or 0
        
        # Get user's referrals
        referrals = Referral.objects.filter(inviter=user)
        
        user_details.append({
            'user': user,
            'wallet': wallet,
            'total_deposited': total_deposited,
            'total_invested': total_invested,
            'total_returns': total_returns,
            'active_investments': active_investments,
            'referral_earnings': referral_earnings,
            'total_referrals': referrals.count(),
            'deposits': deposits,
            'investments': investments,
            'referrals': referrals,
        })
    
    # Get recent activities
    recent_deposits = Deposit.objects.all().order_by('-created_at')[:10]
    recent_investments = Investment.objects.all().order_by('-created_at')[:10]
    recent_returns = Investment.objects.filter(is_active=False).order_by('-end_date')[:10]
    
    context = {
        'tier_stats': tier_stats,
        'total_deposits': total_deposits,
        'total_investments': total_investments,
        'total_returns': total_returns,
        'total_users': total_users,
        'user_details': user_details,
        'recent_deposits': recent_deposits,
        'recent_investments': recent_investments,
        'recent_returns': recent_returns,
    }
    
    return render(request, 'core/admin_dashboard.html', context)
