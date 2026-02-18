# langgraph_workflow.py
from typing import TypedDict, Annotated, Sequence
import operator
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI

from rag import build_rag_chain
from vector import create_or_load_vectorstore

# ------------------- Initialize Models -------------------
vectorstore = create_or_load_vectorstore()
rag_chain, retriever = build_rag_chain(vectorstore)
model = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.3)

# ------------------- State -------------------
class AgentState(TypedDict):
    messages: Annotated[Sequence[str], operator.add]
    route: str  # New key to store "RAG" or "LLM"

# ------------------- Classification -------------------
class QueryClassifier(BaseModel):
    Category: str = Field(description="Either 'RAG' or 'LLM'")

parser = PydanticOutputParser(pydantic_object=QueryClassifier)

def supervisor_node(state: AgentState):
    """Decide if query should go to RAG or LLM."""
    question = state["messages"][-1]
    template = """
    Classify the user question as:
    - 'RAG' if it is about cardiology, medical knowledge, symptoms, treatments, or diseases.
    - 'LLM' if it is general or unrelated to medical topics.

    {format_instructions}
    Question: {question}
    """
    prompt = PromptTemplate(
        template=template,
        input_variables=["question"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    chain = prompt | model | parser
    response = chain.invoke({"question": question})

    # Add route to state without changing the original query
    return {"messages": [question], "route": response.Category}

# ------------------- RAG Node -------------------
def rag_node(state: AgentState):
    question = state["messages"][-1]
    docs = retriever.invoke(question)
    if not docs:
        return {"messages": ["I'm sorry, I couldn't find medical information about this."]}
    context = "\n\n".join([d.page_content for d in docs])
    response = rag_chain.invoke({"context": context, "input": question})
    return {"messages": [response["answer"]]}

# ------------------- LLM Node -------------------
def llm_node(state: AgentState):
    question = state["messages"][-1]
    response = model.invoke(f"Answer this question in a helpful way: {question}")
    return {"messages": [response.content]}

# ------------------- Router -------------------
def router(state: AgentState):
    return "rag_node" if state.get("route") == "RAG" else "llm_node"

# ------------------- Workflow -------------------
workflow = StateGraph(AgentState)
workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("rag_node", rag_node)
workflow.add_node("llm_node", llm_node)

workflow.set_entry_point("Supervisor")
workflow.add_conditional_edges("Supervisor", router, {
    "rag_node": "rag_node",
    "llm_node": "llm_node",
})
workflow.add_edge("rag_node", END)
workflow.add_edge("llm_node", END)

app = workflow.compile()
