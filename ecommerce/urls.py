from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('admin/', admin.site.urls),

    # Editor de Texto
    path("ckeditor5/", include('django_ckeditor_5.urls')),

    # APPs
    path('', include('product.urls', namespace='product')),

    path('carrinho/', include('cart.urls', namespace='cart')),
    path('checkout/', include('checkout.urls', namespace='checkout')),
    path('accounts/', include('accounts.urls', namespace='accounts')),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)