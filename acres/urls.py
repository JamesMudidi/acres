from django.contrib import admin
from django.urls import path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from django.views.generic.base import RedirectView


schema_view = get_schema_view(
    openapi.Info(
        title="Acres",
        default_version="v1",
        description="Acres is built for professional property managers.\
               It includes all the necessary tools for a professional\
               property management company to manage unlimited properties,\
               owners, and tenants. Our goal is to provide your business with\
               the best software, coupled with the best customer service in the\
               industry, so you choose to use it because you love it rather than \
               be forced to use it because of a contract",
        terms_of_service="https://www.google.com/policies/terms/",
    ),
    permission_classes=(AllowAny,),
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/documentation/', schema_view.with_ui('swagger', cache_timeout=0),
         name='api_documentation'),
    path('', RedirectView.as_view(url='api/documentation/', permanent=False),
         name='api_documentation'),
]
