from typing import Optional
from py2neo import Graph
from config import CONFIG
import logging

logger = logging.getLogger(__name__)

class GraphDBManager:
    """Manages optional graph database connections."""
    
    def __init__(self):
        self.graph: Optional[Graph] = None
        self.is_connected = False
        
    def connect(self) -> bool:
        """Attempt to connect to the graph database."""
        if not CONFIG["GRAPH_DB_ENABLED"]:
            logger.info("Graph database is disabled in configuration")
            return False
            
        try:
            self.graph = Graph(
                CONFIG["NEO4J_URI"],
                auth=(CONFIG["NEO4J_USERNAME"], CONFIG["NEO4J_PASSWORD"])
            )
            # Test the connection
            self.graph.run("RETURN 1")
            self.is_connected = True
            logger.info("Successfully connected to Neo4j graph database")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to Neo4j: {str(e)}")
            self.graph = None
            self.is_connected = False
            return False
    
    def get_graph(self) -> Optional[Graph]:
        """Get the graph connection if available."""
        if not self.is_connected:
            return None
        return self.graph
    
    def is_available(self) -> bool:
        """Check if graph database is available."""
        return self.is_connected
    
    def run_query(self, query: str, parameters: dict = None) -> Optional[list]:
        """Run a Cypher query if graph database is available."""
        if not self.is_available():
            return None
            
        try:
            if parameters:
                result = self.graph.run(query, parameters)
            else:
                result = self.graph.run(query)
            return result.data()
        except Exception as e:
            logger.error(f"Error running Cypher query: {str(e)}")
            return None

# Global instance
graph_db_manager = GraphDBManager() 