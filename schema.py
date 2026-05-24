from pydantic import BaseModel, Field
from typing_extensions import TypedDict, Literal
from langgraph.graph import MessagesState

class State(MessagesState):
    Request: str
    classification_decision: Literal["News", "Review", "Guide", "Event", "Advice"]


class ContentRouterSchema(BaseModel):
    """Classifies and routes user requests based on intent."""

    reasoning: str = Field(
        description="Short justification for the classification."
    )

    classification: Literal["News", "Review", "Guide", "Event", "Advice"] = Field(
    description=(
            "The classification of the request content: "
            "'News' for updates, announcements, trailers, industry rumors, or recent information; "
            "'Review' for detailed evaluations, scores, opinions, or pros/cons about video games or hardware; "
            "'Guide' for functional step-by-step instructions, walkthroughs, gameplay help, puzzles, or unlock mechanics; "
            "'Event' for schedules, conferences, showcases, tournaments, or upcoming gaming activities with specific dates; "
            "'Advice' for creative brainstorming, future topic ideas, editorials, or strategic content guidance."
        ),
    )