import json
import os

from pymatgen.core import Structure

# ------Settings------#
struct_json_path = "../qmof_structure_data.json"
cif_folder_path = "../relaxed_structures"
write_site_props = True
only_ddec_charge = False
# ------Settings------#

# Make folder to store CIFs
os.makedirs(cif_folder_path, exist_ok=True)

# Read in structure data
with open(struct_json_path, "r") as f:
    qmof_struct_data = json.load(f)

# Loop over structures and write each one out to a CIF
for entry in qmof_struct_data:
    qmof_id = entry["qmof_id"]
    print(f"Writing {qmof_id}")

    struct = Structure.from_dict(entry["structure"])

    cif_path = os.path.join(cif_folder_path, f"{qmof_id}.cif")
    struct.to(filename=cif_path)

    properties = dict(sorted(struct.site_properties.items()))

    # Skip property writing if no site properties exist
    if write_site_props and len(properties) == 0:
        continue

    # Overwrite CIF with site properties
    if write_site_props:
        new_cif = ""
        i = 0
        prop_lines = False

        with open(cif_path, "r") as f:
            for line in f:
                if "_atom_site_occupancy" in line:
                    new_cif += line

                    if only_ddec_charge:
                        if "pbe_ddec_charge" not in properties:
                            print(f"Skipping charge for {qmof_id}: pbe_ddec_charge missing")
                            break
                        new_cif += " _atom_site_charge\n"
                    else:
                        for key in properties.keys():
                            new_cif += f" _atom_site_{key}\n"

                    prop_lines = True
                    continue

                if i == len(struct):
                    prop_lines = False

                if prop_lines:
                    new_cif += line.strip()

                    if only_ddec_charge:
                        new_cif += f"  {properties['pbe_ddec_charge'][i]}"
                    else:
                        for value_sets in properties.values():
                            new_cif += f"  {value_sets[i]}"

                    new_cif += "\n"
                    i += 1
                else:
                    new_cif += line

        with open(cif_path, "w") as f:
            f.write(new_cif)

print("CIF generation completed.")