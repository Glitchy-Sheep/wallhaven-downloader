from dataclasses import dataclass
from typing import List, Dict, Optional

from aiowallhaven.types.wallhaven_enums import Purity, Category


@dataclass
class PurityFilter:
    """
    Object representing a purity filter for wallpapers (sfw, sketchy, nsfw).
    """

    def __init__(self, active_purities: set[Purity] = None):
        if active_purities:
            self.active_purities = active_purities
        else:
            self.active_purities = set()

    def set_purity(self, purity: Purity):
        self.active_purities.add(purity)

    def remove_purity(self, purity: Purity):
        self.active_purities.remove(purity)

    def is_purity_active(self, purity: Purity) -> bool:
        return purity in self.active_purities

    def __repr__(self):
        rep = str(int(self.is_purity_active(Purity.sfw)))
        rep += str(int(self.is_purity_active(Purity.sketchy)))
        rep += str(int(self.is_purity_active(Purity.nsfw)))
        return rep


@dataclass
class CategoryFilter:
    """
    Object representing category filter (general, anime, people)
    """

    def __init__(self, active_categories: set[Category] = None):
        if active_categories:
            self.active_categories = active_categories
        else:
            self.active_categories = set()

    def set_category(self, category: Category):
        self.active_categories.add(category)

    def remove_category(self, category: Category):
        self.active_categories.remove(category)

    def is_category_active(self, category: Category) -> bool:
        return category in self.active_categories

    def __repr__(self):
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
    id: int
    name: str
    alias: str
    category_id: int
    category: str
    purity: str
    created_at: str


@dataclass
class Uploader:
    username: str
    group: str
    avatar: Dict[str, str]


@dataclass
class WallpaperInfo:
    """
    Object representing wallpaper info.
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
    ratio: Ratio
    file_size: int
    file_type: str
    created_at: str
    colors: List[str]
    path: str
    thumbs: str

    uploader: Optional[Uploader] = None
    tags: Optional[List[WallpaperTag]] = None

    @classmethod
    def from_json(cls, json_data: Dict) -> "WallpaperInfo":
        # Unpack complex data structures in a special way
        if "uploader" in json_data.keys():
            json_data["uploader"] = Uploader(**json_data["uploader"])
        if "tags" in json_data.keys():
            json_data["tags"] = [WallpaperTag(**tag) for tag in json_data["tags"]]

        json_data["purity"] = Purity.from_str(json_data["purity"])
        json_data["category"] = Category.from_str(json_data["category"])
        json_data["resolution"] = Resolution.from_str(json_data["resolution"])
        return cls(**json_data)


@dataclass
class UserCollectionInfo:
    """
    Object representing collection info.
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
    query: str
    seed: str

    current_page: int
    last_page: int
    per_page: int
    total: int


@dataclass
class WallpaperCollection:
    """
    Object representing collection wallpapers info.
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
        return WallpaperCollection(
            meta=WallpaperCollection._get_meta_from_json(json_data),
            wallpapers=WallpaperCollection._get_wallpapers_from_json(json_data),
        )
