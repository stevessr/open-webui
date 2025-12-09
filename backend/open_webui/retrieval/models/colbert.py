import logging

from open_webui.env import SRC_LOG_LEVELS
from open_webui.retrieval.models.base_reranker import BaseReranker

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["RAG"])


class ColBERT(BaseReranker):
    def __init__(self, name, **kwargs) -> None:
        raise Exception("Local ColBERT reranking is no longer supported. Please use external reranking services.")

    def predict(self, sentences):
        raise Exception("Local ColBERT reranking is no longer supported. Please use external reranking services.")
