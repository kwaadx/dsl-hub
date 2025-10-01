# Minimal mock LLM; replace with real provider (OpenAI/Anthropic/etc).
class LLMClient:
    async def generate_pipeline(self, context: dict, user_message: dict) -> dict:
        # return a tiny valid draft based on schema expectations (placeholder)
        return {
            "name": "example-pipeline",
            "stages": [
                {"name":"load", "type":"source", "params":{"path":"s3://bucket/key"}},
                {"name":"transform", "type":"map", "params":{"fn":"clean_text"}},
                {"name":"save", "type":"sink", "params":{"table":"results"}}
            ]
        }

    async def self_check(self, draft: dict) -> dict:
        return {"notes":[
            "Verify `path` exists.",
            "Validate that `table` is present and accessible."
        ]}
