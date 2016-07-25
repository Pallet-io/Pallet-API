class ExplorerRouter(object):
    """
    A router to control all database operations on models in the
    explorer application.
    """

    def db_for_read(self, model, **hints):
        """
        Attempts to read explorer models go to explorer_db.
        """
        if model._meta.app_label == 'explorer':
            return 'explorer_db'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write explorer models go to explorer_db.
        """
        if model._meta.app_label == 'explorer':
            return 'explorer_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the explorer app is involved.
        """
        if obj1._meta.app_label == 'explorer' or obj2._meta.app_label == 'explorer':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the explorer app only appears in the 'explorer_db' database.
        """
        if app_label == 'explorer':
            return db == 'explorer_db'
        return None
