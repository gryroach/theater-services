from schemas.role import Role, RolePermissions


class Roles:
    admin = Role(
        name="admin",
        permissions=RolePermissions(
            view_regular_movies=True,
            view_premium_movies=True,
            create_movies=True,
            edit_movies=True,
            delete_movies=True,
        ),
    )
    moderator = Role(
        name="moderator",
        permissions=RolePermissions(
            view_regular_movies=True,
            view_premium_movies=True,
            create_movies=True,
            edit_movies=True,
            delete_movies=False,
        ),
    )
    regular_user = Role(
        name="regular_user",
        permissions=RolePermissions(
            view_regular_movies=True,
            view_premium_movies=False,
            create_movies=False,
            edit_movies=False,
            delete_movies=False,
        ),
    )
    premium_user = Role(
        name="premium_user",
        permissions=RolePermissions(
            view_regular_movies=True,
            view_premium_movies=True,
            create_movies=False,
            edit_movies=False,
            delete_movies=False,
        ),
    )

    @classmethod
    def roles(cls):
        return [
            value.name for value in vars(cls).values()
            if isinstance(value, Role)
        ]
