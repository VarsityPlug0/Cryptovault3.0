from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('tiers/', views.tiers_view, name='tiers'),
    path('invest/<int:tier_id>/', views.invest_view, name='invest'),
    path('cash-out/<int:investment_id>/', views.cash_out_view, name='cash_out'),
    path('check-cash-out/<int:investment_id>/', views.check_cash_out_view, name='check_cash_out'),
    path('get-server-time/', views.get_server_time_view, name='get_server_time'),
    path('wallet/', views.wallet_view, name='wallet'),
    path('referral/', views.referral_page, name='referral'),
    path('feed/', views.feed_view, name='feed'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('withdrawal/', views.withdrawal_view, name='withdrawal'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('contact/', views.contact_view, name='contact'),
] 