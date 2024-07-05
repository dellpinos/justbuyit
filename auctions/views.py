from bson import is_valid
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Max, F
from django.utils import timezone

from .models import User, Listing, Comment, Bid, UserListing, Category

# Listing form
class ListingForm(forms.Form):

    id_hidden = forms.CharField(
        widget=forms.HiddenInput(),
        required=False  
    )
    title = forms.CharField(
        label = "Title",
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter the title'
        }),
        max_length=60,
    )
    description = forms.CharField(
        label = "Description",
        widget=forms.Textarea(attrs={
            'placeholder': 'Enter a description'
        }),
        max_length=255
    )
    image = forms.CharField(
        label = "Image (max 200 characters)",
        validators=[URLValidator()],
        widget=forms.TextInput(attrs={
            'placeholder': 'https://example_image.com'
        }),
        required=False,
        max_length=200,
    )
    price = forms.DecimalField(
        label = "Initial Price",
        widget=forms.NumberInput(attrs={
            'placeholder': '299'
        }),
        max_value=99999999
    )
    category = forms.ChoiceField(
        label="Category",
        widget=forms.Select,
        required=False
    )
    state_change = forms.BooleanField(
        label="Listing Activation State",
        widget=forms.CheckboxInput(attrs={'class': 'form__checkbox'}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(ListingForm, self).__init__(*args, **kwargs)
        self.fields['category'].choices = [("", "-- None --")] + [
            (category.id, category.title) for category in Category.objects.all()
        ]

    # Prevents the title from being repeated
    def clean_title(self):
        title = self.cleaned_data.get("title")
        if self.cleaned_data.get("id_hidden"):
            instance_id = self.cleaned_data.get("id_hidden")
            if Listing.objects.filter(title=title).exclude(id=instance_id).exists():
                raise forms.ValidationError("Title already taken.")
            return title
        else:
            if Listing.objects.filter(title=title).exists():
                raise forms.ValidationError("Title already taken.")
            return title

    
    def clean_url(self):
        url = self.cleaned_data.get('url')
        validate = URLValidator()

        try:
            validate(url)
        except ValidationError:
            raise forms.ValidationError("Enter a valid URL.")
        return url

def index(request):

    active_listings = Listing.objects.exclude(state=False).order_by('-bid_change_at')

    for listing in active_listings:
        
        higher_bid = Bid.objects.filter(listing = listing).order_by('-amount').first()

        if higher_bid is None:
            listing.actual_price = listing.price
        else:
            listing.actual_price = higher_bid.amount

    return render(request, "auctions/index.html", {
        "listings" : active_listings
    })

def create_listing(request):

    # Auth
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))

    if request.method == 'POST':
        form = ListingForm(request.POST)

        if form.is_valid():
            
            if form.cleaned_data['category']:
                category_db = Category.objects.get(pk=form.cleaned_data['category'])
            else:
                category_db = None

            listing = Listing(
                title = form.cleaned_data['title'],
                description = form.cleaned_data['description'],
                image = form.cleaned_data['image'],
                price = form.cleaned_data['price'],
                state = form.cleaned_data['state_change'],
                category = category_db,
                user = request.user
            )
            listing.save()

            return HttpResponseRedirect(reverse("index"))

        else:
            return render(request, "auctions/create.html", {
            "form": form
        })
            
    else:
        form = ListingForm()
        return render(request, "auctions/create.html", {
            "form": form
        })
    

def show_listing(request, listing):

    listing_db = Listing.objects.get(pk=listing)
    comments = Comment.objects.filter(listing = listing)
    higher_bid = Bid.objects.filter(listing = listing).order_by('-amount').first()

    if higher_bid is None:
        actual_price = listing_db.price
    else:
        actual_price = higher_bid.amount

    watching = False
    has_commented = False

    if request.user.is_authenticated:

        user = request.user
        watching_item = UserListing.objects.filter(user=user, listing=listing)
        comment_item = Comment.objects.filter(user = user, listing=listing)

        if watching_item:
            watching = True
        if comment_item:
            has_commented = True

    if higher_bid.user == request.user and listing_db.closed:
        listing_db.won_user = True
    else:
        listing_db.won_user = False
    

    return render(request, "auctions/show.html", {
        "listing": listing_db,
        "watching": watching,
        "has_commented": has_commented,
        "comments": comments,
        "actual_price": actual_price
    })


