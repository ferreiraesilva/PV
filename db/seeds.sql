-- safv seed data (admin user)

INSERT INTO tenants (id, name, slug, is_default, metadata)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'Labs4Ideas',
    'labs4ideas',
    TRUE,
    jsonb_build_object('notes', 'Bootstrap tenant for local development')
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    slug = EXCLUDED.slug,
    is_default = EXCLUDED.is_default,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

INSERT INTO permissions (id, code, description)
VALUES
    ('33333333-3333-3333-3333-333333333331', 'manage_users', 'Allows managing tenant users and roles'),
    ('33333333-3333-3333-3333-333333333332', 'view_audit_logs', 'Allows viewing audit log entries'),
    ('33333333-3333-3333-3333-333333333333', 'manage_financial_models', 'Allows maintaining financial models and indices')
ON CONFLICT (code) DO NOTHING;

INSERT INTO roles (id, tenant_id, name, description, is_default)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    'tenant_admin',
    'Full administrative role for SAFV tenant',
    TRUE
)
ON CONFLICT (tenant_id, name) DO UPDATE SET description = EXCLUDED.description,
    is_default = EXCLUDED.is_default;

INSERT INTO role_permissions (role_id, permission_id)
SELECT '22222222-2222-2222-2222-222222222222', perm.id
FROM permissions perm
WHERE perm.code IN ('manage_users', 'view_audit_logs', 'manage_financial_models')
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO users (
    id,
    tenant_id,
    email,
    hashed_password,
    full_name,
    is_active,
    is_superuser,
    is_suspended,
    roles
)
VALUES (
    '44444444-4444-4444-4444-444444444444',
    '11111111-1111-1111-1111-111111111111',
    'admin@labs4ideas.com.br',
    '$2b$12$Y3gvmmuiRrJ5gDLUBxKMk.rYfX7UykHSpL9PiW3fVGPoL0Lbvm/VW',
    'Default SAFV Admin',
    TRUE,
    TRUE,
    FALSE,
    jsonb_build_array('superadm', 'tenantadmin')
)
ON CONFLICT (tenant_id, email) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    is_active = TRUE,
    is_superuser = TRUE,
    is_suspended = FALSE,
    roles = EXCLUDED.roles,
    updated_at = NOW();

INSERT INTO user_roles (user_id, role_id)
VALUES ('44444444-4444-4444-4444-444444444444', '22222222-2222-2222-2222-222222222222')
ON CONFLICT (user_id, role_id) DO NOTHING;

-- Default credentials: admin@labs4ideas.com.br / ChangeMe123!
