from typing import Literal

from pydantic import BaseModel, Field


ValidationSeverity = Literal["error", "warning", "info", "usage"]
CoverPreset = Literal["kdp", "apple", "kobo"]
ConversionTarget = Literal["epub", "mobi", "azw3", "pdf", "html"]
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


class Contributor(BaseModel):
    name: str
    role: str = "aut"


class Identifier(BaseModel):
    type: str
    value: str


class EpubMetadata(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    contributors: list[Contributor] = Field(default_factory=list)
    language: str | None = None
    identifiers: list[Identifier] = Field(default_factory=list)
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


class MetadataUpdateRequest(BaseModel):
    jobId: str
    metadata: EpubMetadata
    coverImageDataUrl: str | None = None
    coverPreset: CoverPreset = "kdp"


class MetadataUpdateResult(BaseModel):
    jobId: str
    validation: "ValidationResult"


class ConversionOptions(BaseModel):
    tocDepth: int | None = None
    embedFonts: bool = False
    stripCss: bool = False
    pageSize: str | None = None


class ConversionRequest(BaseModel):
    jobId: str
    target: ConversionTarget
    options: ConversionOptions = Field(default_factory=ConversionOptions)


class ConversionResult(BaseModel):
    jobId: str
    target: ConversionTarget
    artifactUrl: str
    log: str


class StructureChange(BaseModel):
    path: str
    change: Literal["added", "removed", "changed"]


class MetadataChange(BaseModel):
    field: str
    before: str | None = None
    after: str | None = None


class ChapterDiff(BaseModel):
    path: str
    before: str | None = None
    after: str | None = None


class DiffResult(BaseModel):
    structure: list[StructureChange]
    metadata: list[MetadataChange]
    chapters: list[ChapterDiff]


class UnpackEntry(BaseModel):
    path: str
    kind: Literal["xhtml", "css", "image", "xml", "opf", "ncx", "font", "text", "binary"]
    size: int


class UnpackPreview(BaseModel):
    path: str
    kind: Literal["xhtml", "css", "image", "xml", "opf", "ncx", "font", "text", "binary"]
    text: str | None = None
    dataUrl: str | None = None


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
