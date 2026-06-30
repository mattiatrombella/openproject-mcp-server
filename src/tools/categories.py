"""Work package category management tools."""

from typing import Optional
from pydantic import BaseModel, Field
from src.server import mcp, get_client
from src.utils.formatting import format_success, format_error


class SetWorkPackageCategoryInput(BaseModel):
    """Input model for setting a work package category."""
    work_package_id: int = Field(..., description="The work package ID", gt=0)
    category_id: Optional[int] = Field(
        None,
        description="The category ID to assign. Pass null/omit to clear the category.",
    )


@mcp.tool
async def list_project_categories(project_id: int) -> str:
    """List all categories available in a project.

    Categories are defined per-project and can be assigned to work packages.
    Use this to discover valid category IDs before setting one on a task.

    Args:
        project_id: The project ID

    Returns:
        List of categories with their IDs and default assignees
    """
    try:
        client = get_client()

        result = await client.get_categories(project_id)
        categories = result.get("_embedded", {}).get("elements", [])

        if not categories:
            return f"No categories found for project #{project_id}."

        text = f"✅ **Categories for Project #{project_id} ({len(categories)}):**\n\n"
        for category in categories:
            text += f"**{category.get('name', 'Unnamed')}** (ID: {category.get('id', 'N/A')})\n"

            default_assignee = category.get("_links", {}).get("defaultAssignee")
            if default_assignee and default_assignee.get("title"):
                text += f"  Default Assignee: {default_assignee['title']}\n"

            text += "\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list categories: {str(e)}")


@mcp.tool
async def get_work_package_category(work_package_id: int) -> str:
    """Get the category currently assigned to a work package.

    Args:
        work_package_id: The work package ID

    Returns:
        The work package's category, or a note if none is set
    """
    try:
        client = get_client()

        wp = await client.get_work_package(work_package_id)
        subject = wp.get("subject", "No title")

        category_link = wp.get("_links", {}).get("category", {})
        href = category_link.get("href") if isinstance(category_link, dict) else None

        text = f"✅ **Category for Work Package #{work_package_id}** ({subject})\n\n"

        if not href:
            text += "No category assigned.\n"
            return text

        category_name = category_link.get("title", "Unknown")
        # href format: /api/v3/categories/{id}
        category_id = href.rstrip("/").split("/")[-1]
        text += f"**Category**: {category_name} (ID: {category_id})\n"

        return text

    except Exception as e:
        return format_error(f"Failed to get work package category: {str(e)}")


@mcp.tool
async def set_work_package_category(input: SetWorkPackageCategoryInput) -> str:
    """Set or clear the category of a work package.

    Pass a category_id to assign that category, or omit/null it to clear the
    current category. Use list_project_categories to find valid category IDs
    for the work package's project.

    Args:
        input: work_package_id and optional category_id (null clears it)

    Returns:
        Success message with the updated category

    Example:
        {"work_package_id": 1234, "category_id": 7}
    """
    try:
        client = get_client()

        # Key presence drives behaviour in update_work_package; always send
        # category_id so None explicitly clears the category.
        result = await client.update_work_package(
            input.work_package_id, {"category_id": input.category_id}
        )

        if input.category_id is None:
            text = format_success(
                f"Category cleared for Work Package #{input.work_package_id}.\n"
            )
            return text

        category_link = result.get("_links", {}).get("category", {})
        category_name = (
            category_link.get("title", "Unknown")
            if isinstance(category_link, dict)
            else "Unknown"
        )

        text = format_success(
            f"Category updated for Work Package #{input.work_package_id}.\n\n"
        )
        text += f"**Category**: {category_name} (ID: {input.category_id})\n"

        return text

    except Exception as e:
        return format_error(f"Failed to set work package category: {str(e)}")
