from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import InvestmentTier, DailySpecial
import random

class Command(BaseCommand):
    help = 'Creates a daily special investment offer'

    def handle(self, *args, **kwargs):
        # Get all available tiers
        tiers = InvestmentTier.objects.all()
        
        # Select a random tier
        selected_tier = random.choice(tiers)
        
        # Set start time to now
        start_time = timezone.now()
        
        # Set end time to 24 hours from now
        end_time = start_time + timedelta(hours=24)
        
        # Generate a random multiplier between 1.2 and 2.0 (20% to 100% extra returns)
        multiplier = round(random.uniform(1.2, 2.0), 2)
        
        # Create the daily special
        special = DailySpecial.objects.create(
            tier=selected_tier,
            start_time=start_time,
            end_time=end_time,
            special_return_multiplier=multiplier
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created daily special for {selected_tier.name} '
                f'with {multiplier}x returns until {end_time}'
            )
        ) 