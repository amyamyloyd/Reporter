# AutoGen to LangChain Agent Migration Guide

## Overview
This document provides a comprehensive analysis of the existing AutoGen agent system and a detailed migration strategy to LangChain with built-in agent registry and contracts. The migration leverages LangChain's superior agent management, tool integration, and orchestration capabilities.

## Current AutoGen Agent Architecture

### Agent Hierarchy and Responsibilities

```
AgentOrchestrator (Singleton)
├── ChatAgent (Entry Point)
├── OrchestrationAgent (Router)
└── Specialized Agents
    ├── QueryAgent (SQL Generation)
    ├── ReportAgent (Report Building)
    ├── UploadAgent (Metadata Enrichment)
    └── MemoryAgent (Data Retrieval)
```

### Current Agent Analysis

#### 1. **AgentOrchestrator** (Main Coordinator)
**Current Implementation**:
- Singleton pattern for global access
- Manages all agent instances
- Coordinates agent conversations
- Handles frontend requests
- Maintains agent registry for routing

**Responsibilities**:
- Initialize all agents on startup
- Route user messages through agent pipeline
- Manage agent state and lifecycle
- Provide agent status monitoring

**Current Issues**:
- Tight coupling between agents
- Manual conversation orchestration
- No built-in error recovery
- Limited scalability

#### 2. **ChatAgent** (Entry Point)
**Current Implementation**:
- ConversableAgent with GPT-4
- Processes natural language input
- Structures input for routing
- Injects localStorage context

**Responsibilities**:
- Accept user natural language input
- Parse prompts into structured dictionaries
- Inject frontend context (doc_id, schema, metadata)
- Send structured requests to OrchestrationAgent

**Current Issues**:
- Limited conversation memory
- No context persistence
- Basic input validation
- No conversation history management

#### 3. **OrchestrationAgent** (Router)
**Current Implementation**:
- ConversableAgent with routing logic
- Uses agent_router.py utility
- Routes to specialized agents
- Handles disambiguation

**Responsibilities**:
- Receive structured input from ChatAgent
- Determine target agent based on intent
- Route requests to appropriate agents
- Handle unclear routing scenarios

**Current Issues**:
- Manual routing logic
- No dynamic agent discovery
- Limited fallback mechanisms
- No load balancing

#### 4. **QueryAgent** (SQL Generation)
**Current Implementation**:
- ConversableAgent with DuckDB integration
- Converts natural language to SQL
- Executes queries via DuckDB
- Returns structured results

**Responsibilities**:
- Convert query intent to SQL
- Execute SQL via DuckDB
- Return structured results (sql, rows, columns, summary)
- Auto-save queries as temp_query

**Current Issues**:
- No query optimization
- Limited error handling
- No query caching
- Basic SQL validation

#### 5. **ReportAgent** (Report Building)
**Current Implementation**:
- ConversableAgent with report_builder.py
- Interprets report specifications
- Builds grouped/filtered reports
- Supports multiple output formats

**Responsibilities**:
- Interpret report specifications
- Use report_builder.py for assembly
- Save to JSON and saved_reports
- Return HTML, XLSX, or JSON output

**Current Issues**:
- Limited report templates
- No dynamic formatting
- Basic error handling
- No report caching

#### 6. **UploadAgent** (Metadata Enrichment)
**Current Implementation**:
- ConversableAgent for post-upload processing
- Enriches file metadata
- Updates document registry
- Manages file context

**Responsibilities**:
- Process files after upload
- Prompt user for file description
- Update JSON metadata
- Update doc_registry

**Current Issues**:
- Limited metadata validation
- No batch processing
- Basic error recovery
- No metadata versioning

#### 7. **MemoryAgent** (Data Retrieval)
**Current Implementation**:
- ConversableAgent with DuckDB queries
- Retrieves saved queries and reports
- Searches by doc_id, query_name, tags
- Returns full SQL or report definitions

**Responsibilities**:
- Fetch saved queries from DuckDB
- Search saved reports
- Return complete definitions
- Support tag-based search

