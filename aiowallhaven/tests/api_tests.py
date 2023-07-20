import os
import unittest
import warnings  # disable some socket warnings
from datetime import datetime as dt  # for "sorting" test

from aiowallhaven.api import WallHavenAPI
from aiowallhaven.types.wallhaven_enums import Category
from aiowallhaven.types.wallhaven_types import (
    Ratio,
    Resolution,
    Sorting,
    TopRange,
    Order,
    Color,
    Purity,
    CategoryFilter,
    SearchFilter,
    PurityFilter,
    UserCollectionInfo,
    WallpaperTag,
    UserSettings,
    WallpaperCollection,
    WallpaperInfo,
)

API_KEY = os.getenv("WALLHAVEN_API_KEY")
if not API_KEY:
    raise PermissionError("The wallhaven API key is required for this test.")

api = WallHavenAPI(API_KEY)


def get_wallpaper_datetime(date: str):
    return dt.strptime(date, "%Y-%m-%d %H:%M:%S")


class ApiTestSearch(unittest.IsolatedAsyncioTestCase):
    # Sometimes tests cause unclosed socket warnings
    # I couldn't beat this yet, maybe something happens in _get_method of the API
    # if you know the issue, please open pull request with possible decision
    def setUp(self):
        warnings.filterwarnings(
            action="ignore", message="unclosed", category=ResourceWarning
        )
        return super().setUp()

    async def test_query(self):
        target_query = "pool"
        response = await api.search(query=target_query)
        query = response.meta.query
        self.assertEqual(query, target_query)

    async def test_categories(self):
        all_categories = [Category.general, Category.anime, Category.people]

        for test_category in all_categories:
            search_filter = SearchFilter(
                category=CategoryFilter(test_category),
            )

            response = await api.search(search_filter=search_filter)
            for wallpaper in response.wallpapers:
                self.assertEqual(wallpaper.category, test_category)

    async def test_purity(self):
        all_purity = [Purity.sfw, Purity.sketchy, Purity.nsfw]

        for purity in all_purity:
            search_filter = SearchFilter(purity=PurityFilter(purity))
            response = await api.search(search_filter=search_filter)
            for wallpaper in response.wallpapers:
                self.assertEqual(wallpaper.purity, purity)

    async def test_sorting_date_added(self):
        target_sorting = Sorting.date_added
        target_order = Order.desc
        search_filter = SearchFilter(sorting=target_sorting, order=target_order)
        response = await api.search(search_filter=search_filter)

        previous_date = get_wallpaper_datetime(response.wallpapers[0].created_at)
        for wallpaper in response.wallpapers:
            current_wallpaper_date = get_wallpaper_datetime(wallpaper.created_at)
            self.assertLessEqual(current_wallpaper_date, previous_date)
            previous_date = current_wallpaper_date

    async def test_sorting_views(self):
        target_sorting = Sorting.views
        target_order = Order.desc
        search_filter = SearchFilter(sorting=target_sorting, order=target_order)
        response = await api.search(search_filter=search_filter)

        previous_views = int(response.wallpapers[0].views)
        for wallpaper in response.wallpapers:
            current_views = int(wallpaper.views)
            self.assertLessEqual(current_views, previous_views)
            previous_views = current_views

    async def test_sorting_random(self):
        target_sorting = Sorting.random
        search_filter = SearchFilter(sorting=target_sorting)
        result = await api.search(search_filter=search_filter)
        self.assertIsNotNone(result.meta.seed)  # random set seed

    async def test_sorting_favorites(self):
        target_sorting = Sorting.favorites
        target_order = Order.desc
        search_filter = SearchFilter(sorting=target_sorting, order=target_order)
        response = await api.search(search_filter=search_filter)

        previous_favorites = int(response.wallpapers[0].favorites)
        for wallpaper in response.wallpapers:
            current_favorites = int(wallpaper.favorites)
            self.assertLessEqual(current_favorites, previous_favorites)
            previous_favorites = current_favorites

    async def test_at_least(self):
        target_at_least = Resolution(3000, 3000)
        search_filter = SearchFilter(atleast=target_at_least)
        response = await api.search(search_filter=search_filter)

        for wallpaper in response.wallpapers:
            current_x = wallpaper.dimension_x
            current_y = wallpaper.dimension_y
            self.assertGreaterEqual(int(current_x), int(target_at_least.x))
            self.assertGreaterEqual(int(current_y), int(target_at_least.y))

    async def test_resolution(self):
        target_resolution = [Resolution(1920, 1080)]
        search_filter = SearchFilter(resolutions=target_resolution)
        response = await api.search(search_filter=search_filter)

        for wallpaper in response.wallpapers:
            self.assertEqual(wallpaper.resolution, target_resolution[0])

    async def test_ratios(self):
        target_ratio = Ratio(1, 1)
        search_filter = SearchFilter(ratios=[target_ratio])
        response = await api.search(search_filter=search_filter)

        for wallpaper in response.wallpapers:
            self.assertEqual(target_ratio.x / target_ratio.y, wallpaper.ratio)

    async def test_color(self):
        target_color = Color.black
        search_filter = SearchFilter(color=target_color)
        response = await api.search(search_filter=search_filter)

        for wallpaper in response.wallpapers:
            self.assertIn("#" + target_color.value, wallpaper.colors)

    async def test_page(self):
        target_page = 2
        search_filter = SearchFilter(page=target_page)
        response = await api.search(query="anime", search_filter=search_filter)
        self.assertEqual(target_page, int(response.meta.current_page))

    # ------------------------------ #
    #      Manual Test Section       #
    # ------------------------------ #
    # These tests can't be fully verified in some cases
    # some of them are fully random
    # some of just don't have regularity to check
    # so just assume the tests below are ok if we have 200==OK response

    async def test_sorting_toplist(self):
        target_sorting = Sorting.toplist
        search_filter = SearchFilter(sorting=target_sorting)
        response = await api.search(search_filter=search_filter)
        self.assertIsNot(response.wallpapers, [])

    async def test_sorting_relevance(self):
        target_sorting = Sorting.relevance
        search_filter = SearchFilter(sorting=target_sorting)
        response = await api.search(search_filter=search_filter)
        self.assertIsNot(response.wallpapers, [])

    async def test_toprange(self):
        target_toprange = TopRange.one_day
        search_filter = SearchFilter(toprange=target_toprange)
        response = await api.search("anime", search_filter=search_filter)
        self.assertIsNot(response.wallpapers, [])

    # Something is completely wrong with seed values
    # it seems that API just ignores it, because different seeds
    # give same page of wallpapers (even with sorting=random)
    async def test_seed(self):
        target_seed = "abc123"
        search_filter = SearchFilter(seed=target_seed)
        response = await api.search(search_filter=search_filter)
        self.assertIsNot(response.wallpapers, [])


