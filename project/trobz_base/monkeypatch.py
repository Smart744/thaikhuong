############################################
# Trobz Upgrade module Monkey-Pack Section #
############################################
from odoo.addons.base.module import module
from odoo.tools.config import config
import logging
_logger = logging.getLogger(__name__)


def trobz_button_upgrade(self):
    '''
    Overwrite this function to upgrade all installed modules from Trobz
    when upgrading the module "trobz_base"
    '''
    _logger.info("Trobz_button_upgrade is processing.........")
    upgrade_ids = self.ids
    # check whether "trobz_base" is in the list
    check_trobz_base = self.search([('name', '=', 'trobz_base'),
                                    ('id', 'in', upgrade_ids)])
    if check_trobz_base:
        # get all installed module with author "Trobz"
        installed_trobz_modules = self.search([('state', '=', 'installed'),
                                               ('author', 'ilike', 'Trobz')])
        upgrade_ids.extend(installed_trobz_modules.ids)
        """
        uniquifying the ids to avoid:
            Error: "One of the records you are trying to modify has
            already been deleted (Document type: %s)"
        if exist an duplicate id in ids
        """
        upgrade_ids = list(set(upgrade_ids))
    _logger.info("Trobz_button_upgrade ids of modules "
                 "that need to upgrade: %s" % upgrade_ids)
    _logger.info("Trobz_button_upgrade call native "
                 "native_button_upgrade...")
    # call super
    upgrade_modules = self.browse(upgrade_ids)
    native_button_upgrade(upgrade_modules)
"""
# if exist trobz_base in update of config, override native button_upgrade
# by trobz_button_upgrade to upgrade all trobz_modules
"""
if 'trobz_base' in config['update']:
    _logger.info("Override button_upgrade by trobz_button_upgrade")
    # get native button_upgrade from Odoo
    native_button_upgrade = getattr(module.Module, 'button_upgrade')
    # set trobz_button_upgrade as default upgrade function of base
    setattr(module.Module, 'button_upgrade', trobz_button_upgrade)
