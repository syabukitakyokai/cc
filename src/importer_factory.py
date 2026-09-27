from .importers.base import CardImporter
from .importers.rakuten import RakutenImporter
from .importers.vpass import VpassImporter
from .importers.epos import EposImporter
from .importers.nicos import NicosImporter
from .importers.saison import SaisonImporter
from .importers.jcb import JcbImporter
from .importers.view import ViewImporter



IMPORTER_TYPES: dict[
    str,
    type[CardImporter],
] = {
    "rakuten": RakutenImporter,
    "vpass": VpassImporter,
    "epos": EposImporter,
    "nicos": NicosImporter,
    "saison": SaisonImporter,
    "jcb": JcbImporter,
    "view": ViewImporter,
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