**Current Issues**:
- Limited search capabilities
- No semantic search
- Basic caching
- No query optimization

## LangChain Migration Strategy

### Why LangChain is Superior

1. **Built-in Agent Registry**: Centralized agent management with discovery
2. **Agent Contracts**: Standardized interfaces and protocols
3. **Tool Integration**: Seamless function calling and tool management
4. **Memory Management**: Built-in conversation and context persistence
5. **Error Handling**: Robust error recovery and fallback mechanisms
6. **Scalability**: Better support for distributed and microservice architectures
7. **Monitoring**: Built-in observability and logging
8. **Testing**: Comprehensive testing frameworks and mocking

### LangChain Agent Architecture

```
LangChain Agent System
├── Agent Registry (Central Management)
├── Agent Contracts (Standardized Interfaces)
├── Tool Registry (Function Integration)
├── Memory Manager (Context Persistence)
└── Specialized Agents
    ├── QueryAgent (ReAct + Tools)
    ├── ReportAgent (Plan-and-Execute)
    ├── UploadAgent (ReAct + Tools)
    └── MemoryAgent (Retrieval + Tools)
```

### Migration Implementation Plan

#### Phase 1: Agent Registry Setup
**Deliverable**: Centralized agent registry with contracts

```python
from langchain.agents import AgentRegistry, AgentContract
from langchain.tools import Tool
from typing import Dict, Any, List

class ExcelReportingAgentRegistry:
    """Centralized agent registry for Excel Reporting POC"""
    
    def __init__(self):
        self.registry = AgentRegistry()
        self.contracts = {}
        self.tools = {}
        self._setup_agent_contracts()
        self._setup_tools()
    
    def _setup_agent_contracts(self):
        """Define standardized agent contracts"""
        
        # Query Agent Contract
        self.contracts["QueryAgent"] = AgentContract(
            name="QueryAgent",
            description="Converts natural language to SQL and executes queries",
            input_schema={
                "doc_id": str,
                "query_text": str,
                "schema": List[str],
                "metadata": Dict[str, Any]
            },
            output_schema={
                "sql": str,
                "rows": List[List[Any]],
                "columns": List[str],
                "summary": str
            },
            tools=["sql_generator", "query_executor", "query_saver"],
            memory_type="conversation"
        )
        
        # Report Agent Contract
        self.contracts["ReportAgent"] = AgentContract(
            name="ReportAgent",
            description="Generates reports with filters, grouping, and formatting",
            input_schema={
                "doc_id": str,
                "report_name": str,
                "filters": Dict[str, Any],
                "group_by": List[str],
                "aggregations": Dict[str, str]
            },
            output_schema={
                "report_name": str,
                "sql": str,
                "rows": List[List[Any]],
                "columns": List[str],
                "summary": str
            },
            tools=["report_builder", "sql_generator", "report_saver"],
            memory_type="conversation"
        )
        
        # Upload Agent Contract
        self.contracts["UploadAgent"] = AgentContract(
            name="UploadAgent",
            description="Enriches file metadata after upload",
            input_schema={
                "file_path": str,
                "metadata": Dict[str, Any],
                "user_description": str
            },
            output_schema={
                "enriched_metadata": Dict[str, Any],
                "doc_id": str,
                "classification": Dict[str, Any]
            },
            tools=["metadata_extractor", "classifier", "metadata_saver"],
            memory_type="session"
        )
        
        # Memory Agent Contract
        self.contracts["MemoryAgent"] = AgentContract(
            name="MemoryAgent",
            description="Retrieves and manages saved queries and reports",
            input_schema={
                "doc_id": str,
                "query_name": str,
                "tags": List[str],
                "search_type": str
            },
            output_schema={
                "queries": List[Dict[str, Any]],
                "reports": List[Dict[str, Any]],
                "total_count": int
            },
            tools=["query_retriever", "report_retriever", "search_engine"],
            memory_type="persistent"
        )
    
    def _setup_tools(self):
        """Register all available tools"""
        
        # SQL Generation Tool
        self.tools["sql_generator"] = Tool(
            name="sql_generator",
            description="Generate SQL from natural language query",
            func=self._generate_sql
        )
        
        # Query Execution Tool
        self.tools["query_executor"] = Tool(
            name="query_executor",
            description="Execute SQL query via DuckDB",
            func=self._execute_query
        )
        
        # Report Builder Tool
        self.tools["report_builder"] = Tool(
            name="report_builder",
            description="Build report with filters and grouping",
            func=self._build_report
        )
        
        # Metadata Extractor Tool
        self.tools["metadata_extractor"] = Tool(
            name="metadata_extractor",
            description="Extract metadata from Excel files",
            func=self._extract_metadata
        )
        
        # Query Retriever Tool
        self.tools["query_retriever"] = Tool(
            name="query_retriever",
            description="Retrieve saved queries from database",
            func=self._retrieve_queries
        )
    
    def register_agent(self, agent_name: str, agent_instance):
        """Register agent with the registry"""
        contract = self.contracts.get(agent_name)
        if not contract:
            raise ValueError(f"No contract found for agent: {agent_name}")
        
        self.registry.register(
            name=agent_name,
            agent=agent_instance,
            contract=contract
        )
    
    def get_agent(self, agent_name: str):
        """Get agent from registry"""
        return self.registry.get(agent_name)
    
    def list_agents(self) -> List[str]:
        """List all registered agents"""
        return self.registry.list_agents()
```

