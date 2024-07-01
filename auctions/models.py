from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    pass

class Category(models.Model):
    title = models.CharField(max_length=30)

    def __str__(self):
        return f"Name: {self.title}"

class Listing(models.Model):
    title = models.CharField(max_length=30)
    description = models.CharField(max_length=250)
    image = models.URLField(max_length=200, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    state = models.BooleanField(default=True)
    closed = models.BooleanField(default=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="listings", null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")

    def __str__(self):
        return f"Title: {self.title}, description: {self.description} and initial price: {self.price}, category: {self.category}, state: {self.state}"


# Pivot User - Listing
class UserListing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="userlistings")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="userlistings")

    def __str__(self):
        return f"User: {self.user}, Listing: {self.listing}"

class Bid(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Amount: {self.amount}, User: {self.user}, Listing: {self.listing}"

class Comment(models.Model):
    message = models.CharField(max_length=250)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Comment: {self.message}, user: {self.user}, listing: {self.listing}"


