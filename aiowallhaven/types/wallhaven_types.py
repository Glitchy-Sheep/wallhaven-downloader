import aiowallhaven.types.api_exception_reasons as exception_reasons

from dataclasses import dataclass
from typing import List, Dict, Optional

from aiowallhaven.types.wallhaven_enums import (
    Purity,
    Category,
    TopRange,
    Sorting,
    Order,
    Color,
)


@dataclass
class PurityFilter:
    """
    Object representing a purity filter for wallpapers (sfw, sketchy, nsfw).
    """

    def __init__(self, *active_purities: Purity):
        """
        Initializes a new instance of the PurityFilter class.

        :param active_purities: A set of active purity levels.
        :type active_purities: set[Purity], optional
        """
        if active_purities:
            self.active_purities = set(active_purities)
        else:
            self.active_purities = set()

    def set_purity(self, purity: Purity):
        """
        Sets a specific purity level as active in the filter.

        :param purity: The purity level to set as active.
        :type purity: Purity
        """
        self.active_purities.add(purity)

    def remove_purity(self, purity: Purity):
        """
        Removes a specific purity level from the active purities.

        :param purity: The purity level to remove.
        :type purity: Purity
        """
        self.active_purities.remove(purity)

    def is_purity_active(self, purity: Purity) -> bool:
        """
        Checks if a specific purity level is active in the filter.

        :param purity: The purity level to check.
        :type purity: Purity
        :return: True if the purity level is active, False otherwise.
        :rtype: bool
        """
        return purity in self.active_purities

    def __repr__(self):
        """
        Returns a string representation of the active purities.

        The representation and its order defined by the api.
        Examples of representation:
        'sfw, sketchy, nsfw' = '111'
        'sfw, nsfw' = '101'
        'nsfw' = '001'

        :return: A string representation of the active purities.
        :rtype: str
        """
        # The order of the purities representation is defined by the api.
        rep = str(int(self.is_purity_active(Purity.sfw)))
        rep += str(int(self.is_purity_active(Purity.sketchy)))
        rep += str(int(self.is_purity_active(Purity.nsfw)))
        return rep


@dataclass
class CategoryFilter:
    """
    Object representing category filter (general, anime, people)
    """

    def __init__(self, *active_categories: Category):
        """
        Initializes the 'CategoryFilter' object for future use.

        :param active_categories: Set of active categories. (default is an empty set).
        :type active_categories: set[Category], optional
        """
        if active_categories:
            self.active_categories = set(active_categories)
        else:
            self.active_categories = set()

    def set_category(self, category: Category):
        """
        Sets a category as active.

        :param category: The category to set as active.
        :type category: Category
        """
        self.active_categories.add(category)

    def remove_category(self, category: Category):
        """
        Removes a category from the active categories in the filter.

        :param category: The category to remove.
        """
        self.active_categories.remove(category)

    def is_category_active(self, category: Category) -> bool:
        """
        Checks if a category is active in the filter.

        :param category: The category to check.
        :return: True if the category is active, False otherwise.
        """
        return category in self.active_categories

    def __repr__(self):
        """
        Returns a string representation of the active categories.

        The representation and its order defined by the api.
        Examples of representation:
        'general, anime, people' = '111'
        'general, people' = '101'
        'people' = '001'


        :return: A string representation of the active categories.
        """
        rep = str(int(self.is_category_active(Category.general)))
        rep += str(int(self.is_category_active(Category.anime)))
        rep += str(int(self.is_category_active(Category.people)))
        return rep


@dataclass
class Resolution:
    """
    Object representing picture resolution as x and y (both must be positive).

    Can be represented in resolution format
    (e.g. 1920x1080)

    :raise InvalidResolution: either x or y are negative values
    """

    x: int
    y: int

    @staticmethod
    def from_str(value: str) -> "Resolution":
        """
        Create a Resolution object from a string representation.

        :param value: String representation of the resolution (e.g. "1920x1080")
        :return: Resolution object
        :raise ValueError: Raised when the input value is not in the correct format
        """
        if "x" not in value:
            raise ValueError(f"Invalid resolution format: {value}")
        x, y = map(int, value.split("x", maxsplit=1))
        return Resolution(x, y)

    def __eq__(self, other) -> bool:
        if isinstance(other, Resolution):
            return self.x == other.x and self.y == other.y
        return NotImplemented

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __post_init__(self):
        if self.x <= 0 or self.y <= 0:
            raise ValueError("Both x and y must be positive.")

    def __repr__(self):
        return f"{self.x}x{self.y}"


@dataclass
class Ratio(Resolution):
    """
    Object representing picture ratio as x and y (both must be positive).

    Can be represented in ratio format
    (e.g. 16x9)

    :raise InvalidRatio: either x or y are negative values
    """

    def __post_init__(self):
        if self.x <= 0 or self.y <= 0:
            raise ValueError("Both x and y must be positive.")

    def __repr__(self):
        return f"{self.x}x{self.y}"


