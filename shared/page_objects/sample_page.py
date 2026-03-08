from playwright.async_api import Page, Locator
from .base_page import BasePage

class SamplePage(BasePage):
    async def goto(self):
        await self.page.goto("/sample")

    async def click_button(self) -> None:
        button = self.page.get_by_role("button", name="Submit")
        await button.click()

    async def get_error_message(self) -> Locator:
        return self.page.get_by_role("alert", name="Error")
