"""djangoProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from report import views
from report.views import ArticlesViewSet, black_list_refresh_view

router = routers.DefaultRouter()
router.register(r'articles', ArticlesViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/token/blacklist/', black_list_refresh_view),

    path('api/v1/branches/', views.get_branches),
    path('api/v1/main-data/', views.main_data_dashboard),
    path('api/v1/article_grp/', views.articles_group),

    path('api/v1/transactions/', views.get_transactions),
    path('api/v1/transactions-short/', views.get_transactions_short),
    path('api/v1/transactions-chart/', views.get_transactions_chart),

    path('api/v1/', include(router.urls)),
]
