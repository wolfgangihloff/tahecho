from smolagents import Tool

class GenerateJQLQueryTool(Tool):
    name = "generate_jql_query"
    description = "Generate a JQL query based on user input"
    inputs = {
        "description": {
            "type": "string",
            "description": "Description of the query to generate"
        }
    }
    output_type = "string"
    
    def forward(self, description): 
        """
        Generate a JQL query based on the user's description.
        
        This tool analyzes the user's description and generates an appropriate JQL query.
        It handles various types of queries such as:
        - Finding issues assigned to a specific user
        - Finding issues with a specific status
        - Finding issues in a specific project
        - Finding issues with a specific priority
        - Finding issues created or updated within a specific time frame
        - Combining multiple criteria with AND/OR operators
        
        Args:
            description (str): Description of the query to generate
            
        Returns:
            str: The generated JQL query
        """
        # Convert description to lowercase for easier matching
        description_lower = description.lower()
        
        # Initialize query parts list
        query_parts = []
        
        # Check for common query patterns and add appropriate JQL clauses
        
        # Project
        if "project" in description_lower:
            # Extract project name or key if specified
            if "project:" in description_lower:
                # Try to extract project name/key after "project:"
                parts = description_lower.split("project:")
                if len(parts) > 1:
                    project_part = parts[1].strip().split()[0]
                    query_parts.append(f"project = {project_part}")
                else:
                    query_parts.append("project = currentProject()")
            else:
                query_parts.append("project = currentProject()")
        
        # Assignee
        if "assigned to me" in description_lower or "my issues" in description_lower:
            query_parts.append("assignee = currentUser()")
        elif "assigned" in description_lower and "to" in description_lower:
            # Try to extract assignee name
            idx_assigned = description_lower.find("assigned")
            idx_to = description_lower.find("to", idx_assigned)
            if idx_to > idx_assigned:
                assignee = description_lower[idx_to + 2:].strip().split()[0]
                query_parts.append(f"assignee = '{assignee}'")
        elif "unassigned" in description_lower:
            query_parts.append("assignee is EMPTY")
        
        # Status
        status_keywords = {
            "open": "status = 'Open'",
            "in progress": "status = 'In Progress'",
            "done": "status = 'Done'",
            "closed": "status = 'Closed'",
            "resolved": "status = 'Resolved'",
            "to do": "status = 'To Do'"
        }
        
        for keyword, clause in status_keywords.items():
            if keyword in description_lower:
                query_parts.append(clause)
                break
        
        # Priority
        priority_keywords = {
            "highest": "priority = Highest",
            "high": "priority = High",
            "medium": "priority = Medium",
            "low": "priority = Low",
            "lowest": "priority = Lowest"
        }
        
        for keyword, clause in priority_keywords.items():
            if keyword in description_lower and "priority" in description_lower:
                query_parts.append(clause)
                break
        
        # Issue type
        issue_types = {
            "bug": "issuetype = Bug",
            "task": "issuetype = Task",
            "story": "issuetype = Story",
            "epic": "issuetype = Epic"
        }
        
        for keyword, clause in issue_types.items():
            if keyword in description_lower:
                query_parts.append(clause)
                break
        
        # Time-based queries
        if "created today" in description_lower:
            query_parts.append("created >= startOfDay()")
        elif "created yesterday" in description_lower:
            query_parts.append("created >= startOfDay(-1) AND created <= endOfDay(-1)")
        elif "created this week" in description_lower:
            query_parts.append("created >= startOfWeek()")
        elif "created last week" in description_lower:
            query_parts.append("created >= startOfWeek(-1) AND created <= endOfWeek(-1)")
        
        if "updated today" in description_lower:
            query_parts.append("updated >= startOfDay()")
        elif "updated yesterday" in description_lower:
            query_parts.append("updated >= startOfDay(-1) AND updated <= endOfDay(-1)")
        elif "updated this week" in description_lower:
            query_parts.append("updated >= startOfWeek()")
        elif "updated last week" in description_lower:
            query_parts.append("updated >= startOfWeek(-1) AND updated <= endOfWeek(-1)")
        
        # Text search
        if "contains" in description_lower:
            idx_contains = description_lower.find("contains")
            text = description_lower[idx_contains + 8:].strip().split()[0]
            query_parts.append(f"text ~ '{text}'")
        
        # If no specific criteria were found, return a default query
        if not query_parts:
            return "project = currentProject() ORDER BY created DESC"
        
        # Combine all query parts with AND operator
        jql_query = " AND ".join(query_parts)
        
        # Add default sorting if not specified
        if "order by" not in description_lower:
            jql_query += " ORDER BY created DESC"
        
        return jql_query
