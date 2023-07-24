# --------- Network Errors ----------

NotFoundError = """
    The requested resource was not found.
"""

TooManyRequests = """
    Too many requests to the server, please try again later
"""

Unauthorized = """
    Invalid API key. Please provide a valid API key.
    You can regenerate your API key at https://wallhaven.cc/settings/account
"""

GeneralError = """
    The request to open {session} failed with the following HTTP code:
    {status_code}
"""

# --------- Value Errors ----------

ValueErrorPurity = """
    Invalid purity filter was provided: {purity}
    Valid formats: PurityFilter(Purity.sfw, Purity.sketchy...)
"""

ValueErrorCategory = """
    Invalid category filter was provided: {category}
    Valid formats: CategoryFilter(Category.sfw, Category.nsfw...)
"""

ValueErrorSorting = """
    Invalid parameter was provided. 
    Only "date_added", "relevance", "random", "favorites", "toplist" 
    are considered to be valid arguments.
"""

ValueErrorOrder = """
    Invalid order method was provided. 
    Only 'desc' and 'asc' are considered to be valid arguments.
"""

ValueErrorToprange = """
    Invalid parameter was provided. 
    Only "1d", "3d", "1w", "1M", "3M", "6M", "1y" are considered to be valid arguments.
"""

ValueErrorAtleast = """
    Invalid screen resolution was provided. 
    Valid formats: Resolution(1920, 1080), Resolution(3080, 2140)
"""

ValueErrorResolutions = """
    Invalid resolution was provided: '{resolution}' in resolutions list {resolutions_list}.
    Valid format: [Resolution(1920, 1080), Resolution(2560x1600)]
"""

ValueErrorResolutionsFormat = """
    The argument should be a list of resolutions.
    Valid format: [Resolution(1920, 1080), Resolution(2560x1600)]. 
"""

ValueErrorRatios = """
    The provided ratio is incorrect. 
    Example of a valid format: Ratio(16, 9)
"""

ValueErrorRatiosFormat = """
    The argument should be a list of ratios.
    Valid format: [Ratio(16, 9), Ratio(16, 10)]. 
"""

ValueErrorId = """
    The provided id is incorrect.
    Id should be an integer. Example: 999777 
"""
