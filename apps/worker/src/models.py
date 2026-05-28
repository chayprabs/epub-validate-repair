from typing import Literal

from pydantic import BaseModel, Field


ValidationSeverity = Literal["error", "warning", "info", "usage"]
RepairFixId = Literal[
    "manifest-mismatch",
    "spine-reference",
    "toc-document",
    "invalid-xhtml",
    "mimetype-entry",
    "missing-cover",
    "container-xml",
]


class EpubcheckMessage(BaseModel):
    id: str
    severity: ValidationSeverity
    message: str
    file: str
    line: int | None = None
    column: int | None = None
    suggestion: str | None = None
    fixableBy: str | None = None


class ManifestItem(BaseModel):
    id: str
    href: str
    mediaType: str


class SpineItem(BaseModel):
    idref: str
    href: str | None = None


class TocItem(BaseModel):
    label: str
    href: str
    children: list["TocItem"] = Field(default_factory=list)


class EpubMetadata(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    contributors: list[str] = Field(default_factory=list)
    language: str | None = None
    identifiers: list[str] = Field(default_factory=list)
    publisher: str | None = None
    publishedAt: str | None = None
    description: str | None = None
    subjects: list[str] = Field(default_factory=list)
    rights: str | None = None
    series: str | None = None
    seriesIndex: str | None = None
    custom: dict[str, str] = Field(default_factory=dict)


class ValidationArtifacts(BaseModel):
    htmlUrl: str
    jsonUrl: str


class RepairRecipe(BaseModel):
    id: RepairFixId
    label: str
    description: str


class RepairRequest(BaseModel):
    jobId: str
    fixes: list[RepairFixId]


class RepairResult(BaseModel):
    jobId: str
    appliedFixes: list[RepairFixId]
    validation: "ValidationResult"


class ValidationResult(BaseModel):
    jobId: str
    epubVersion: Literal["2.0", "3.0", "3.1", "3.2", "3.3"] = "3.0"
    pass_: bool = Field(alias="pass")
    counts: dict[ValidationSeverity, int]
    messages: list[EpubcheckMessage]
    metadata: EpubMetadata
    spine: list[SpineItem]
    manifest: list[ManifestItem]
    toc: list[TocItem]
    artifacts: ValidationArtifacts

    model_config = {
        "populate_by_name": True
    }
