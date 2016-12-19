from odoo import models, api

# Group
group_configure_user = 'Administration / User'


class post_install_security(models.TransientModel):
    _name = "post.install.security.trobz.base.module"
    _description = "Post Install Security for Trobz Base Module"

    @api.model
    def create_model_access_rights(self):
        MODEL_ACCESS_RIGHTS = {
            ('res.users'): {
                (group_configure_user): [1, 1, 1, 1],
            },
            ('ir.module.category'): {
                (group_configure_user): [1, 0, 0, 0],
            },
            ('ir.module.module'): {
                (group_configure_user): [1, 0, 0, 0],
            },
            ('ir.module.module.dependency'): {
                (group_configure_user): [1, 0, 0, 0],
            }
        }

        self.env['access.right.generator'].with_context(
            module_name='trobz.base').create_model_access_rights(
            MODEL_ACCESS_RIGHTS)
        return True

    @api.model_cr
    def _register_hook(self):
        self.create_model_access_rights()
