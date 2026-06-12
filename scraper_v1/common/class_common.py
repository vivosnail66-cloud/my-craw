#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author :  @fangwangme
Time   :  2023-05-03
Desc   :  
"""

class CategoryTask:
    def __init__(self):
        self.name = ""
        self.url = ""
        self.total = 0
        self.crawled = 0
        self.status = 0

    def __str__(self):
        return (
            f"name: {self.name}\n"
            f"url: {self.url}\n"
            f"total: {self.total}\n"
            f"crawled: {self.crawled}\n"
            f"status: {self.status}\n"
        )

    def to_tuple(self):
        return (self.name, self.url, self.total, self.crawled, self.status)    



class Product:
    def __init__(self):
        self.id = ""
        self.type = ""
        self.sku = ""
        self.name = ""
        self.published = ""
        self.is_featured = ""
        self.visibility_in_catalog = ""
        self.short_description = ""
        self.description = ""
        self.date_sale_price_starts = ""
        self.date_sale_price_ends = ""
        self.tax_status = ""
        self.tax_class = ""
        self.in_stock = ""
        self.stock = ""
        self.low_stock_amount = ""
        self.backorders_allowed = ""
        self.sold_individually = ""
        self.weight = ""
        self.length = ""
        self.width = ""
        self.height = ""
        self.allow_customer_reviews = ""
        self.purchase_note = ""
        self.sale_price = ""
        self.regular_price = ""
        self.categories = ""
        self.tags = ""
        self.shipping_class = ""
        self.images = ""
        self.download_limit = ""
        self.download_expiry_days = ""
        self.parent = ""
        self.grouped_products = ""
        self.upsells = ""
        self.cross_sells = ""
        self.external_url = ""
        self.button_text = ""
        self.position = ""
        self.attribute1_name = ""
        self.attribute1_value = ""
        self.attribute1_visible = ""
        self.attribute1_global = ""
        self.attribute1_default = ""
        self.attribute2_name = ""
        self.attribute2_values = ""
        self.attribute2_visible = ""
        self.attribute2_global = ""
        self.attribute2_default = ""
        self.video_url = ""
        self.scraped_category = ""
        self.url = ""
        self.status = ""

    def __str__(self):
        return (
            f"id: {self.id}\n"
            f"type: {self.type}\n"
            f"sku: {self.sku}\n"
            f"name: {self.name}\n"
            f"published: {self.published}\n"
            f"is_featured: {self.is_featured}\n"
            f"visibility_in_catalog: {self.visibility_in_catalog}\n"
            f"short_description: {self.short_description}\n"
            f"description: {self.description}\n"
            f"date_sale_price_starts: {self.date_sale_price_starts}\n"
            f"date_sale_price_ends: {self.date_sale_price_ends}\n"
            f"tax_status: {self.tax_status}\n"
            f"tax_class: {self.tax_class}\n"
            f"in_stock: {self.in_stock}\n"
            f"stock: {self.stock}\n"
            f"low_stock_amount: {self.low_stock_amount}\n"
            f"backorders_allowed: {self.backorders_allowed}\n"
            f"sold_individually: {self.sold_individually}\n"
            f"weight: {self.weight}\n"
            f"length: {self.length}\n"
            f"width: {self.width}\n"
            f"height: {self.height}\n"
            f"allow_customer_reviews: {self.allow_customer_reviews}\n"
            f"purchase_note: {self.purchase_note}\n"
            f"sale_price: {self.sale_price}\n"
            f"regular_price: {self.regular_price}\n"
            f"categories: {self.categories}\n"
            f"tags: {self.tags}\n"
            f"shipping_class: {self.shipping_class}\n"
            f"images: {self.images}\n"
            f"download_limit: {self.download_limit}\n"
            f"download_expiry_days: {self.download_expiry_days}\n"
            f"parent: {self.parent}\n"
            f"grouped_products: {self.grouped_products}\n"
            f"upsells: {self.upsells}\n"
            f"cross_sells: {self.cross_sells}\n"
            f"external_url: {self.external_url}\n"
            f"button_text: {self.button_text}\n"
            f"position: {self.position}\n"
            f"attribute1_name: {self.attribute1_name}\n"
            f"attribute1_value: {self.attribute1_value}\n"
            f"attribute1_visible: {self.attribute1_visible}\n"
            f"attribute1_global: {self.attribute1_global}\n"
            f"attribute1_default: {self.attribute1_default}\n"
            f"attribute2_name: {self.attribute2_name}\n"
            f"attribute2_values: {self.attribute2_values}\n"
            f"attribute2_visible: {self.attribute2_visible}\n"
            f"attribute2_global: {self.attribute2_global}\n"
            f"attribute2_default: {self.attribute2_default}\n"
            f"video_url: {self.video_url}\n"
            f"scraped_category: {self.scraped_category}\n"
            f"url: {self.url}\n"
            f"status: {self.status}\n"
        )

    def to_listing_tuple(self):
        return (
            self.categories,
            self.name,
            self.url,
            self.status,
        )
    
    def to_detail_tuple(self):
        return (
            self.type,
            self.sku,
            self.name,
            self.visibility_in_catalog,
            self.short_description,
            self.description,
            self.sale_price,
            self.regular_price,
            self.categories,
            self.tags,
            self.images,
            self.parent,
            self.attribute1_name,
            self.attribute1_value,
            self.attribute1_visible,
            self.attribute1_global,
            self.scraped_category,
            self.video_url,
            self.url,
            self.status
        )
    

class Review:
    def __init__(self):
        self.review_id = ""
        self.product_id = ""
        self.product_handle = ""
        self.product_url = ""
        self.title = ""
        self.body = ""
        self.rating = 0
        self.review_date = ""
        self.reviewer_name = ""
        self.reviewer_email = ""
        self.reply = ""
        self.picture_urls = ""
        self.ip_address = ""

    def __str__(self):
        return (
            f"review_id: {self.review_id}\n"
            f"product_id: {self.product_id}\n"
            f"product_handle: {self.product_handle}\n"
            f"product_url: {self.product_url}\n"
            f"title: {self.title}\n"
            f"body: {self.body}\n"
            f"rating: {self.rating}\n"
            f"review_date: {self.review_date}\n"
            f"reviewer_name: {self.reviewer_name}\n"
            f"reviewer_email: {self.reviewer_email}\n"
            f"reply: {self.reply}\n"
            f"picture_urls: {self.picture_urls}\n"
            f"ip_address: {self.ip_address}\n"
        )
    
    def to_tuple(self):
        return (
            self.review_id,
            self.product_id,
            self.product_handle,
            self.product_url,
            self.title,
            self.body,
            self.rating,
            self.review_date,
            self.reviewer_name,
            self.reviewer_email,
            self.reply,
            self.picture_urls,
            self.ip_address,
        )
