from .hybrid_search import search
import sqlite3


def find_indices(primary_list, query_list):
    """
    Find the indices of elements from query_list in primary_list.

    Args:
        primary_list (list): The list to search in
        query_list (list): The list of elements to search for

    Returns:
        list: A list of indices where query elements are found in primary list
    """
    indices = []
    for query_item in query_list:
        try:
            index = primary_list.index(query_item)
            indices.append(index)
        except ValueError:
            pass
    return indices


conn = sqlite3.connect('backend/database/tools.db')
cursor = conn.cursor()

descriptions = []
cursor.execute("SELECT * FROM tools")
tools = cursor.fetchall()
for row in tools:
    text = f"{row[0]} {row[1]}"
    descriptions.append(text.lower())

# Commit changes and close connection
conn.commit()
conn.close()


def search_tool(query):
    """
    Searches for tools based on a query and returns the matching tool data
    in RRF-optimal order.

    Args:
        query (str): The search query string.

    Returns:
        list: A list of tuples, where each tuple represents a matching tool's data
              (name, description, url).
    """
    # Find matching tool descriptions based on the query (returned in RRF order)
    matching_descriptions = search(descriptions, query.lower())

    # Find the indices of these matching descriptions in the main descriptions list
    matching_indices = find_indices(descriptions, matching_descriptions)

    # Collect the full tool data for each matching index (preserving RRF order)
    matching_tools_data = []
    for index in matching_indices:
        matching_tools_data.append(tools[index])

    return matching_tools_data
