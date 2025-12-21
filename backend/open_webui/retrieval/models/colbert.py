import logging

from open_webui.retrieval.models.base_reranker import BaseReranker

log = logging.getLogger(__name__)


class ColBERT(BaseReranker):
    def __init__(self, name, **kwargs) -> None:
        raise Exception("Local ColBERT reranking is no longer supported. Please use external reranking services.")

    def predict(self, sentences):
        raise Exception("Local ColBERT reranking is no longer supported. Please use external reranking services.")
