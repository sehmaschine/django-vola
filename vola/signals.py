# coding: utf-8

# DJANGO IMPORTS
from django.dispatch import Signal

# create preview signals
vola_pre_create_preview = Signal(providing_args=["container"])
vola_post_create_preview = Signal(providing_args=["container"])

# transfer preview signals
vola_pre_transfer_preview = Signal(providing_args=["container"])
vola_post_transfer_preview = Signal(providing_args=["container"])
