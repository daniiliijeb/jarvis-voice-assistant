from __future__ import annotations

import logging
from typing import Optional, Tuple

try:
    from sentence_transformers import SentenceTransformer
    from numpy import dot
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class SemanticRouter:
    """Семантический маршрутизатор команд - понимает команды по смыслу, а не по тексту
    
    Использует sentence-transformers для создания embeddings и сравнения по cosine similarity.
    Это позволяет понимать команды даже если они сформулированы по-другому.
    
    Примеры:
    - "запусти браузер" = "открой интернет" = "включи хром" = "выведи гугл"
    - Все эти фразы будут распознаны как команда "browser"
    """
    
    def __init__(self):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers не установлен. Установите: pip install sentence-transformers"
            )
        
        self.logger = logging.getLogger("jarvis")
        self.logger.info("SemanticRouter: Загрузка модели sentence-transformers...")
        
        # Используем лёгкую модель для быстрой работы
        # all-MiniLM-L6-v2 - быстрая и точная модель для русского и английского
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.logger.info("SemanticRouter: Модель загружена")
        
        # База команд: "имя команды" : [список примеров фраз]
        self.commands: dict[str, list[str]] = {}
        
        # Индекс embeddings: "имя команды" : [массив embeddings для каждой фразы]
        self.index: dict[str, list] = {}
    
    def add_intent(self, name: str, phrases: list[str]) -> None:
        """Добавляет намерение (команду) с примерами фраз
        
        Args:
            name: Имя команды (например, "browser", "youtube")
            phrases: Список примеров фраз для этой команды
        """
        if not phrases:
            self.logger.warning(f"SemanticRouter: Пустой список фраз для команды '{name}'")
            return
        
        # Создаём embeddings для всех фраз
        # normalize_embeddings=True для использования cosine similarity
        emb = self.model.encode(phrases, normalize_embeddings=True)
        
        self.commands[name] = phrases
        self.index[name] = emb
        
        self.logger.debug(f"SemanticRouter: Добавлена команда '{name}' с {len(phrases)} примерами")
    
    def match(self, query: str, threshold: float = 0.62) -> Tuple[Optional[str], float]:
        """Находит наиболее подходящую команду для запроса
        
        Args:
            query: Фраза пользователя
            threshold: Минимальный порог similarity (0.0 - 1.0)
        
        Returns:
            Tuple[имя_команды, score] или (None, 0.0) если ничего не найдено
        """
        if not query or not self.index:
            return None, 0.0
        
        # Создаём embedding для запроса
        q_emb = self.model.encode(query, normalize_embeddings=True)
        
        best_cmd = None
        best_score = 0.0
        
        # Сравниваем с каждой командой
        for name, embeddings in self.index.items():
            # Сравниваем с каждой примерной фразой команды
            # Используем cosine similarity (dot product для normalized embeddings)
            scores = [float(dot(q_emb, e)) for e in embeddings]
            score = max(scores)  # Берём максимальный score среди всех примеров
            
            if score > best_score:
                best_cmd = name
                best_score = score
        
        # Проверяем порог
        if best_score >= threshold:
            self.logger.debug(
                f"SemanticRouter: Найдена команда '{best_cmd}' для '{query}' "
                f"(score: {best_score:.3f})"
            )
            return best_cmd, best_score
        
        self.logger.debug(
            f"SemanticRouter: Команда не найдена для '{query}' "
            f"(лучший score: {best_score:.3f}, порог: {threshold})"
        )
        return None, best_score


