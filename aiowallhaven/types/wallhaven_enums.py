from enum import Enum


class Purity(Enum):
    nsfw = 0
    sketchy = 1
    sfw = 2

    @staticmethod
    def from_str(value: str) -> "Purity":
        return getattr(Purity, value.lower())


class Category(Enum):
    general = 0
    anime = 1
    people = 2

    @staticmethod
    def from_str(value: str) -> "Category":
        return getattr(Category, value.lower())


class Sorting(Enum):
    date_added = "date_added"
    relevance = "relevance"
    random = "random"
    views = "views"
    favorites = "favorites"
    toplist = "toplist"


class Order(Enum):
    # desc used by default
    desc = "desc"
    asc = "asc"


class TopRange(Enum):
    one_day = "1d"
    three_days = "3d"
    one_week = "1w"
    one_month = "1M"
    three_months = "3M"
    six_months = "6M"
    one_year = "1y"


class Color(Enum):
    # Color names from http://chir.ag/projects/name-that-color
    lonestar = "660000"
    red_berry = "990000"
    guardsman_red = "cc0000"
    persian_red = "cc3333"
    french_rose = "ea4c88"
    plum = "993399"
    royal_purple = "663399"
    sapphire = "333399"
    science_blue = "0066cc"
    pacific_blue = "0099cc"
    downy = "66cccc"
    atlantis = "77cc33"
    limeade = "669900"
    verdun_green = "336600"
    verdun_green_2 = "666600"
    olive = "999900"
    earls_green = "cccc33"
    yellow = "ffff00"
    sunglow = "ffcc33"
    orange_peel = "ff9900"
    blaze_orange = "ff6600"
    tuscany = "cc6633"
    potters_clay = "996633"
    nutmeg_wood_finish = "663300"
    black = "000000"
    dusty_gray = "999999"
    silver = "cccccc"
    white = "ffffff"
    gun_powder = "424153"
