from PIL import Image

from cad_image_cropper.exceptions import InvalidImageError
from cad_image_cropper.models.crop_region import CropRegion


class ImageCropper:
    def crop_image(self, image: Image.Image, region: CropRegion) -> Image.Image:
        try:
            box = self._build_crop_box(region)
            return image.crop(box)
        except Exception as exc:
            raise InvalidImageError(
                f"Failed to crop image: {exc}",
                image.filename if hasattr(image, "filename") else None,  # type: ignore[arg-type]
            ) from exc

    def _build_crop_box(self, region: CropRegion) -> tuple[int, int, int, int]:
        return (region.x_start, region.y_start, region.x_end, region.y_end)
