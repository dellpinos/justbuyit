from os import name
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("listing/create", views.create_listing, name="create_listing"),
    path("listing/watch/change", views.watch_listing, name="watch_listing"),
    path("listing/watch/watchlist", views.watchlist, name="watchlist"),
    path("listing/bid/new", views.bid_listing, name="bid_listing"),
    path("listing/bid/your_bids", views.your_bids, name="your_bids"),
    path("listing/close", views.close_listing, name="close_listing"),
    path("listing/comment/create", views.create_comment, name="create_comment"),
    path("listing/your_listings/show", views.your_listings, name="your_listings"),
    path("listing/edit/<int:listing>", views.edit_listing, name="edit_listing"),
    path("listing/<int:listing>", views.show_listing, name="show_listing"),
    path("categories", views.categories_index, name="index_category"),
    path("categories/<str:category>", views.category_show, name="show_category"),
]
