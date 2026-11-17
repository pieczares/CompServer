from api.base import Controller


class HealthController(Controller):
    def __init__(self) -> None:
        super().__init__(tags=["Health"])
        self.router.add_api_route("/health", self.health, methods=["GET"])

    def health(self) -> dict:
        return {"status": "ok"}