#### Phase 2: Agent Implementation with LangChain

**QueryAgent Migration**:
```python
from langchain.agents import ReActAgent, create_react_agent
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.tools import Tool

class QueryAgent:
    """LangChain-based Query Agent with ReAct pattern"""
    
    def __init__(self, registry: ExcelReportingAgentRegistry):
        self.registry = registry
        self.llm = OpenAI(temperature=0.1, model="gpt-4")
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Get tools from registry
        tools = [
            registry.tools["sql_generator"],
            registry.tools["query_executor"],
            registry.tools["query_saver"]
        ]
        
        # Create ReAct agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=tools,
            prompt=self._create_prompt()
        )
    
    def _create_prompt(self):
        """Create ReAct prompt for query agent"""
        return """
        You are a SQL query expert. Your job is to:
        1. Understand the user's natural language query
        2. Generate appropriate SQL using the sql_generator tool
        3. Execute the query using the query_executor tool
        4. Save the query using the query_saver tool
        
        Always provide a clear summary of the results.
        
        Available tools:
        - sql_generator: Generate SQL from natural language
        - query_executor: Execute SQL query via DuckDB
        - query_saver: Save query to database
        
        Use the following format:
        Question: {input}
        Thought: I need to understand what the user wants to query
        Action: sql_generator
        Action Input: {query_text}
        Observation: {tool_output}
        Thought: Now I'll execute the SQL
        Action: query_executor
        Action Input: {sql}
        Observation: {query_results}
        Thought: I'll save this query for future use
        Action: query_saver
        Action Input: {query_data}
        Observation: {save_result}
        Final Answer: {summary}
        """
    
    async def process_query(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process query request using ReAct pattern"""
        try:
            # Format input for agent
            formatted_input = self._format_input(input_data)
            
            # Run agent
            result = await self.agent.arun(
                input=formatted_input,
                memory=self.memory
            )
            
            return {
                "success": True,
                "result": result,
                "agent": "QueryAgent"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": "QueryAgent"
            }
```

**ReportAgent Migration**:
```python
from langchain.agents import PlanAndExecuteAgent, create_plan_and_execute_agent
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory

class ReportAgent:
    """LangChain-based Report Agent with Plan-and-Execute pattern"""
    
    def __init__(self, registry: ExcelReportingAgentRegistry):
        self.registry = registry
        self.llm = OpenAI(temperature=0.1, model="gpt-4")
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Get tools from registry
        tools = [
            registry.tools["report_builder"],
            registry.tools["sql_generator"],
            registry.tools["report_saver"]
        ]
        
        # Create Plan-and-Execute agent
        self.agent = create_plan_and_execute_agent(
            llm=self.llm,
            tools=tools,
            memory=self.memory
        )
    
    async def process_report(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process report request using Plan-and-Execute pattern"""
        try:
            # Format input for agent
            formatted_input = self._format_input(input_data)
            
            # Run agent
            result = await self.agent.arun(
                input=formatted_input
            )
            
            return {
                "success": True,
                "result": result,
                "agent": "ReportAgent"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": "ReportAgent"
            }
```

