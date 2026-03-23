from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    # path('login/', views.login_view, name='login'),
    # path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # path('logout/', views.logout_view, name='logout'),
    path('about/',views.about_view,name='about'),
    path('contact/',views.contact_view,name='contact'),
    path("smartclean/", views.smart_clean, name="smart_clean"),
    path("visual/",views.data_dashboard,name="data_dashboard"),
    path("port/",views.port_view,name="port")

    

]

