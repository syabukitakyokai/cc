from .importers.base import CardImporter
from .importers.rakuten import RakutenImporter
from .importers.vpass import VpassImporter


IMPORTER_TYPES: dict[
    str,
    type[CardImporter],
] = {
    "rakuten": RakutenImporter,
    "vpass": VpassImporter,
}


def create_importer(
    importer_name: str,
) -> CardImporter:
    try:
        importer_type = IMPORTER_TYPES[
            importer_name
        ]

    except KeyError as error:
        supported_importers = ", ".join(
            sorted(IMPORTER_TYPES)
        )

        raise ValueError(
            f"Unknown importer: {importer_name}. "
            f"Supported importers: "
            f"{supported_importers}"
        ) from error

    return importer_type()