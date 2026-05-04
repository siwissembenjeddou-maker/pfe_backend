import os
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

AUTISM_KNOWLEDGE_BASE = [
    "Children with autism often show limited eye contact during social interactions. "
    "They may not respond to their name being called. Lack of pointing, showing, or sharing interests "
    "by 12 months is an early indicator.",

    "Joint attention deficits are a hallmark of autism. A child with ASD may not follow another person's "
    "gaze or pointing gesture. They tend to engage in parallel play rather than interactive play.",

    "Pragmatic language difficulties in autism include taking turns in conversation, understanding "
    "non-literal language (sarcasm, jokes), and using context-appropriate speech.",

    "Repetitive motor movements (stereotypies) such as hand flapping, rocking, spinning, and toe walking "
    "are common in autism. These are often self-regulatory (stimming) behaviours.",

    "Insistence on sameness is characteristic of autism spectrum disorder. Children may become extremely "
    "distressed by small changes in routine, environment, or the sequence of daily activities.",

    "Restricted interests in autism manifest as intense, consuming focus on specific topics or objects, "
    "often to the exclusion of other activities.",

    "Sensory hypersensitivity in autism: the child may cover ears for ordinary sounds, avoid textures, "
    "refuse certain foods based on texture or smell, or be distressed by bright lights.",

    "Sensory hyposensitivity: some autistic children have a high pain threshold, appear not to notice "
    "temperature extremes, seek intense sensory input through crashing, spinning, or deep pressure.",

    "During eating activities, autistic children often show extreme food selectivity, difficulty using "
    "utensils, not sitting at the table, and sensory aversion to certain foods.",

    "Signs during drinking: child insists on one specific cup or straw, refuses drinks by smell before "
    "tasting, spills frequently due to motor coordination difficulties.",

    "During writing tasks, autistic children may show difficulty with pencil grip, writing pressure, "
    "letter formation, and staying within lines.",

    "Play in autism is often solitary, repetitive, and non-functional (e.g., lining up toys rather than "
    "playing imaginatively). The child may lack pretend play.",

    "Social play deficits: autistic children often struggle to join peer games, wait for turns, follow "
    "changing rules, or engage in cooperative play.",

    "Communication during daily activities: may use echolalia, speak in a monotone, have a large "
    "vocabulary but struggle with conversation, or be non-verbal.",

    "Autism scoring framework: Score 0-2.9 (Mild). Score 3-5.9 (Moderate). Score 6-10 (Severe).",

    "Dimension scoring guide: Social Interaction (0-10), Communication (0-10), "
    "Repetitive Behaviors (0-10), Sensory Response (0-10), "
    "Daily Living Skills (0-10), Emotional Regulation (0-10).",

    "Early intervention for autism is most effective before age 5. ABA (Applied Behaviour Analysis) "
    "improves communication, social skills, and adaptive behaviour.",

    "Speech and Language Therapy targets communication: verbal speech, AAC devices, pragmatic skills. "
    "PECS is used for non-verbal children.",

    "Occupational Therapy addresses sensory processing, fine/gross motor skills, and daily living skills.",

    "Social skills groups provide structured peer interaction practice targeting reciprocal conversation, "
    "reading social cues, and friendship building.",

    "Parent-mediated interventions significantly improve child communication and social outcomes "
    "when implemented consistently at home.",

    "Visual supports (schedules, social stories, first-then boards) reduce anxiety and improve "
    "transitions in autistic children.",
]


