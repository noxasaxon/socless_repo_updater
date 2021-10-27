from copy import deepcopy


def update_package_json_contents(
    package_json: dict,
    pj_deps: dict,
    pj_replace_only: bool = True,
) -> dict:
    new_package_json = deepcopy(package_json)
    for name, version in pj_deps.items():
        if name not in new_package_json["dependencies"] and pj_replace_only:
            print(f"Skipping {name}. {name} not in dependencies and replace_only=True")
        else:
            new_package_json["dependencies"][name] = version
    return new_package_json
