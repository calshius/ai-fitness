def format_output(response):
    """Format the LLM response for better readability"""
    # Check if response is an error message
    if response.startswith("Error:"):
        return response

    # Split the response into sections
    sections = {"OBSERVATIONS": "", "DIETARY SUGGESTIONS": "", "SUMMARY": ""}

    current_section = None
    lines = response.split("\n")

    for line in lines:
        # Check if line contains a section header
        for section in sections.keys():
            if section in line.upper():
                current_section = section
                break

        # Add line to current section if we're in a section
        if current_section:
            sections[current_section] += line + "\n"

    # Format the output with colors and styling
    formatted_output = ""

    # If the response doesn't have our expected structure, return it as is
    if all(v == "" for v in sections.values()):
        return response

    # Format each section
    for section, content in sections.items():
        if content:
            # Add section header with styling
            formatted_output += f"\n\033[1;36m{section}\033[0m\n"
            formatted_output += "=" * len(section) + "\n"

            # Add section content with bullet points highlighted
            for line in content.split("\n"):
                if line.strip().startswith("-"):
                    # Highlight bullet points
                    formatted_output += f"\033[1;33m{line}\033[0m\n"
                elif line.strip().startswith("•"):
                    # Highlight bullet points (alternative symbol)
                    formatted_output += f"\033[1;33m{line}\033[0m\n"
                else:
                    formatted_output += line + "\n"

    return formatted_output
