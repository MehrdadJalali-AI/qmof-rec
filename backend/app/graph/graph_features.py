def atom_features(site):
    element = site.specie

    atomic_number = float(element.Z)
    atomic_mass = float(element.atomic_mass)
    row = float(element.row)

    group = element.group
    group = float(group) if group is not None else 0.0

    electronegativity = element.X
    electronegativity = float(electronegativity) if electronegativity is not None else 0.0

    return [
        atomic_number,
        atomic_mass,
        row,
        group,
        electronegativity,
    ]