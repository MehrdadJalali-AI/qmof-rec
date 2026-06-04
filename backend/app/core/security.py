def validate_file_extension(filename: str, allowed_extensions: list[str]) -> bool:
    return any(filename.lower().endswith(ext) for ext in allowed_extensions)