class RAGEngine:
    _instance   = None
    _collection = None
    _embed_model = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        import chromadb
        from sentence_transformers import SentenceTransformer

        logger.info("Initialising RAG engine…")
        self._embed_model = SentenceTransformer('all-MiniLM-L6-v2')

        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self._collection = client.get_or_create_collection(
            name='autism_knowledge',
            metadata={'hnsw:space': 'cosine'},
        )

        if self._collection.count() == 0:
            logger.info("Seeding ChromaDB…")
            ids        = [f'doc_{i}' for i in range(len(AUTISM_KNOWLEDGE_BASE))]
            embeddings = self._embed_model.encode(AUTISM_KNOWLEDGE_BASE).tolist()
            self._collection.add(ids=ids, embeddings=embeddings, documents=AUTISM_KNOWLEDGE_BASE)
            logger.info(f"Added {len(AUTISM_KNOWLEDGE_BASE)} chunks to ChromaDB.")

    def add_custom_data(self, texts: list, ids: list = None):
        if ids is None:
            existing = self._collection.count()
            ids = [f'custom_{existing + i}' for i in range(len(texts))]
        embeddings = self._embed_model.encode(texts).tolist()
        self._collection.add(ids=ids, embeddings=embeddings, documents=texts)
        logger.info(f"Added {len(texts)} custom chunks to ChromaDB.")

    def retrieve(self, query: str, n_results: int = 5) -> list:
        embedding = self._embed_model.encode([query])[0].tolist()
        results   = self._collection.query(query_embeddings=[embedding], n_results=n_results)
        return results['documents'][0] if results['documents'] else []

    def analyze(self, transcription: str, child_info: dict, activity_type: str) -> dict:
        context_chunks = self.retrieve(f"{activity_type}: {transcription}", n_results=6)
        context        = '\n\n'.join(context_chunks)
        prompt         = self._build_prompt(transcription, child_info, activity_type, context)
        raw_response   = self._call_llm(prompt)
        return self._parse_response(raw_response)

    def _build_prompt(self, transcription, child_info, activity_type, context):
        return f"""You are an expert autism assessment AI assistant.

## AUTISM KNOWLEDGE BASE (Retrieved Context)
{context}

## CHILD INFORMATION
- Name: {child_info.get('name', 'Unknown')}
- Age: {child_info.get('age', 'Unknown')} years
- Gender: {child_info.get('gender', 'Unknown')}

## ACTIVITY TYPE
{activity_type}

## PARENT'S DESCRIPTION
"{transcription}"

## YOUR TASK
Analyse the parent's description using the knowledge base above.
Respond ONLY with a valid JSON object (no markdown, no extra text):

{{
  "autism_score": <float 0.0-10.0>,
  "severity_level": "<mild|moderate|severe>",
  "dimension_scores": {{
    "Social Interaction": <float 0.0-10.0>,
    "Communication": <float 0.0-10.0>,
    "Repetitive Behaviors": <float 0.0-10.0>,
    "Sensory Response": <float 0.0-10.0>,
    "Daily Living Skills": <float 0.0-10.0>,
    "Emotional Regulation": <float 0.0-10.0>
  }},
  "ai_analysis": "<2-4 sentence professional interpretation>",
  "key_observations": ["<obs 1>", "<obs 2>", "<obs 3>"],
  "immediate_recommendations": ["<rec 1>", "<rec 2>", "<rec 3>"]
}}

Scoring: 0-2.9=mild, 3-5.9=moderate, 6-10=severe. Severity must match score.
"""

    def _call_llm(self, prompt):
        if settings.LLM_PROVIDER == 'anthropic':
            return self._call_anthropic(prompt)
        return self._call_openai(prompt)

    def _call_anthropic(self, prompt):
        import anthropic
        client  = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model='claude-opus-4-6',
            max_tokens=1024,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return message.content[0].text

    def _call_openai(self, prompt):
        from openai import OpenAI
        client   = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model='gpt-4-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=1024,
            temperature=0.2,
        )
        return response.choices[0].message.content

    def _parse_response(self, raw):
        try:
            clean = raw.strip()
            if clean.startswith('```'):
                clean = '\n'.join(clean.split('\n')[1:-1])
            result = json.loads(clean)
            score  = float(result.get('autism_score', 0))
            result['autism_score'] = max(0.0, min(10.0, score))
            if result['autism_score'] < 3:
                result['severity_level'] = 'mild'
            elif result['autism_score'] < 6:
                result['severity_level'] = 'moderate'
            else:
                result['severity_level'] = 'severe'
            return result
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                'autism_score': 0.0,
                'severity_level': 'mild',
                'dimension_scores': {
                    'Social Interaction': 0.0, 'Communication': 0.0,
                    'Repetitive Behaviors': 0.0, 'Sensory Response': 0.0,
                    'Daily Living Skills': 0.0, 'Emotional Regulation': 0.0,
                },
                'ai_analysis': 'Analysis could not be completed. Please try again.',
                'key_observations': [],
                'immediate_recommendations': [],
            }


def transcribe_audio(audio_file_path: str) -> str:
    # Lazy import to avoid ctranslate2/pkg_resources issue during Django startup
    from faster_whisper import WhisperModel
    
    # Load once globally (important for performance)
    global WHISPER_MODEL_INSTANCE
    if 'WHISPER_MODEL_INSTANCE' not in globals():
        WHISPER_MODEL_INSTANCE = WhisperModel(
            model_size_or_path="base",
            compute_type="int8"   # best for Windows CPU
        )
    
    logger.info(f"Transcribing: {audio_file_path}")

    segments, _ = WHISPER_MODEL_INSTANCE.transcribe(
        audio_file_path,
        beam_size=5
    )

    text = ""
    for segment in segments:
        text += segment.text + " "

    return text.strip()