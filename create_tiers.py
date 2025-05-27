import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aicryptovault.settings')
django.setup()

from core.models import InvestmentTier

# Define investment tiers
tiers = [
    {
        'name': 'Starter',
        'amount': 50,
        'return_amount': 100,
        'duration_days': 0.5,
        'min_level': 1,
        'description': 'Perfect for first-time investors. Quick 12-hour return with 100% profit.'
    },
    {
        'name': 'Basic',
        'amount': 200,
        'return_amount': 500,
        'duration_days': 2,
        'min_level': 1,
        'description': 'Ideal for regular investors. 2-day investment with 150% profit.'
    },
    {
        'name': 'Standard',
        'amount': 500,
        'return_amount': 1500,
        'duration_days': 3,
        'min_level': 1,
        'description': 'Popular choice for steady growth. 3-day investment with 200% profit.'
    },
    {
        'name': 'Premium',
        'amount': 1000,
        'return_amount': 3000,
        'duration_days': 4,
        'min_level': 1,
        'description': 'For serious investors. 4-day investment with 200% profit.'
    },
    {
        'name': 'Elite',
        'amount': 2000,
        'return_amount': 6000,
        'duration_days': 5,
        'min_level': 2,
        'description': 'High-value investment option. 5-day term with 200% profit.'
    },
    {
        'name': 'Ultimate',
        'amount': 5000,
        'return_amount': 15000,
        'duration_days': 7,
        'min_level': 2,
        'description': 'Maximum returns for experienced investors. 7-day investment with 200% profit.'
    },
    {
        'name': 'Platinum Plus',
        'amount': 7500,
        'return_amount': 22500,
        'duration_days': 8,
        'min_level': 2,
        'description': 'Exclusive tier for dedicated investors. 8-day investment with 200% profit.'
    },
    {
        'name': 'Diamond',
        'amount': 10000,
        'return_amount': 30000,
        'duration_days': 10,
        'min_level': 3,
        'description': 'Premium tier for high-net-worth investors. 10-day term with 200% profit.'
    },
    {
        'name': 'Platinum',
        'amount': 20000,
        'return_amount': 60000,
        'duration_days': 15,
        'min_level': 3,
        'description': 'Elite tier for sophisticated investors. 15-day term with 200% profit.'
    },
    {
        'name': 'Master',
        'amount': 50000,
        'return_amount': 150000,
        'duration_days': 20,
        'min_level': 3,
        'description': 'Ultimate tier for master investors. 20-day term with 200% profit.'
    }
]

# Create tiers
for tier_data in tiers:
    InvestmentTier.objects.get_or_create(
        name=tier_data['name'],
        defaults={
            'amount': tier_data['amount'],
            'return_amount': tier_data['return_amount'],
            'duration_days': tier_data['duration_days'],
            'min_level': tier_data['min_level'],
            'description': tier_data['description']
        }
    )

print("Investment tiers created successfully!") 