@dataclass
class WallpaperTag:
    """
    Represents a wallpaper tag.

    :ivar id: The unique identifier of the tag.
    :ivar name: The name of the tag.
    :ivar alias: The alias of the tag.
    :ivar category_id: The unique identifier of the category.
    :ivar category: The name of the category.
    :ivar purity: The purity of the tag.
    :ivar created_at: The creation date of the tag.
    """

    id: int
    name: str
    alias: str
    category_id: int
    category: str
    purity: Purity
    created_at: str

    @staticmethod
    def from_json(json_data):
        json_data["purity"] = Purity.from_str(json_data["purity"])
        return WallpaperTag(**json_data)


@dataclass
class Uploader:
    """
    Represents an uploader.

    :ivar username: The username of the uploader.
    :ivar group: The group of the uploader.
    :ivar avatar: Represents avatar miniatures of the uploader.
    """

    username: str
    group: str
    avatar: Dict[str, str]


@dataclass
class WallpaperInfo:
    """
    Object representing wallpaper info.

    :ivar id: The unique identifier of the wallpaper.
    :ivar url: The URL of the wallpaper.
    :ivar short_url: The short URL of the wallpaper.
    :ivar views: The number of views of the wallpaper.
    :ivar favorites: The number of favorites of the wallpaper.
    :ivar source: The source of the wallpaper.
    :ivar purity: The purity of the wallpaper.
    :ivar category: The category of the wallpaper.
    :ivar dimension_x: The width of the wallpaper.
    :ivar dimension_y: The height of the wallpaper.
    :ivar resolution: The resolution of the wallpaper.
    :ivar ratio: The ratio of the wallpaper as fraction.
    :ivar file_size: The file size of the wallpaper.
    :ivar file_type: The file type of the wallpaper.
    :ivar created_at: The creation date of the wallpaper.
    :ivar colors: The colors of the wallpaper.
    :ivar path: The path of the wallpaper.
    :ivar thumbs: The thumbs of the wallpaper.

    :ivar uploader: (Optional) The uploader of the wallpaper.
    :ivar tags: (Optional) The tags of the wallpaper.
    """

    id: str
    url: str
    short_url: str

    views: int
    favorites: int
    source: str
    purity: Purity
    category: Category
    dimension_x: int
    dimension_y: int
    resolution: Resolution
    ratio: float
    file_size: int
    file_type: str
    created_at: str
    colors: List[str]
    path: str
    thumbs: str

    uploader: Optional[Uploader] = None
    tags: Optional[List[WallpaperTag]] = None

    @staticmethod
    def from_json(json_data: Dict) -> "WallpaperInfo":
        """
        Create a WallpaperInfo object from a json data.

        :param json_data: The json data from the api about the wallpaper
        :type json_data: Dict

        :return: WallpaperInfo
        """
        # Unpack complex data structures in a special way
        if "uploader" in json_data.keys():
            json_data["uploader"] = Uploader(**json_data["uploader"])
        if "tags" in json_data.keys():
            json_data["tags"] = [
                WallpaperTag.from_json(tag_json_data)
                for tag_json_data in json_data["tags"]
            ]

        json_data["purity"] = Purity.from_str(json_data["purity"])
        json_data["category"] = Category.from_str(json_data["category"])
        json_data["resolution"] = Resolution.from_str(json_data["resolution"])
        json_data["ratio"] = float(json_data["ratio"])
        return WallpaperInfo(**json_data)


@dataclass
class UserCollectionInfo:
    """
    Object representing collection info.

    :ivar id: The unique identifier of the collection.
    :ivar label: The label of the collection.
    :ivar views: The number of views of the collection.
    :ivar count: The number of wallpapers in the collection.
    """

    id: int
    label: str
    views: int
    count: int

    def __str__(self):
        collection_info_str = f"id: {self.id}\n"
        collection_info_str += f"label: {self.label}\n"
        collection_info_str += f"views: {self.views}\n"
        collection_info_str += f"count: {self.count}\n"
        return collection_info_str


@dataclass
class SearchMetaInfo:
    """
    Object representing search meta info.
    Meta info contains information about search results and pagination.

    :ivar query: The search query.
    :ivar seed: The seed which was used for search.

    :ivar current_page: The current page number.
    :ivar last_page: The last page number.
    :ivar per_page: The number of wallpapers per page.
    :ivar total: The total number of wallpapers.
    """

    current_page: int
    last_page: int
    per_page: int
    total: int

    query: Optional[str] = None
    seed: Optional[str] = None


