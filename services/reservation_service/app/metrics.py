from time import monotonic


class Metrics:
    def __init__(self) -> None:
        self.started_at = monotonic()
        self.reservations_created = 0
        self.reservation_errors = 0
        self.queue_publish_errors = 0

    def prometheus_text(self, service_name: str) -> str:
        uptime = monotonic() - self.started_at
        return "\n".join(
            [
                "# HELP crs_service_uptime_seconds Service uptime in seconds.",
                "# TYPE crs_service_uptime_seconds gauge",
                f'crs_service_uptime_seconds{{service="{service_name}"}} {uptime:.0f}',
                "# HELP crs_reservations_created_total Confirmed reservations created.",
                "# TYPE crs_reservations_created_total counter",
                f"crs_reservations_created_total {self.reservations_created}",
                "# HELP crs_reservation_errors_total Reservation request failures.",
                "# TYPE crs_reservation_errors_total counter",
                f"crs_reservation_errors_total {self.reservation_errors}",
                "# HELP crs_queue_publish_errors_total Queue publish failures.",
                "# TYPE crs_queue_publish_errors_total counter",
                f"crs_queue_publish_errors_total {self.queue_publish_errors}",
                "",
            ]
        )


metrics = Metrics()