def edit_listing(request, listing):

    listing_db = Listing.objects.get(pk=listing)

    # Auth
    if not request.user.is_authenticated or request.user != listing_db.user:
        return HttpResponseRedirect(reverse("index"))
    

    if request.method == 'POST':

        form = ListingForm(request.POST)

        if form.is_valid():

            if form.cleaned_data['category']:
                category_db = Category.objects.get(pk=form.cleaned_data['category'])
            else:
                category_db = None

            listing_db.title = form.cleaned_data['title']
            listing_db.description = form.cleaned_data['description']
            listing_db.image = form.cleaned_data['image']
            listing_db.price = form.cleaned_data['price']
            listing_db.state = form.cleaned_data['state_change']
            listing_db.category = category_db
            listing_db.updated_at = timezone.now()
            listing_db.save()

            messages.success(request, 'Listing updated successfully!')
            return redirect("show_listing", listing=listing_db.id)
        else:
            return render(request, "auctions/edit.html", {
            "form": form
        })
        
    else:

        form = ListingForm(initial={
            'title': listing_db.title,
            'description': listing_db.description,
            'image': listing_db.image,
            'price': listing_db.price,
            'state_change': listing_db.state,
            'category': listing_db.category_id,
            'id_hidden': listing_db.id
        })


        return render(request, "auctions/edit.html", {
            "form": form,
            "listing_id": listing_db.id
        })
    
def close_listing(request):

    listing = Listing.objects.get(pk=request.POST['listing_id'])

    # Auth
    if not request.user.is_authenticated or request.user != listing.user:
        
        messages.error(request, 'Something went wrong')
        return redirect("index")
    
    listing.updated_at = timezone.now()
    listing.closed = True
    listing.state = False
    listing.save()

    messages.success(request, 'The listing has been closed')
    return redirect("show_listing", listing=listing.id)

    
def your_listings(request):

    # Auth
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    listings = Listing.objects.filter(user=request.user).order_by('-bid_change_at')

    for listing in listings:
        
        higher_bid = Bid.objects.filter(listing = listing).order_by('-amount').first()

        if higher_bid is None:
            listing.actual_price = listing.price
        else:
            listing.actual_price = higher_bid.amount

    return render(request, "auctions/your_listings.html", {
        "listings" : listings
    })

# Add a listing to watchlist
def watch_listing(request):

    # Auth
    if request.user.is_authenticated and request.method == "POST":

        watching = int(request.POST["listing_watch"])

        listing = request.POST["listing_id"]
        user = request.user
        listing = Listing.objects.get(pk=listing)

        if watching:
            # Create item

            user = request.user
            watchlist_item = UserListing(
                user = user,
                listing = listing
            )
            watchlist_item.save()
            messages.success(request, 'Item added to watchlist')
            return redirect("show_listing", listing=listing.id)

        else:
            # Delete item
            watching_item = UserListing.objects.filter(user=user, listing=listing)
            watching_item.delete()

            messages.success(request, 'Item removed from your watchlist')
            return redirect("show_listing", listing=listing.id)

    else:
        messages.error(request, 'Something went wrong')
        return redirect("index")

def watchlist(request):

    # Only active listings are visible

    # Auth
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))

    user_listings_db = UserListing.objects.filter(user=request.user)
    listings = Listing.objects.filter(userlistings__in=user_listings_db).filter(state=True).order_by('-bid_change_at')

    for listing in listings:
        
        higher_bid = Bid.objects.filter(listing = listing).order_by('-amount').first()

        if higher_bid is None:
            listing.actual_price = listing.price
        else:
            listing.actual_price = higher_bid.amount

    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })

def categories_index(request):

    categories = Category.objects.annotate(
        listing_count=Count('listings', filter=Q(listings__state=True))
    ).order_by('title')

    return render(request, "auctions/categories.html", {
        "categories" : categories
    })


