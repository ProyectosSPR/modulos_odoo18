ALLOWED_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/gif",
    "image/webp",
    "image/bmp",
    "image/svg+xml",
    "image/tiff",
}


def is_image_mimetype(mimetype: str) -> bool:
    return mimetype in ALLOWED_IMAGE_TYPES
