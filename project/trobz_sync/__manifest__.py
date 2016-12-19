# -*- coding: utf-8 -*-

{
    'name': 'Synchronization Management',
    'version': '1.1',
    'category': 'Trobz Standard Modules',
    'author': 'Trobz',
    'website': 'http://trobz.com',
    'depends': [
        'deferred_processing',
        'trobz_base'
    ],
    'data': [
        # Data
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        # Security
        'security/ir.model.access.csv',
        # View
        'views/trobz_sync_setting_view.xml',
        'views/trobz_sync_mapping_view.xml',
        'views/trobz_sync_record_view.xml',
        'views/trobz_sync_log_view.xml',
        # Menu
        'views/sync_menu.xml',
        # Wizard
        'wizards/sync_password_prompt_wizard.xml',
    ],
    'installable': False,
    'active': False,
}