@dataclass
class WallpaperCollection:
    """
    Object representing collection wallpapers info.

    :ivar meta: The meta info about wallpaper collection (pages, total, etc.)
    :ivar wallpapers: The list of wallpapers in the collection and their info
    """

    meta: SearchMetaInfo
    wallpapers: List[WallpaperInfo]

    @staticmethod
    def _get_meta_from_json(json_data: Dict):
        return SearchMetaInfo(**json_data["meta"])

    @staticmethod
    def _get_wallpapers_from_json(json_data):
        wallpapers = []
        for wallpaper_json_data in json_data["data"]:
            wallpaper_info = WallpaperInfo.from_json(wallpaper_json_data)
            wallpapers.append(wallpaper_info)
        return wallpapers

    @staticmethod
    def from_json(json_data) -> "WallpaperCollection":
        """
        Create a WallpaperCollection object from a json data.

        :param json_data: The json data from the api about the wallpaper
        :return: WallpaperCollection
        """
        return WallpaperCollection(
            meta=WallpaperCollection._get_meta_from_json(json_data),
            wallpapers=WallpaperCollection._get_wallpapers_from_json(json_data),
        )


@dataclass
class UserSettings:
    """
    Object representing user settings.
    """

    thumb_size: str
    per_page: int
    purity: PurityFilter
    categories: CategoryFilter
    resolutions: list[Resolution]
    aspect_ratios: list[Ratio]
    toplist_range: TopRange
    tag_blacklist: list[str]
    user_blacklist: list[str]
    ai_art_filter: bool

    @staticmethod
    def from_json(json_data: Dict) -> "UserSettings":
        json_data["per_page"] = int(json_data["per_page"])

        purity_filter = PurityFilter()
        for purity_str in json_data["purity"]:
            purity_filter.set_purity(Purity.from_str(purity_str))

        category_filter = CategoryFilter()
        for category_str in json_data["categories"]:
            category_filter.set_category(Category.from_str(category_str))

        resolutions = []
        for resolution in list(filter(str.isspace, json_data["resolutions"])):
            resolutions.append(Resolution.from_str(resolution))

        ratios = []
        for ratio in list(filter(str.isspace, json_data["aspect_ratios"])):
            ratios.append(Ratio.from_str(ratio))

        json_data["categories"] = category_filter
        json_data["resolutions"] = resolutions
        json_data["aspect_ratios"] = ratios
        json_data["toplist_range"] = TopRange(json_data["toplist_range"])
        json_data["ai_art_filter"] = bool(json_data["ai_art_filter"])

        # Get rid of empty strings in results (just for cleanup)
        json_data["tag_blacklist"] = list(
            filter(str.isspace, json_data["tag_blacklist"])
        )
        json_data["user_blacklist"] = list(
            filter(str.isspace, json_data["user_blacklist"])
        )

        return UserSettings(**json_data)


@dataclass
class SearchFilter:
    """
    Object representing query params.
    """

    category: CategoryFilter = None
    purity: PurityFilter = None
    sorting: Sorting = None
    order: Order = None
    toprange: TopRange = None
    atleast: Resolution = None
    resolutions: list[Resolution] = None
    ratios: list[Ratio] = None
    color: Color = None
    seed: str = None
    ai_art_filter: bool = False  # show by default

    def to_query_params_dict(self):
        query_params = {}

        if self.category:
            query_params["categories"] = str(self.category)

        if self.purity:
            query_params["purity"] = str(self.purity)

        if self.sorting:
            if not isinstance(self.sorting, Sorting):
                raise ValueError(exception_reasons.ValueErrorSorting)
            query_params["sorting"] = self.sorting.value

        if self.order:
            if not isinstance(self.order, Order):
                raise ValueError(exception_reasons.ValueErrorOrder)
            query_params["order"] = self.order.value

        if self.toprange:
            if not isinstance(self.toprange, TopRange):
                raise ValueError(exception_reasons.ValueErrorToprange)
            query_params["toprange"] = self.toprange.value

        if self.atleast:
            if not isinstance(self.atleast, Resolution):
                raise ValueError(exception_reasons.ValueErrorAtleast)
            query_params["atleast"] = str(self.atleast)

        if self.resolutions:
            if not isinstance(self.resolutions, list):
                raise ValueError(exception_reasons.ValueErrorResolutionsFormat)

            for res in self.resolutions:
                if not isinstance(res, Resolution):
                    raise ValueError(exception_reasons.ValueErrorResolutions)

            query_params["resolutions"] = "%2C".join(str(x) for x in self.resolutions)

        if self.ratios:
            if not isinstance(self.ratios, list):
                raise ValueError(exception_reasons.ValueErrorRatiosFormat)

            for rat in self.ratios:
                if not isinstance(rat, Ratio):
                    raise ValueError(exception_reasons.ValueErrorRatios)

            query_params["ratios"] = "%2C".join(str(x) for x in self.ratios)

        if self.color:
            query_params["colors"] = self.color.value

        if self.seed:
            query_params["seed"] = self.seed

        query_params["ai_art_filter"] = str(int(self.ai_art_filter))

        return query_params
