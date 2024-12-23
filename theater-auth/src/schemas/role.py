from pydantic import BaseModel, field_validator


class RolePermissions(BaseModel):
    view_regular_movies: bool
    view_premium_movies: bool
    create_movies: bool
    edit_movies: bool
    delete_movies: bool


class Role(BaseModel):
    name: str
    permissions: RolePermissions

    def __str__(self):
        return self.name


class UpdateRole(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def role_must_exists(cls, v: str) -> str:
        from services.roles import Roles

        if v not in Roles.roles():
            raise ValueError("Role does not exists")
        return v
