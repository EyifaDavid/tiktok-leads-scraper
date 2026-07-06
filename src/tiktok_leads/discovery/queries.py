"""Default search queries, hashtags, and bio keywords for lead discovery.

All lists can be overridden via Settings (environment variables).
Users should customize these for their target industry/niche.
"""

# Search queries for TikTok user search
SEARCH_QUERIES = [
    # Primary logistics terms
    "logistics company",
    "freight forwarder",
    "shipping agent",
    "cargo company",
    "freight company",
    
    # Regional variations
    "international shipping",
    "ocean freight",
    "air freight",
    "customs broker",
    "customs clearance",
    
    # Service-specific
    "warehousing",
    "supply chain",
    "last mile delivery",
    "express delivery",
    "courier service",
    
    # Industry-specific
    "trucking company",
    "truck logistics",
    "container shipping",
    "FCL shipping",
    "LCL shipping",
    
    # Location-based (expand as needed)
    "freight forwarder USA",
    "logistics UK",
    "shipping company Dubai",
    "freight China",
    
    # B2B focused
    "B2B logistics",
    "commercial shipping",
    "business freight",
    "enterprise logistics",
]

# Hashtags to scrape for discovering companies
HASHTAGS = [
    # Primary logistics hashtags
    "logistics",
    "freightforwarding",
    "shipping",
    "supplychain",
    "cargo",
    
    # Industry hashtags
    "trucking",
    "warehousing",
    "customs",
    "importexport",
    "globaltrade",
    
    # Business hashtags
    "b2b",
    "logisticslife",
    "freightbroker",
    "shippinglife",
    
    # Service-specific
    "lastmile",
    "fulfillment",
    "3pl",
    "ecommercelogistics",
]

# Bio keywords to identify relevant accounts (alias: INCLUDE_KEYWORDS)
BIO_KEYWORDS = [
    # Company indicators
    "logistics",
    "freight",
    "shipping",
    "cargo",
    "forwarder",
    "carrier",
    
    # Service indicators
    "transportation",
    "delivery",
    "courier",
    "express",
    "haulage",
    
    # Business type
    "b2b",
    "wholesale",
    "distribution",
    "supply chain",
    "warehousing",
    
    # International
    "international",
    "global",
    "worldwide",
    "overseas",
    "cross-border",
]

# Exclude keywords to filter out irrelevant accounts
EXCLUDE_KEYWORDS = [
    "personal",
    "vlog",
    "entertainment",
    "music",
    "dance",
    "comedy",
    "influencer",
    "lifestyle",
    "fashion",
    "beauty",
]

# Alias for compatibility
INCLUDE_KEYWORDS = BIO_KEYWORDS
