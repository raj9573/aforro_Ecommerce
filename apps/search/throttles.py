from rest_framework.throttling import AnonRateThrottle


class ProductSuggestRateThrottle(AnonRateThrottle):
    scope = "product_suggest"
    
    