#### Phase 3: Tool Integration

**Tool Implementation**:
```python
from langchain.tools import BaseTool
from typing import Dict, Any, List
import json

class SQLGeneratorTool(BaseTool):
    """Tool for generating SQL from natural language"""
    
    name = "sql_generator"
    description = "Generate SQL query from natural language description"
    
    def _run(self, query_text: str, schema: List[str], doc_id: str) -> str:
        """Generate SQL from natural language"""
        try:
            # Use LLM to generate SQL
            prompt = f"""
            Generate SQL for the following query:
            Query: {query_text}
            Schema: {', '.join(schema)}
            Table: {doc_id}
            
            Return only the SQL query, no explanations.
            """
            
            # Call LLM (implementation depends on your LLM setup)
            sql = self._call_llm(prompt)
            
            return sql
            
        except Exception as e:
            return f"Error generating SQL: {str(e)}"
    
    async def _arun(self, query_text: str, schema: List[str], doc_id: str) -> str:
        """Async version of SQL generation"""
        return self._run(query_text, schema, doc_id)

class QueryExecutorTool(BaseTool):
    """Tool for executing SQL queries via DuckDB"""
    
    name = "query_executor"
    description = "Execute SQL query via DuckDB and return results"
    
    def _run(self, sql: str, doc_id: str) -> str:
        """Execute SQL query"""
        try:
            # Import your DuckDB manager
            from utils.duckdb_manager import create_persistent_database
            
            conn = create_persistent_database()
            result = conn.execute(sql).fetchall()
            columns = [desc[0] for desc in conn.description]
            
            return json.dumps({
                "rows": result,
                "columns": columns,
                "row_count": len(result)
            })
            
        except Exception as e:
            return f"Error executing query: {str(e)}"
    
    async def _arun(self, sql: str, doc_id: str) -> str:
        """Async version of query execution"""
        return self._run(sql, doc_id)
```

#### Phase 4: Memory Management

**Memory Implementation**:
```python
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.llms import OpenAI
from typing import Dict, Any

class AgentMemoryManager:
    """Centralized memory management for all agents"""
    
    def __init__(self):
        self.llm = OpenAI(temperature=0.1)
        self.memories = {}
    
    def get_memory(self, agent_name: str, memory_type: str = "conversation") -> Any:
        """Get memory instance for agent"""
        key = f"{agent_name}_{memory_type}"
        
        if key not in self.memories:
            if memory_type == "conversation":
                self.memories[key] = ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True
                )
            elif memory_type == "summary":
                self.memories[key] = ConversationSummaryMemory(
                    llm=self.llm,
                    memory_key="chat_history",
                    return_messages=True
                )
            elif memory_type == "session":
                self.memories[key] = ConversationBufferMemory(
                    memory_key="session_history",
                    return_messages=True
                )
        
        return self.memories[key]
    
    def clear_memory(self, agent_name: str, memory_type: str = "conversation"):
        """Clear memory for specific agent"""
        key = f"{agent_name}_{memory_type}"
        if key in self.memories:
            self.memories[key].clear()
    
    def get_memory_summary(self, agent_name: str) -> Dict[str, Any]:
        """Get memory summary for agent"""
        key = f"{agent_name}_conversation"
        if key in self.memories:
            memory = self.memories[key]
            return {
                "message_count": len(memory.chat_history.messages),
                "memory_type": "conversation",
                "last_activity": memory.chat_history.messages[-1].timestamp if memory.chat_history.messages else None
            }
        return {"message_count": 0, "memory_type": "none"}

```

