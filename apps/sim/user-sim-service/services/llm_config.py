import os


class LLMConfig:
    API_KEY_ROTATION_LIST: str = os.getenv(
        "API_KEY_ROTATION_LIST",
        "sk-358c49d734ed49f7a3ff6b39ea6b77a3,sk-e2430b25aa8646e28eacf09d2b1d3b50"
    )
    DASHSCOPE_API_KEY_POOL: str = os.getenv(
        "DASHSCOPE_API_KEY_POOL",
        "sk-358c49d734ed49f7a3ff6b39ea6b77a3,sk-e2430b25aa8646e28eacf09d2b1d3b50"
    )
    OPENAI_API_BASE: str = os.getenv(
        "OPENAI_API_BASE",
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    OPENAI_MODEL_NAME: str = os.getenv(
        "OPENAI_MODEL_NAME",
        "qwen-turbo-2025-07-15,qwen-plus-2025-07-28,qwen-max-latest,qwen3-32b"
    )
    MODEL_CANDIDATES: str = os.getenv(
        "MODEL_CANDIDATES",
        "qwen-turbo-2025-07-15,qwen-plus-2025-07-28,qwen-max-latest,qwen3-32b"
    )

    @classmethod
    def get_api_keys(cls) -> list:
        return cls.DASHSCOPE_API_KEY_POOL.split(",")

    @classmethod
    def get_model_candidates(cls) -> list:
        return [m.strip() for m in cls.MODEL_CANDIDATES.split(",")]

    @classmethod
    def get_api_base(cls) -> str:
        return cls.OPENAI_API_BASE.strip()
