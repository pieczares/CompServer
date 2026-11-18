from api.controller import Controller
from api.health_controller import HealthController
from api.produkty_controller import ProduktyController
from core.database import Database
from core.settings import Settings
from job_scheduler import JobScheduler
from services.product_link_service import ProductLinkService
from services.product_scraper import ProductScraper
from tasks.refresh_product_links_task import RefreshProductLinksTask
from tasks.refresh_products_task import RefreshProductsTask


class Container:
    """Jedyne miejsce, w którym składane są zależności aplikacji."""

    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings = settings
        self.database = database

        link_service = ProductLinkService(
            threads=settings.http_threads,
            page_limit=settings.crawl_page_limit,
        )
        scraper = ProductScraper(threads=settings.http_threads)

        self.scheduler = JobScheduler(
            settings=settings,
            links_task=RefreshProductLinksTask(database.session_factory, link_service),
            products_task=RefreshProductsTask(database.session_factory, scraper, settings.products_links_limit),
        )

        self.controllers: list[Controller] = [
            HealthController(),
            ProduktyController(database.session_factory),
        ]
