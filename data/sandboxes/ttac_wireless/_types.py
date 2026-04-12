#!/usr/bin/env python
# -*-coding:utf-8 -*-

from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field


# ------------------------------------------------------------------------------
# ToolCall
# ------------------------------------------------------------------------------

class ToolFunction(BaseModel):
    """
    Mirrors the OpenAI Chat Completions tool call function payload.
    `arguments` is a JSON string (per OpenAI spec).
    """
    name: str
    arguments: str = Field(default="{}", description="JSON-encoded string of function arguments")


class ToolCall(BaseModel):
    """
    Minimal Pydantic model compatible with OpenAI tool call objects like:

    {
      "id": "call_abc123",
      "type": "function",
      "function": { "name": "...", "arguments": "{...}" }
    }
    """
    id: str
    type: Literal["function"] = "function"
    function: ToolFunction


class AssistantMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    reasoning_content: Optional[str] = None



class ToolCallTrace(BaseModel):
    """
    Trace entry for a single tool call during the agent loop.
    """
    function_name: str
    arguments: str
    turn: int
    has_failed: bool
    order: int


class AgentResult(BaseModel):
    """
    Final structured output.
    """
    scenario_id: str
    num_iterations: int = Field(..., ge=1)
    tool_calls: List[ToolCallTrace]
    num_tool_calls: int = Field(..., ge=0)
    status: Literal["solved", "unresolved"]
    traces: str
    answer: str
    messages: List[Dict[str, Any]]
    reason: Optional[str] = None
    
# ------------------------------------------------------------------------------
# Task / Root causes
# ------------------------------------------------------------------------------

class RootCause(BaseModel):
    id: str = Field(..., description="Root cause identifier, e.g. C1")
    label: str = Field(..., description="Human-readable description")


class Task(BaseModel):
    allowed_tools: Literal["all"] | str
    description: str
    options: List[RootCause]



# ------------------------------------------------------------------------------
# Context
# ------------------------------------------------------------------------------

class Environment(BaseModel):
    mobility_scenario: str
    network_type: str
    num_base_stations: str  # kept as str to match source data


class Context(BaseModel):
    description: str
    wireless_network_information: Environment


# ------------------------------------------------------------------------------
# Data section
# ------------------------------------------------------------------------------

class ScenarioData(BaseModel):
    collection_method: str
    network_configuration_data: str = Field(
        ...,
        description="Pipe-delimited CSV as raw string"
    )
    user_plane_data: str = Field(
        ...,
        description="Pipe-delimited CSV as raw string"
    )
    signaling_plane_data: Optional[str] = Field(
        default=None,
        description="Pipe-delimited CSV as raw string"
    )
    traffic_data: Optional[str] = Field(
        default=None,
        description="Pipe-delimited CSV as raw string"
    )
    mr_data: Optional[str] = Field(
        default=None,
        description="Pipe-delimited CSV as raw string"
    )
    notes: Optional[str] = None


# ------------------------------------------------------------------------------
# Tools metadata
# ------------------------------------------------------------------------------

class ToolsMetadata(BaseModel):
    capabilities: List[str]
    description: str


# ------------------------------------------------------------------------------
# Expected output
# ------------------------------------------------------------------------------

class ExpectedOutputContent(BaseModel):
    evidence: str
    findings: str
    recommendations: str


class ExpectedOutput(BaseModel):
    content: ExpectedOutputContent
    type: str


# ------------------------------------------------------------------------------
# Scenario (top-level)
# ------------------------------------------------------------------------------

class Scenario(BaseModel):
    scenario_id: str
    answer: str = Field(..., description="Correct root cause ID, e.g. C6")
    task: Task
    context: Context
    data: ScenarioData
    tools: ToolsMetadata
    expected_output: Optional[ExpectedOutput] = None
    steps: Optional[List[str]] = None
