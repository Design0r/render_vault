import sys
import time
from pathlib import Path

from . import Logger


def take_screenshot(path: Path, geometry: tuple[int, int, int, int]) -> None:
    import mss.tools
    from PIL import Image

    x, y, w, h = geometry

    with mss.mss() as sct:
        monitor = {
            "top": y,
            "left": x,
            "width": w,
            "height": h,
        }

        sct_img = sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        img.resize((350, 350)).save(path, "JPEG")

        Logger.info(f"Saved Screenshot in {path}")


def create_sdr_preview(hdri_path: Path, thumbnail_path: Path, size: int):
    if not hdri_path.is_file() or thumbnail_path.exists():
        return thumbnail_path

    try:
        import rust_thumbnails

        if hdri_path.suffix == ".hdr":
            rust_thumbnails.hdr_to_jpg(
                str(hdri_path), str(thumbnail_path), size, size // 2
            )
            time.sleep(0.1)
            return
        elif hdri_path.suffix == ".exr":
            if sys.platform == "darwin":
                rust_thumbnails.exr_to_jpg(
                    str(hdri_path), str(thumbnail_path), size, size // 2
                )
                return

            import cv2
            import imageio
            import numpy as np

            imageio.plugins.freeimage.download()
            image = imageio.imread(hdri_path, format="EXR-FI")[:, :, :3]
        else:
            return

        res_img = cv2.resize(image, (size, size // 2), interpolation=cv2.INTER_LINEAR)
        tonemapped_image = reinhard_tonemap(res_img)
        gamma_corrected = np.power(tonemapped_image, 1.0 / 2.2)
        jpg_image = np.clip(gamma_corrected * 255, 0, 255).astype(np.uint8)

        imageio.imwrite(thumbnail_path, jpg_image, format="jpg")  # type: ignore

    except Exception as e:
        Logger.exception(e)


def reinhard_tonemap(img, exposure=1.0, white=1.0):
    return img * (1.0 + (img / (white**2))) / (1.0 + img)