class ApiTestGet(unittest.IsolatedAsyncioTestCase):
    # Sometimes tests cause unclosed socket warnings
    # I couldn't beat this yet, maybe something happens in _get_method of the API
    # if you know the issue, please open pull request with possible decision
    def setUp(self):
        warnings.filterwarnings(
            action="ignore", message="unclosed", category=ResourceWarning
        )
        return super().setUp()

    async def test_get_collections(self):
        username = "Raylz"
        response = await api.get_user_collections_list(username)
        for collection in response:
            self.assertIsInstance(collection, UserCollectionInfo)

    async def test_get_tag(self):
        tag = await api.get_tag(1)
        self.assertIsInstance(tag, WallpaperTag)
        self.assertIsNotNone(tag.name)

    async def test_get_settings(self):
        settings = await api.my_settings()
        self.assertIsInstance(settings, UserSettings)

    async def test_get_user_uploads(self):
        uploads_collection = await api.get_user_uploads("provip")
        self.assertIsInstance(uploads_collection, WallpaperCollection)

    async def test_get_wallpaper(self):
        test_wallpaper_id = "e7jj6r"
        wallpaper = await api.get_wallpaper(test_wallpaper_id)
        self.assertIsInstance(wallpaper, WallpaperInfo)
        self.assertEqual(wallpaper.id, test_wallpaper_id)
        self.assertIsNotNone(wallpaper.path)


if __name__ == "__main__":
    unittest.main()
