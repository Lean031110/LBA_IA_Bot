import numpy as np
from typing import Dict, List, Tuple, Optional
import sqlite3
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config.config import Config
from utils.helpers import clean_text

class SimpleAIEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.knowledge_base = {}
        self.conversation_history = {}
        self.logger = logging.getLogger(__name__)
        self.load_knowledge_base()

    def load_knowledge_base(self) -> None:
        """Carga la base de conocimiento desde la base de datos"""
        try:
            with sqlite3.connect(Config.DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT pattern, response, confidence FROM knowledge')
                rows = cursor.fetchall()

                for pattern, response, confidence in rows:
                    self.knowledge_base[pattern] = {
                        'response': response,
                        'confidence': confidence,
                        'vector': None  # Se calculará bajo demanda
                    }

                if not self.knowledge_base:
                    self.initialize_default_knowledge()

        except Exception as e:
            self.logger.error(f"Error loading knowledge base: {e}")
            self.initialize_default_knowledge()

    def initialize_default_knowledge(self) -> None:
        """Inicializa la base de conocimiento con respuestas predeterminadas"""
        default_knowledge = {
            "hola": {
                "response": "¡Hola! ¿En qué puedo ayudarte?",
                "confidence": 1.0
            },
            "gracias": {
                "response": "¡De nada! Estoy aquí para ayudar.",
                "confidence": 1.0
            },
            "adios": {
                "response": "¡Hasta luego! Que tengas un buen día.",
                "confidence": 1.0
            }
        }

        for pattern, data in default_knowledge.items():
            self.learn(pattern, data['response'], data['confidence'])

    def learn(self, pattern: str, response: str, confidence: float = 0.8) -> bool:
        """Aprende un nuevo patrón de respuesta"""
        try:
            # Limpiar y validar entrada
            pattern = clean_text(pattern)
            if not pattern or not response:
                return False

            # Guardar en la base de datos
            with sqlite3.connect(Config.DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO knowledge (pattern, response, confidence)
                    VALUES (?, ?, ?)
                ''', (pattern, response, confidence))
                conn.commit()

            # Actualizar memoria local
            self.knowledge_base[pattern] = {
                'response': response,
                'confidence': confidence,
                'vector': None
            }

            return True

        except Exception as e:
            self.logger.error(f"Error learning new pattern: {e}")
            return False

    def get_response(self, text: str, user_id: int) -> Tuple[str, float]:
        """Genera una respuesta basada en el texto de entrada"""
        try:
            # Limpiar texto
            clean_input = clean_text(text)

            # Buscar mejor coincidencia
            best_match, confidence = self._find_best_match(clean_input)

            # Si no hay coincidencia suficiente, intentar generar respuesta
            if confidence < Config.MIN_CONFIDENCE:
                generated_response = self._generate_response(clean_input, user_id)
                if generated_response:
                    return generated_response, 0.6

            return best_match, confidence

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "Lo siento, ha ocurrido un error.", 0.0

    def _find_best_match(self, text: str) -> Tuple[str, float]:
        """Encuentra la mejor coincidencia en la base de conocimiento"""
        if not self.knowledge_base:
            return "No tengo suficiente información para responder.", 0.0

        best_match = None
        best_confidence = 0.0

        # Vectorizar texto de entrada
        input_vector = self.vectorizer.fit_transform([text])

        for pattern, data in self.knowledge_base.items():
            # Calcular vector si no existe
            if data['vector'] is None:
                data['vector'] = self.vectorizer.transform([pattern])

            # Calcular similitud
            similarity = cosine_similarity(input_vector, data['vector'])[0][0]
            confidence = similarity * data['confidence']

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = data['response']

        return best_match or "No entiendo tu pregunta.", best_confidence

    def _generate_response(self, text: str, user_id: int) -> Optional[str]:
        """Intenta generar una respuesta basada en el contexto"""
        try:
            # Verificar historial de conversación
            if user_id in self.conversation_history:
                context = self.conversation_history[user_id]
                # Aquí se podría implementar un sistema más complejo de generación
                # Por ahora, solo devolvemos None para usar respuestas predeterminadas
                return None

            return None

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return None

    def update_conversation_history(self, user_id: int, text: str) -> None:
        """Actualiza el historial de conversación de un usuario"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        self.conversation_history[user_id].append({
            'text': text,
            'timestamp': datetime.now()
        })

        # Mantener solo los últimos N mensajes
        if len(self.conversation_history[user_id]) > Config.MAX_CONTEXT_LENGTH:
            self.conversation_history[user_id].pop(0)

    def get_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas del motor de IA"""
        return {
            'patterns': len(self.knowledge_base),
            'users': len(self.conversation_history),
            'total_interactions': sum(
                len(history) for history in self.conversation_history.values()
            )
        }