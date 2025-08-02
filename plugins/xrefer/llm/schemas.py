# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Pydantic schemas for structured LLM output.

This module defines the expected response schemas for each prompt type,
enabling the use of LangChain's .with_structured_output() method to
ensure reliable JSON responses from language models.
"""

from typing import Dict, List
from pydantic import BaseModel, Field


class CategorizerResponse(BaseModel):
    """
    Schema for categorizer prompt responses.
    
    The categorizer expects a mapping of item indices to category indices.
    """
    category_assignments: Dict[str, int] = Field(
        description="Mapping of item indices (as strings) to category indices (as integers)"
    )


class ArtifactAnalyzerResponse(BaseModel):
    """
    Schema for artifact analyzer prompt responses.
    
    The artifact analyzer expects a list of interesting artifact indices.
    """
    interesting_indexes: List[int] = Field(
        description="List of indices for artifacts identified as interesting"
    )


class ClusterAnalysis(BaseModel):
    """
    Schema for individual cluster analysis within cluster analyzer response.
    """
    label: str = Field(description="Short name indicating the cluster's functionality")
    description: str = Field(description="Short summary of what the cluster appears to do")
    relationships: str = Field(description="How it interacts with referenced clusters")
    function_prefix: str = Field(description="One word prefix for functions in this cluster")


class ClusterAnalyzerResponse(BaseModel):
    """
    Schema for cluster analyzer prompt responses.
    
    The cluster analyzer expects detailed analysis of function clusters
    along with overall binary assessment.
    """
    clusters: Dict[str, ClusterAnalysis] = Field(
        description="Dictionary mapping cluster IDs to their analysis"
    )
    binary_description: str = Field(
        description="Overall description of the binary based on cluster analysis"
    )
    binary_category: str = Field(
        description="Category classification for the binary"
    )
    binary_report: str = Field(
        description="Detailed technical report about the malware's capabilities and functionality"
    )
