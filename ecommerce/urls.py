from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [

    path('admin/', admin.site.urls),

    # Editor de Texto
    path("ckeditor5/", include('django_ckeditor_5.urls')),

    # APPs
    path('', include('product.urls', namespace='product')),

    path('carrinho/', include('cart.urls', namespace='cart')),
    path('checkout/', include('checkout.urls', namespace='checkout')),
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # --- URLs de Autenticação do Django para recuperação de senha ---
    path('contas/password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('contas/password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('contas/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('contas/reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)