#### Phase 5: Error Handling and Recovery

**Error Handling Implementation**:
```python
from langchain.agents import AgentExecutor
from langchain.agents.agent import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish
from typing import Union, Dict, Any
import logging

class ExcelReportingOutputParser(AgentOutputParser):
    """Custom output parser with error handling"""
    
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """Parse agent output with error handling"""
        try:
            # Parse the output
            if "Final Answer:" in text:
                return AgentFinish(
                    return_values={"output": text.split("Final Answer:")[-1].strip()},
                    log=text
                )
            else:
                # Extract action and action input
                action_match = re.search(r"Action: (.*)", text)
                action_input_match = re.search(r"Action Input: (.*)", text)
                
                if action_match and action_input_match:
                    return AgentAction(
                        tool=action_match.group(1).strip(),
                        tool_input=action_input_match.group(1).strip(),
                        log=text
                    )
                else:
                    return AgentFinish(
                        return_values={"output": "I couldn't understand the request. Please try again."},
                        log=text
                    )
                    
        except Exception as e:
            logging.error(f"Error parsing agent output: {e}")
            return AgentFinish(
                return_values={"output": f"Error processing request: {str(e)}"},
                log=text
            )

class RobustAgentExecutor(AgentExecutor):
    """Agent executor with enhanced error handling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Run agent with retry logic"""
        for attempt in range(self.max_retries):
            try:
                result = await super().arun(*args, **kwargs)
                return result
            except Exception as e:
                logging.warning(f"Agent execution attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": f"Agent execution failed after {self.max_retries} attempts: {str(e)}"
                    }
                await asyncio.sleep(self.retry_delay * (attempt + 1))
```

### Migration Benefits

#### 1. **Agent Registry Advantages**
- **Centralized Management**: Single source of truth for all agents
- **Dynamic Discovery**: Agents can be registered/unregistered at runtime
- **Contract Enforcement**: Standardized interfaces ensure consistency
- **Health Monitoring**: Built-in agent health checks and status monitoring

#### 2. **Tool Integration Benefits**
- **Seamless Function Calling**: Direct integration with internal functions
- **Tool Composition**: Easy combination of multiple tools
- **Error Handling**: Built-in tool error handling and recovery
- **Performance Monitoring**: Tool execution metrics and optimization

#### 3. **Memory Management Improvements**
- **Persistent Context**: Conversation history survives across sessions
- **Context Summarization**: Automatic conversation summarization for long sessions
- **Memory Types**: Different memory types for different use cases
- **Memory Optimization**: Efficient memory usage and cleanup

#### 4. **Error Handling and Recovery**
- **Automatic Retries**: Built-in retry logic with exponential backoff
- **Fallback Mechanisms**: Graceful degradation when agents fail
- **Error Classification**: Categorized error handling for different failure types
- **Recovery Strategies**: Automatic recovery from common failure scenarios

#### 5. **Scalability and Performance**
- **Async Support**: Full async/await support for better performance
- **Load Balancing**: Built-in load balancing for multiple agent instances
- **Caching**: Intelligent caching of agent responses and tool results
- **Resource Management**: Efficient resource usage and cleanup

### Testing Strategy

#### 1. **Unit Tests**
```python
import pytest
from unittest.mock import Mock, patch
from agents.query_agent import QueryAgent

class TestQueryAgent:
    """Unit tests for QueryAgent"""
    
    @pytest.fixture
    def query_agent(self):
        registry = Mock()
        return QueryAgent(registry)
    
    @pytest.mark.asyncio
    async def test_process_query_success(self, query_agent):
        """Test successful query processing"""
        input_data = {
            "doc_id": "test_doc",
            "query_text": "Show me all records",
            "schema": ["id", "name", "value"]
        }
        
        with patch.object(query_agent.agent, 'arun') as mock_run:
            mock_run.return_value = "SELECT * FROM test_doc"
            
            result = await query_agent.process_query(input_data)
            
            assert result["success"] == True
            assert result["agent"] == "QueryAgent"
    
    @pytest.mark.asyncio
    async def test_process_query_error(self, query_agent):
        """Test query processing error handling"""
        input_data = {
            "doc_id": "test_doc",
            "query_text": "Invalid query",
            "schema": []
        }
        
        with patch.object(query_agent.agent, 'arun') as mock_run:
            mock_run.side_effect = Exception("Test error")
            
            result = await query_agent.process_query(input_data)
            
            assert result["success"] == False
            assert "error" in result
```

