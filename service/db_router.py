# -*- coding: utf-8 -*-
"""
Roteador de banco de dados para direcionar consultas dos modelos legados
para o banco de dados contact_z_legacy.
"""


class LegacyDatabaseRouter:
    """
    Roteador para direcionar operações dos modelos legados para o banco contact_z_legacy.
    """
    
    # Lista de modelos legados que devem usar o banco contact_z_legacy
    legacy_models = [
        'Organizations',
        'Users', 
        'Channels',
        'Contacts',
        'Groups',
        'Chats',
        'Messages',
        'Sectors',
        'Tags',
        'UserSectors',
        'ContactOrganizations',
        'ContactTags',
        'GroupOrganizations',
        'GroupTags',
    ]
    
    def db_for_read(self, model, **hints):
        """
        Suggest the database to read from for objects of type model.
        """
        if model._meta.app_label == 'legacy_models' or model.__name__ in self.legacy_models:
            return 'contact_z_legacy'
        return None
    
    def db_for_write(self, model, **hints):
        """
        Suggest the database to write to for objects of type model.
        """
        if model._meta.app_label == 'legacy_models' or model.__name__ in self.legacy_models:
            return 'contact_z_legacy'
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if models are in the same app.
        """
        db_set = {'default', 'contact_z_legacy'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Ensure that legacy models are not migrated to the default database.
        """
        if app_label == 'legacy_models':
            return db == 'contact_z_legacy'
        elif db == 'contact_z_legacy':
            return False
        return None 