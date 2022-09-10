import os                               # os.getenv()
import unittest
import warnings                         # disable some socket warnings
import logging, sys                     # logger for checking failed tests
from datetime import datetime as dt     # for "sorting" test

from wallhaven_api import WallHavenAPI
from wallhaven_api import SORTING


API_KEY = os.getenv("WALLHAVEN_API_KEY")
if not(API_KEY):
    raise Exception("The wallhaven API key is required for this test.")

api = WallHavenAPI(API_KEY)

def get_wallpaper_datetime(date: str):
    return dt.strptime(date, "%Y-%m-%d %H:%M:%S")


class API_Test_Search(unittest.IsolatedAsyncioTestCase):
    # Sometimes tests cause unclosed socket warnings
    # I couldn't beat this yet, maybe something happens in _get_method of the API
    # if you know the issue, please open pull request with possible decision
    def setUp(self):
        warnings.filterwarnings(
            action="ignore",
            message="unclosed",
            category=ResourceWarning)
        return super().setUp()


    async def test_query(self):
        target_query = "pool"
        response = await api.search(q = target_query)
        query = response["meta"]["query"]
        self.assertEqual(query, target_query)


    async def test_categories(self):
        all_categories = ["general", "anime", "people"]
        for category in all_categories:
            response = await api.search(categories=[category])
            wallpapers = response["data"]
            for wallpaper in wallpapers:
                self.assertEqual(wallpaper["category"], category)


    async def test_purity(self):
        all_purity = ["sfw", "sketchy", "nsfw"]
        for purity in all_purity:
            response = await api.search(purity=[purity])
            wallpapers = response["data"]
            for wallpaper in wallpapers:
                self.assertEqual(wallpaper["purity"], purity)


    async def test_sorting_date_added(self):
        target_sorting = "date_added"
        self.assertIn(target_sorting, SORTING)
        response = await api.search(sorting=target_sorting, order="desc")

        wallpapers = response["data"]
        previous_date = get_wallpaper_datetime(wallpapers[0]["created_at"])
        for wallpaper in wallpapers:
            current_wallpaper_date = get_wallpaper_datetime(wallpaper["created_at"])
            self.assertLessEqual(current_wallpaper_date, previous_date)
            previous_date = current_wallpaper_date


    async def test_sorting_views(self):
        target_sorting = "views"
        self.assertIn(target_sorting, SORTING)
        request = await api.search(sorting=target_sorting, order="desc")
        wallpapers = request["data"]

        previous_views = int(wallpapers[0]["views"])
        for wallpaper in wallpapers:
            current_views = int(wallpaper["views"])
            self.assertLessEqual(current_views, previous_views)
            previous_views = current_views


    async def test_sorting_favorites(self):
        target_sorting = "favorites"
        self.assertIn(target_sorting, SORTING)

        request = await api.search(sorting=target_sorting, order="desc")

        wallpapers = request["data"]
        previous_views = int(wallpapers[0][target_sorting])
        for wallpaper in wallpapers:
            current_views = int(wallpaper[target_sorting])
            self.assertLessEqual(current_views, previous_views)
            previous_views = current_views


    async def test_at_least(self):
        target_at_least = "3000x3000"
        request = await api.search(atleast=target_at_least)

        at_least_resolution = target_at_least.split("x")
        at_least_x = at_least_resolution[0]
        at_least_y = at_least_resolution[1]

        wallpapers = request["data"]
        for wallpaper in wallpapers:
            current_resolution = wallpaper["resolution"].split("x")
            current_x = current_resolution[0]
            current_y = current_resolution[1]
            self.assertGreaterEqual(current_x, at_least_x)
            self.assertGreaterEqual(current_y, at_least_y)



    # ------------------------------ #
    #      Manual Test Section       #
    # ------------------------------ #
    # These tests can't be fully verified in some cases
    # some of them are fully random
    # some of just don't have regularity to check
    # so just assume the tests below are ok if we have 200==OK response

    async def test_sorting_toplist(self):
        target_sorting = "toplist"
        self.assertIn(target_sorting, SORTING)
        result = await api.search(sorting=target_sorting)
        self.assertTrue(result)


    async def test_sorting_random(self):
        target_sorting = "random"
        self.assertIn(target_sorting, SORTING)
        result = await api.search(sorting=target_sorting)
        self.assertTrue(result)


    async def test_sorting_relevance(self):
        target_sorting = "relevance"
        self.assertIn(target_sorting, SORTING)
        result = await api.search(sorting=target_sorting)
        self.assertTrue(result)


# TODO:
# 1. add a logging system to check specific tests if the are fail
# logging.getLogger("CLASS_NAME.test_method_name").setLevel(logging.INFO)
# 2. finish remaining tests


if __name__ == "__main__":
    unittest.main()