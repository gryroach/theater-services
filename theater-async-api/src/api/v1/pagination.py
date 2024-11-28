from fastapi import Query


class PaginationParams:
    def __init__(
        self,
        page_size: int = Query(default=10, ge=1, le=50),
        page_number: int = Query(default=1, ge=1),
    ):
        self.page_size = page_size
        self.page_number = page_number
