from __future__ import annotations

from typing import Iterator
from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_db
from .infrastructure.sqlalchemy_repos import SAThreadRepo, SAMessageRepo
from .infrastructure.uow_sqlalchemy import SAUnitOfWork
from .application.messages import CreateMessage, ListMessages
from .application.threads import GetThread

def sa_session() -> Iterator[Session]:
    with get_db() as db:
        yield db

def thread_repo(db: Session = Depends(sa_session)) -> SAThreadRepo:
    return SAThreadRepo(db)

def message_repo(db: Session = Depends(sa_session)) -> SAMessageRepo:
    return SAMessageRepo(db)

def uow(db: Session = Depends(sa_session)) -> SAUnitOfWork:
    return SAUnitOfWork(db)

# Use-cases
def uc_create_message(u: SAUnitOfWork = Depends(uow), m: SAMessageRepo = Depends(message_repo), t: SAThreadRepo = Depends(thread_repo)):
    return CreateMessage(uow=u, messages=m, threads=t)

def uc_list_messages(m: SAMessageRepo = Depends(message_repo)):
    return ListMessages(messages=m)

def uc_get_thread(t: SAThreadRepo = Depends(thread_repo)):
    return GetThread(threads=t)

from .infrastructure.schema_repo import SASchemaRepo
from .application.validation import ValidatePayload
from .infrastructure.llm_openai import OpenAILLM
from .infrastructure.similarity_builtin import BuiltinSimilarity

# Repos/adapters
def schema_repo(db: Session = Depends(sa_session)) -> SASchemaRepo:
    return SASchemaRepo(db)

def llm() -> OpenAILLM:
    return OpenAILLM()

def similarity() -> BuiltinSimilarity:
    return BuiltinSimilarity()

# Use-cases
def uc_validate_payload(repo: SASchemaRepo = Depends(schema_repo)) -> ValidatePayload:
    return ValidatePayload(repo)


from .infrastructure.domain_repos import SAFlowRepo, SAPipelineRepo, SAThreadSummaryRepo
from .application.flows import ListFlows, CreateFlow, UpdateFlow, DeleteFlow
from .application.pipelines import CreatePipeline, ListPipelinesForFlow
from .application.summaries import ListThreadSummaries

def flow_repo(db: Session = Depends(sa_session)) -> SAFlowRepo:
    return SAFlowRepo(db)

def pipeline_repo(db: Session = Depends(sa_session)) -> SAPipelineRepo:
    return SAPipelineRepo(db)

def thread_summary_repo(db: Session = Depends(sa_session)) -> SAThreadSummaryRepo:
    return SAThreadSummaryRepo(db)

# Flow UCs
def uc_list_flows(r: SAFlowRepo = Depends(flow_repo)) -> ListFlows:
    return ListFlows(r)
def uc_create_flow(r: SAFlowRepo = Depends(flow_repo)) -> CreateFlow:
    return CreateFlow(r)
def uc_update_flow(r: SAFlowRepo = Depends(flow_repo)) -> UpdateFlow:
    return UpdateFlow(r)
def uc_delete_flow(r: SAFlowRepo = Depends(flow_repo)) -> DeleteFlow:
    return DeleteFlow(r)

# Pipeline UCs
def uc_create_pipeline(p: SAPipelineRepo = Depends(pipeline_repo), f: SAFlowRepo = Depends(flow_repo)) -> CreatePipeline:
    return CreatePipeline(p, f)
def uc_list_pipelines_for_flow(p: SAPipelineRepo = Depends(pipeline_repo), f: SAFlowRepo = Depends(flow_repo)) -> ListPipelinesForFlow:
    return ListPipelinesForFlow(p, f)

# Summaries
def uc_list_thread_summaries(r: SAThreadSummaryRepo = Depends(thread_summary_repo)) -> ListThreadSummaries:
    return ListThreadSummaries(r)


from .application.agent import StartAgentRun
from .services.llm import LLMClient as LegacyLLMClient  # fallback
from .services.similarity_service import SimilarityService as LegacySimilarity
from .agent.graph import AgentRunner
from .database import SessionLocal

def agent_runner(sim: LegacySimilarity = Depends(similarity), llm_client: LegacyLLMClient = Depends(llm)) -> AgentRunner:
    return AgentRunner(session_factory=SessionLocal, similarity_service=sim, llm_client=llm_client)

def uc_start_agent_run(r: AgentRunner = Depends(agent_runner)) -> StartAgentRun:
    return StartAgentRun(r)

from .infrastructure.agent_adapters import SARunsRepo, PipelineServiceAdapter, ValidationServiceAdapter


def runs_repo(db: Session = Depends(sa_session)) -> SARunsRepo:
    return SARunsRepo(db)

def pipeline_service(db: Session = Depends(sa_session)) -> PipelineServiceAdapter:
    return PipelineServiceAdapter(db)

def validation_service_port(db: Session = Depends(sa_session)) -> ValidationServiceAdapter:
    return ValidationServiceAdapter(db)

from .infrastructure.summarizer_llm import LLMSummarizer
from .infrastructure.domain_repos import SAFlowSummaryRepo
from .application.summaries_generate import GenerateThreadSummary, RefreshFlowSummary

def flow_summary_repo(db: Session = Depends(sa_session)) -> SAFlowSummaryRepo:
    return SAFlowSummaryRepo(db)
def summarizer(llm_client = Depends(llm)) -> LLMSummarizer:
    # LLMSummarizer wraps LLM client; LLMSummarizer creates its own OpenAILLM if llm_client is None
    from .infrastructure.llm_openai import OpenAILLM
    return LLMSummarizer(OpenAILLM())
def uc_generate_thread_summary(m = Depends(message_repo), t = Depends(thread_repo), ts = Depends(thread_summary_repo), s = Depends(summarizer), eb = Depends(event_bus)) -> GenerateThreadSummary:
    return GenerateThreadSummary(m, t, ts, s, eb)
def uc_refresh_flow_summary(ts = Depends(thread_summary_repo), fs = Depends(flow_summary_repo), s = Depends(summarizer), eb = Depends(event_bus)) -> RefreshFlowSummary:
    return RefreshFlowSummary(ts, fs, s, eb)

from .infrastructure.event_bus import SSEEventBus


def event_bus() -> SSEEventBus:
    return SSEEventBus()

from .infrastructure.prompt_repo import SAPromptTemplateRepo
from .infrastructure.compat_repo import SACompatRuleRepo
from .infrastructure.agent_log_repo import SAAgentLogRepo

def prompt_repo(db: Session = Depends(sa_session)) -> SAPromptTemplateRepo:
    return SAPromptTemplateRepo(db)
def compat_repo(db: Session = Depends(sa_session)) -> SACompatRuleRepo:
    return SACompatRuleRepo(db)
def agent_log(db: Session = Depends(sa_session)) -> SAAgentLogRepo:
    return SAAgentLogRepo(db)
