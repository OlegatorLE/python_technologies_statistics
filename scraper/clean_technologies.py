def clean_technologies(tech_list) -> list:
    """
    Cleans up the technology list by removing duplicates and variations,
    and retaining only unique technology names.

    :param tech_list: List of technology names
    :return: A cleaned list of unique technology names
    """
    # Normalize the technology names by lowercasing and stripping spaces
    normalized_techs = set(tech.strip().lower() for tech in tech_list)

    # Dictionary to map variations to a standard name
    standardization_dict = {
        "postgresql": "postgres",
        "fastapi": "fast api",
        "python3": "python",
        "react.js": "react",
        "aws services": "aws",
        "javascript": "js",
    }

    # Replace variations with standard names
    cleaned_techs = set(
        standardization_dict.get(tech, tech) for tech in
        normalized_techs)

    # Return the cleaned list sorted alphabetically
    return sorted(cleaned_techs)
