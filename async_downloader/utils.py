from typing import List, Optional

from aiohttp_socks import ProxyConnector
from fake_useragent import UserAgent


class UserAgentRotator:
    def __init__(
        self,
        generator: Optional[UserAgent] = UserAgent(),
        requests_per_user_agent: Optional[int] = 1,
        change_user_agent: bool = True,
    ):
        self._requests_counter = 0

        self.user_agent_generator = generator
        self._user_agent_str = self.user_agent_generator.random

        self._REQUESTS_PER_USER_AGENT = requests_per_user_agent
        self._CHANGE_USER_AGENT = change_user_agent

    def get_user_agent(self):
        if self._requests_counter == self._REQUESTS_PER_USER_AGENT:
            self._user_agent_str = self.user_agent_generator.random
            self._requests_counter = 0
        self._requests_counter += 1
        return self._user_agent_str


class ProxyConnectorRotator:
    def __init__(
        self,
        proxy_list: List[str],
        change_proxy: Optional[bool] = True,
        requests_per_proxy: Optional[int] = 1,
    ):
        self._proxy_list = proxy_list

        self._REQUEST_PER_PROXY = requests_per_proxy
        self._CHANGE_PROXY = change_proxy

        self._requests_count = 0

        self._proxy_pointer = 0
        self._max_proxy_address_index = len(self._proxy_list) - 1

        self._update_proxy_connector()

    def _update_proxy_connector(self):
        if self._proxy_pointer > self._max_proxy_address_index:
            self._proxy_pointer = 0
        self._proxy_connector = ProxyConnector.from_url(
            self._proxy_list[self._proxy_pointer]
        )

    def get_current_proxy_address(self):
        return self._proxy_list[self._proxy_pointer]

    def get_connector(self):
        if self._requests_count == self._REQUEST_PER_PROXY:
            self._requests_count = 0
            self._proxy_pointer += 1
            if self._CHANGE_PROXY:
                self._update_proxy_connector()

        self._requests_count += 1
        return self._proxy_connector
