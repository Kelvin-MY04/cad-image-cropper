from dataclasses import dataclass


@dataclass(frozen=True)
class CropRegion:
    x_start: int
    x_end: int
    y_start: int
    y_end: int

    def __post_init__(self) -> None:
        if self.x_end <= self.x_start:
            raise ValueError(
                f"x_end ({self.x_end}) must be > x_start ({self.x_start})"
            )
        if self.y_end <= self.y_start:
            raise ValueError(
                f"y_end ({self.y_end}) must be > y_start ({self.y_start})"
            )
