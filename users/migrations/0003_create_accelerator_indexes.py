# users/migrations/0003_create_accelerator_indexes.py
from django.db import migrations

SQL_UP = """
-- índices que aceleram as subqueries de permissão
CREATE INDEX IF NOT EXISTS auth_perm_ct_code_idx
  ON auth_permission (content_type_id, codename);

CREATE INDEX IF NOT EXISTS users_user_groups_user_idx
  ON users_user_groups (user_id, group_id);

CREATE INDEX IF NOT EXISTS guard_uobjperm_u_perm_obj_idx
  ON guardian_userobjectpermission (user_id, permission_id, object_pk);

CREATE INDEX IF NOT EXISTS guard_gobjperm_g_perm_obj_idx
  ON guardian_groupobjectpermission (group_id, permission_id, object_pk);
"""


class Migration(migrations.Migration):
    atomic = False  # permite CREATE EXTENSION/índices grandes sem travar a transação
    dependencies = [("users", "0002_alter_user_nickname")]
    operations = [migrations.RunSQL(SQL_UP)]
