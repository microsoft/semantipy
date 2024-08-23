from langchain.llms.base import BaseLanguageModel

lm: BaseLanguageModel


def configure(lm: BaseLanguageModel):
    globals()["lm"] = lm
