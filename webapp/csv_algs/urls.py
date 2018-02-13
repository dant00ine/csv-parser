from django.urls import path, include, re_path

from . import views

urlpatterns = [
    # root url
    path('', views.index, name='index'),

    # ex: batches/5
    # path('<int:batch_id/', views.show_batch, name='show_batch'),
    path('get_sms/', views.get_sms, name='get_sms'),

    # post to batches
    path('create/', views.create, name='create'),
]