#### 2. **Integration Tests**
```python
import pytest
from agents.agent_registry import ExcelReportingAgentRegistry

class TestAgentIntegration:
    """Integration tests for agent system"""
    
    @pytest.fixture
    def registry(self):
        return ExcelReportingAgentRegistry()
    
    def test_agent_registration(self, registry):
        """Test agent registration and retrieval"""
        # Register test agent
        test_agent = Mock()
        registry.register_agent("TestAgent", test_agent)
        
        # Verify registration
        assert "TestAgent" in registry.list_agents()
        assert registry.get_agent("TestAgent") == test_agent
    
    def test_contract_enforcement(self, registry):
        """Test agent contract enforcement"""
        # Test valid agent
        valid_agent = Mock()
        registry.register_agent("QueryAgent", valid_agent)
        
        # Test invalid agent
        with pytest.raises(ValueError):
            registry.register_agent("InvalidAgent", Mock())
```

#### 3. **End-to-End Tests**
```python
import pytest
from agents.agent_orchestrator import LangChainAgentOrchestrator

class TestEndToEnd:
    """End-to-end tests for complete agent system"""
    
    @pytest.fixture
    def orchestrator(self):
        return LangChainAgentOrchestrator()
    
    @pytest.mark.asyncio
    async def test_complete_query_workflow(self, orchestrator):
        """Test complete query workflow from input to output"""
        user_input = "How much did we spend on Vendor X in Q2?"
        context = {
            "doc_id": "hospital_ledger_fy2024_001",
            "schema": ["Vendor", "Date", "Amount"],
            "metadata": {"record_count": 1200}
        }
        
        result = await orchestrator.process_user_message(user_input, context)
        
        assert result["success"] == True
        assert "sql" in result
        assert "rows" in result
        assert "summary" in result
```

### Migration Timeline

#### Week 1-2: Foundation Setup
- [ ] Set up LangChain agent registry
- [ ] Implement agent contracts
- [ ] Create tool integration framework
- [ ] Set up memory management

#### Week 3-4: Agent Migration
- [ ] Migrate QueryAgent to LangChain ReAct
- [ ] Migrate ReportAgent to Plan-and-Execute
- [ ] Migrate UploadAgent to ReAct with tools
- [ ] Migrate MemoryAgent to Retrieval pattern

#### Week 5-6: Integration and Testing
- [ ] Integrate all agents with registry
- [ ] Implement error handling and recovery
- [ ] Create comprehensive test suite
- [ ] Performance optimization

#### Week 7-8: Deployment and Monitoring
- [ ] Deploy new agent system
- [ ] Set up monitoring and logging
- [ ] Performance testing and optimization
- [ ] Documentation and training

### Success Metrics

#### 1. **Functional Metrics**
- [ ] 100% feature parity with AutoGen system
- [ ] All existing workflows work without modification
- [ ] Error rates reduced by 50%
- [ ] Response times improved by 30%

#### 2. **Technical Metrics**
- [ ] Agent registry supports 10+ agents
- [ ] Tool integration supports 20+ tools
- [ ] Memory management handles 1000+ conversations
- [ ] Error recovery success rate > 95%

#### 3. **Operational Metrics**
- [ ] Deployment time reduced by 70%
- [ ] Monitoring coverage increased to 100%
- [ ] Test coverage > 90%
- [ ] Documentation completeness > 95%

This comprehensive migration strategy provides a clear path from the current AutoGen system to a more robust, scalable, and maintainable LangChain-based agent system with built-in registry, contracts, and advanced orchestration capabilities.
