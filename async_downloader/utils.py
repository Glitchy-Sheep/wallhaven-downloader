from fake_useragent import UserAgent


class UserAgentProvider:
    """
    User agent provider for
    """

    def __init__(
        self, generator: UserAgent = UserAgent(), requests_per_user_agent: int = 1
    ):
        self.user_agent_generator = generator
        self._requests_count = 0
        self._user_agent_str = self.user_agent_generator.random
        self._REQUESTS_PER_USER_AGENT = requests_per_user_agent

    def generate(self):
        self._requests_count += 1
        if self._requests_count > self._REQUESTS_PER_USER_AGENT:
            self._user_agent_str = self.user_agent_generator.random

        return self._user_agent_str
