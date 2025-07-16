"""
Unit tests for task classifier module.
"""
import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage
from agents.task_classifier import TaskClassifier
from agents.state import create_initial_state


class TestTaskClassifier:
    """Test TaskClassifier class."""
    
    def test_task_classifier_initialization(self):
        """Test TaskClassifier initialization."""
        # Arrange & Act
        classifier = TaskClassifier()
        
        # Assert
        assert classifier.llm is not None
        assert "task classifier" in str(classifier.classification_prompt).lower()
    
    @patch('agents.task_classifier.ChatOpenAI')
    def test_classify_task_mcp(self, mock_chat_openai):
        """Test classifying a Jira-related task as MCP."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        classifier = TaskClassifier()
        state = create_initial_state("Show me all open bugs in DTS project")
        
        # Mock the chain creation and invoke
        mock_chain = Mock()
        mock_chain.invoke.return_value = AIMessage(content='{"task_type": "mcp", "reasoning": "Direct Jira operation"}')
        
        with patch.object(classifier, 'classification_prompt') as mock_prompt:
            mock_prompt.__or__.return_value = mock_chain
            
            # Act
            result_state = classifier.classify_task(state)
        
        # Assert
        assert result_state.task_type == "mcp"
        assert len(result_state.messages) == 2  # Original message + classification message
        assert "mcp" in result_state.messages[1].content.lower()
    
    @patch('agents.task_classifier.ChatOpenAI')
    def test_classify_task_graph(self, mock_chat_openai):
        """Test classifying a relationship query as Graph."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        classifier = TaskClassifier()
        state = create_initial_state("Why is task DTS-53 blocked?")
        
        # Mock the chain creation and invoke
        mock_chain = Mock()
        mock_chain.invoke.return_value = AIMessage(content='{"task_type": "graph", "reasoning": "Complex reasoning required"}')
        
        with patch.object(classifier, 'classification_prompt') as mock_prompt:
            mock_prompt.__or__.return_value = mock_chain
            
            # Act
            result_state = classifier.classify_task(state)
        
        # Assert
        assert result_state.task_type == "graph"
        assert len(result_state.messages) == 2  # Original message + classification message
        assert "graph" in result_state.messages[1].content.lower()
    
    @patch('agents.task_classifier.ChatOpenAI')
    def test_classify_task_general(self, mock_chat_openai):
        """Test classifying a general conversation as general."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        classifier = TaskClassifier()
        state = create_initial_state("Hello, how are you?")
        
        # Mock the chain creation and invoke
        mock_chain = Mock()
        mock_chain.invoke.return_value = AIMessage(content='{"task_type": "general", "reasoning": "General conversation"}')
        
        with patch.object(classifier, 'classification_prompt') as mock_prompt:
            mock_prompt.__or__.return_value = mock_chain
            
            # Act
            result_state = classifier.classify_task(state)
        
        # Assert
        assert result_state.task_type == "general"
        assert len(result_state.messages) == 2  # Original message + classification message
        assert "general" in result_state.messages[1].content.lower()
    
    @patch('agents.task_classifier.ChatOpenAI')
    def test_classify_task_fallback_on_error(self, mock_chat_openai):
        """Test fallback to general when classification fails."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        classifier = TaskClassifier()
        state = create_initial_state("Show me my tasks")
        
        # Mock the chain creation and invoke to raise an exception
        mock_chain = Mock()
        mock_chain.invoke.side_effect = Exception("API Error")
        
        with patch.object(classifier, 'classification_prompt') as mock_prompt:
            mock_prompt.__or__.return_value = mock_chain
            
            # Act
            result_state = classifier.classify_task(state)
        
        # Assert
        assert result_state.task_type == "general"
        assert len(result_state.messages) == 2  # Original message + error message
        assert "failed" in result_state.messages[1].content.lower()
    
    @patch('agents.task_classifier.ChatOpenAI')
    def test_classify_task_invalid_json_fallback(self, mock_chat_openai):
        """Test fallback when LLM returns invalid JSON."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        classifier = TaskClassifier()
        state = create_initial_state("Create a new task")
        
        # Mock the chain creation and invoke
        mock_chain = Mock()
        mock_chain.invoke.return_value = AIMessage(content="This is not valid JSON")
        
        with patch.object(classifier, 'classification_prompt') as mock_prompt:
            mock_prompt.__or__.return_value = mock_chain
            
            # Act
            result_state = classifier.classify_task(state)
        
        # Assert
        # Should fallback to general since no JSON pattern found
        assert result_state.task_type == "general"
    
    @patch('agents.task_classifier.ChatOpenAI')
    def test_classify_task_mcp_keyword_fallback(self, mock_chat_openai):
        """Test fallback to MCP when 'mcp' keyword is found."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        classifier = TaskClassifier()
        state = create_initial_state("Show me all issues")
        
        # Mock the chain creation and invoke
        mock_chain = Mock()
        mock_chain.invoke.return_value = AIMessage(content="This should be an mcp task")
        
        with patch.object(classifier, 'classification_prompt') as mock_prompt:
            mock_prompt.__or__.return_value = mock_chain
            
            # Act
            result_state = classifier.classify_task(state)
        
        # Assert
        assert result_state.task_type == "mcp"
        assert len(result_state.messages) == 2  # Original message + classification message

    @patch('agents.task_classifier.ChatOpenAI')
    def test_classify_task_graph_keyword_fallback(self, mock_chat_openai):
        """Test fallback to Graph when 'graph' keyword is found."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        classifier = TaskClassifier()
        state = create_initial_state("Why is this blocked?")
        
        # Mock the chain creation and invoke
        mock_chain = Mock()
        mock_chain.invoke.return_value = AIMessage(content="This should be a graph task")
        
        with patch.object(classifier, 'classification_prompt') as mock_prompt:
            mock_prompt.__or__.return_value = mock_chain
            
            # Act
            result_state = classifier.classify_task(state)
        
        # Assert
        assert result_state.task_type == "graph"
        assert len(result_state.messages) == 2  # Original message + classification message


class TestTaskClassifierEdgeCases:
    """Test edge cases for task classifier."""
    
    @patch('agents.task_classifier.ChatOpenAI')
    def test_classify_task_empty_input(self, mock_chat_openai):
        """Test classifying empty input."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        classifier = TaskClassifier()
        state = create_initial_state("")
        
        # Mock the chain creation and invoke
        mock_chain = Mock()
        mock_chain.invoke.return_value = AIMessage(content='{"task_type": "general", "reasoning": "Empty input"}')
        
        with patch.object(classifier, 'classification_prompt') as mock_prompt:
            mock_prompt.__or__.return_value = mock_chain
            
            # Act
            result_state = classifier.classify_task(state)
        
        # Assert
        assert result_state.task_type == "general"
    
    @patch('agents.task_classifier.ChatOpenAI')
    def test_classify_task_very_long_input(self, mock_chat_openai):
        """Test classifying very long input."""
        # Arrange
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        classifier = TaskClassifier()
        long_input = "Show me all issues in project DTS that are assigned to me and have priority high and status is not done and created in the last 30 days and have labels documentation or bug"
        state = create_initial_state(long_input)
        
        # Mock the chain creation and invoke
        mock_chain = Mock()
        mock_chain.invoke.return_value = AIMessage(content='{"task_type": "mcp", "reasoning": "Long Jira query"}')
        
        with patch.object(classifier, 'classification_prompt') as mock_prompt:
            mock_prompt.__or__.return_value = mock_chain
            
            # Act
            result_state = classifier.classify_task(state)
        
        # Assert
        assert result_state.task_type == "mcp"
        assert result_state.user_input == long_input
        assert len(result_state.messages) == 2  # Original message + classification message 