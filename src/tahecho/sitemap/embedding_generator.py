"""Embedding generator for sitemap content."""

import asyncio
import logging
from typing import Any, Dict, List

import openai

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates embeddings for sitemap content using OpenAI."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize embedding generator."""
        self.model = config.get("model", "text-embedding-3-small")
        self.dimension = config.get("dimension", 1536)
        self.client = openai.AsyncOpenAI()

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a text string."""
        try:
            response = await self.client.embeddings.create(
                model=self.model, input=text, encoding_format="float"
            )

            embedding = response.data[0].embedding

            # Validate dimension
            if len(embedding) != self.dimension:
                logger.warning(
                    f"Expected embedding dimension {self.dimension}, got {len(embedding)}"
                )

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in batch."""
        try:
            response = await self.client.embeddings.create(
                model=self.model, input=texts, encoding_format="float"
            )

            embeddings = [data.embedding for data in response.data]

            # Validate dimensions
            for i, embedding in enumerate(embeddings):
                if len(embedding) != self.dimension:
                    logger.warning(
                        f"Expected embedding dimension {self.dimension}, got {len(embedding)} for text {i}"
                    )

            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings batch: {e}")
            raise

    def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate embedding dimension."""
        return len(embedding) == self.dimension

    async def generate_content_embedding(
        self, content: str, max_length: int = 8000
    ) -> List[float]:
        """Generate embedding for content with length limit."""
        # Truncate content if too long
        if len(content) > max_length:
            content = content[:max_length] + "..."

        return await self.generate_embedding(content)

    async def generate_title_embedding(self, title: str) -> List[float]:
        """Generate embedding for page title."""
        return await self.generate_embedding(title)

    async def generate_combined_embedding(
        self, title: str, content: str, title_weight: float = 0.3
    ) -> List[float]:
        """Generate combined embedding from title and content."""
        title_embedding = await self.generate_title_embedding(title)
        content_embedding = await self.generate_content_embedding(content)

        # Combine embeddings with weights
        combined_embedding = []
        for i in range(len(title_embedding)):
            combined_value = (
                title_weight * title_embedding[i]
                + (1 - title_weight) * content_embedding[i]
            )
            combined_embedding.append(combined_value)

        return combined_embedding
