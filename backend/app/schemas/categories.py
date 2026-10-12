from pydantic import BaseModel, ConfigDict, Field


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str = Field(examples=["games"])
    title: str = Field(examples=["Игры"])
