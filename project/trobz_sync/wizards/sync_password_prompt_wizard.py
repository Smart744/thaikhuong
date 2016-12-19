# -*- coding: utf-8 -*-

from openerp.osv import osv, fields


# TODO: rename this model to follow Trobz's convention
class sync_password_prompt_wizard(osv.TransientModel):
    _name = 'sync.password.prompt.wizard'

    _columns = {
        'password': fields.char('password', size=256, required=True),
    }

    def deferred_synchronize(self, cr, uid, ids, context=None):
        """
        Run the synchronization with deferred task.
        """
        if context is None:
            context = {}
        data = self.browse(cr, uid, ids, context=context)
        password = data and data[0].password or ''
        context.update(password=password)

        mapping_obj = self.pool['trobz.sync.mapping']
        setting_obj = self.pool['trobz.sync.setting']
        active_ids = context.get('active_ids', [])

        if context.get('sync_from_mapping', False):
            return mapping_obj.deferred_synchronize(cr, uid, active_ids,
                                                    context=context)
        else:
            return setting_obj.deferred_synchronize(cr, uid, active_ids,
                                                    context=context)

sync_password_prompt_wizard()
