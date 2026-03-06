import re
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime

# Validation patterns
_USERNAME_RE = re.compile(r'^[A-Za-z0-9@.]+$')
_EXCLUDE_RULE_RE = re.compile(r'^[a-z.\-]+$')
_PROJECT_NAME_RE = re.compile(r'^[A-Za-z0-9/_-]+$')


def validate_exclude_rules_str(value: str):
    """Raise ValueError if any comma-separated rule contains invalid characters."""
    for rule in value.split(","):
        rule = rule.strip()
        if rule and not _EXCLUDE_RULE_RE.match(rule):
            raise ValueError(
                f"Exclude rule '{rule}' is invalid. "
                "Rules may only contain lowercase letters (a-z), '.', and '-'."
            )
    return value

# User Schemas
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    role: str = "user"

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not _USERNAME_RE.match(v):
            raise ValueError(
                "Username may only contain letters (A-Z, a-z), numbers, '@', and '.'"
            )
        return v

class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class User(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Existing Schemas
class ScanResultBase(BaseModel):
    scan_date: Optional[datetime] = None
    result_json: dict

class ScanResultCreate(ScanResultBase):
    pass

class ScanResult(ScanResultBase):
    id: int
    project_id: int
    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    github_url: str
    local_path: Optional[str] = None
    exclude_rules: str = ""
    include_rules_yaml: str = ""
    apply_global_exclude: bool = False
    apply_global_include: bool = False


class ProjectCreate(BaseModel):
    github_url: str
    exclude_rules: str = ""
    include_rules_yaml: str = ""
    apply_global_exclude: bool = False
    apply_global_include: bool = False
    integration_id: Optional[int] = None

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        # Strip trailing slash and .git suffix, then extract org/repo segments
        normalized = v.rstrip("/").removesuffix(".git")
        parts = [p for p in normalized.split("/") if p and ":" not in p]
        if len(parts) < 2:
            raise ValueError("GitHub URL must include an org/repo path (e.g. https://github.com/org/repo)")
        project_name = "/".join(parts[-2:])
        if not _PROJECT_NAME_RE.match(project_name):
            raise ValueError(
                "Project name (org/repo) may only contain letters (A-Z, a-z), numbers, '/', and '-'"
            )
        return v

    @field_validator("exclude_rules")
    @classmethod
    def validate_exclude_rules(cls, v: str) -> str:
        if v:
            validate_exclude_rules_str(v)
        return v

class Project(ProjectBase):
    id: int
    created_at: datetime
    integration_id: Optional[int] = None
    scans: List[ScanResult] = []
    class Config:
        from_attributes = True

# Global Configuration Schemas
class GlobalConfigBase(BaseModel):
    key: str
    value: str

class GlobalConfigCreate(GlobalConfigBase):
    pass

class GlobalConfig(GlobalConfigBase):
    id: int
    updated_at: datetime
    class Config:
        from_attributes = True

# GitHub Integration Schemas
class GitHubIntegrationBase(BaseModel):
    org_name: str

class GitHubIntegrationCreate(GitHubIntegrationBase):
    access_token: str
    organizations: Optional[List[str]] = []

class GitHubIntegration(GitHubIntegrationBase):
    id: int
    organizations: Optional[List[str]] = []
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class GitHubRepository(BaseModel):
    name: str
    full_name: str
    html_url: str
    clone_url: str
    description: Optional[str] = None
    language: Optional[str] = None
    default_branch: str

class GitHubRepositoriesResponse(BaseModel):
    repositories: List[GitHubRepository]
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