def category_show(request, category):
        
    category = Category.objects.get(pk=category)
    listings = category.listings.exclude(state=False).filter().order_by('-created_at')

    for listing in listings:
        
        higher_bid = Bid.objects.filter(listing = listing).order_by('-amount').first()

        if higher_bid is None:
            listing.actual_price = listing.price
        else:
            listing.actual_price = higher_bid.amount

    return render(request, "auctions/show_category.html", {
        "category" : category,
        "listings": listings
    })

def create_comment(request):
    
    # The user who created the listing cannot comment
    # The user who has already commented cannot do so again
    # Closed listings cannot be commented on

    if request.user.is_authenticated and request.method == "POST":

        listing = Listing.objects.get(pk=request.POST['listing_id'])

        new_comment = Comment(
            message = request.POST['comment'],
            user = request.user,
            listing = listing
        )
        new_comment.save()

        messages.success(request, 'Comment added')
        return redirect("show_listing", listing=listing.id)
    
    else:
        return HttpResponseRedirect(reverse("login"))


def your_bids(request):

    # Auth
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))

    # Busco todos los listings cerrados
    closed_listings = Listing.objects.filter(closed=True)
    # Agrego un elemento "bids__amount" a cada uno
    closed_max_bid = closed_listings.annotate(max_bid_amount=Max('bids__amount'))
    # Listing cerrados cuyo Bid más alto coincida con el usuario actual
    won_listings = closed_max_bid.filter(bids__amount=F('max_bid_amount'), bids__user=request.user)

    # Agrego un flag a cada Listing
    for listing in won_listings:
        listing.won = True

    # Busco todos los listings abiertos
    user_open_listings = Listing.objects.filter(state=True)

    # Agrego un elemento "bids__amount" a cada uno
    open_max_bid = user_open_listings.annotate(max_bid_amount=Max('bids__amount'))

    # Listings donde ha participado el usuario
    listings_with_bids = open_max_bid.filter(bids__user=request.user)

    for listing in listings_with_bids:
        # Obtén la puja más alta para este listing
        highest_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()
        
        if highest_bid and highest_bid.user == request.user:
            # El usuario actual tiene la puja más alta en este Listing
            listing.losing = False
        else:
            # El usuario no tiene la puja más alta en este Listing
            listing.losing = True


    # # Agrego todos los listings en un array
    listing_list = []

    for listing in won_listings:
        listing_list.append(listing)

    for listing in listings_with_bids:
        listing_list.append(listing)

    # # Busco el precio actual de cada listing
    for listing in listing_list:
        higher_bid = Bid.objects.filter(listing = listing).order_by('-amount').first()

        if higher_bid is None:
            listing.actual_price = listing.price
        else:
            listing.actual_price = higher_bid.amount

    return render(request, "auctions/your_bids.html", {
        "listings": listing_list
    })


def bid_listing(request):

    if request.user.is_authenticated and request.method == "POST":

        listing = Listing.objects.get(pk=request.POST['listing_id'])
        bid = int(request.POST['bid'])

        # Auth
        if not request.user.is_authenticated or request.user == listing.user or bid > 99999999 or bid < listing.price:

            messages.error(request, 'Your bid is lower than the current price')
            return redirect("show_listing", listing=listing.id)

        # Find actual price
        actual_bid = Bid.objects.filter(listing = listing).order_by('-amount').first()

        if actual_bid is None or bid > int(actual_bid.amount):

            # Delete previous offer
            old_bid = Bid.objects.filter(listing = listing, user = request.user)
            if old_bid:
                old_bid.delete()

            new_bid = Bid(
                amount = bid,
                user = request.user,
                listing = listing
            )

            listing.bid_change_at = timezone.now()
            listing.save()
            new_bid.save()

            return HttpResponseRedirect(reverse("your_bids"))
        else:
            messages.error(request, 'Your bid is lower than the current price')
            return redirect("show_listing", listing=listing.id)
    else:
        return HttpResponseRedirect(reverse("login"))



# Auth
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
