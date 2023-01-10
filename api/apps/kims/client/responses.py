from datetime import datetime

from black import List
from pydantic import BaseModel, Field


class TagData(BaseModel):
    name: str = Field(alias='Name')
    description: str = Field(alias='Description')
    eng_unit: str | None = Field(alias='EngUnit')
    data_type: str = Field(alias='DataType')
    data_reference: str = Field(alias='DataReference')
    oldest_value_date: str | None = Field(alias='OldestValueDate')


class TagsData(BaseModel):
    context: str = Field(alias='@odata.context')
    value: List[TagData]


class StatisticsData(BaseModel):
    type: str = Field(alias="Type")
    value: str | None = Field(alias='Value')
    quality: str = Field(alias='Quality')
    quality_info: str = Field(alias='QualityInfo')


class CalculatedValueData(BaseModel):
    timestamp: datetime = Field(alias='Timestamp')
    statistics: List[StatisticsData] = Field(alias='Statistics', default_factory=list)

    class Config:
        json_decoders = {
            datetime: lambda n: datetime.strptime(n, '%Y-%m-%dT%H:%M:%S.%fZ'),
        }


class CalculatedValuesData(BaseModel):
    context: str = Field(alias='@odata.context')
    value: List[CalculatedValueData]
