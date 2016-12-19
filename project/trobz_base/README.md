Features available in all projects at Trobz
===========================================
**User management**
-------------------
* Automatically set the time-zone of the users based on a default time zone
(see below in configuration)
* Use a new concept "Profile" to create/update users easily

**Modules**
-----------
* Add buttons on the list view of modules to install from the list
* By default, display the list view rather than the kanban view

**ERP Maintenance**
-------------------
* Send email to Trobz whenever an error appears
* Check the type of the instance running. If not production, all e-mails are
redirected to a default email  (set in config parameter with the key
'default_email' or 'poweremail.test@trobz.com').
* Set the UI to Extended mode for admin user.
* Upgrade all installed modules from Trobz automatically when upgrading the
module trobz_base

Available functions which are often used in projects
====================================================
* update_company_logo
* load_language
* update_config: Can be used to update the application setting at Settings >
Configuration > xxx
* unlink_object_by_xml_id
* delete_default_products
* run_post_object_one_time: run functions to create/update data in
project module
* make_default_manager_groups: create Demo manager profile
**Update Separator Format for Language**
----------------------------------------
* Default is en_US.UTF-8
