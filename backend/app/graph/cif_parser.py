import os
import tempfile

from pymatgen.core import Structure


def parse_cif_bytes(cif_bytes: bytes, filename: str = "uploaded.cif") -> Structure:
    with tempfile.TemporaryDirectory() as tmpdir:
        cif_path = os.path.join(tmpdir, filename)

        with open(cif_path, "wb") as f:
            f.write(cif_bytes)

        structure = Structure.from_file(cif_path)

    return structure