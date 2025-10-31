SELECT
    user_id,
    login,
    password,
    role
FROM users
WHERE login = %s AND password = %s